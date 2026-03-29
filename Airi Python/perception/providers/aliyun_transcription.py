import asyncio
import json
import logging
import websockets
from typing import Optional, Callable, Dict, Any, AsyncGenerator

from perception.providers.aliyun import AliyunNLSProvider, AliyunNLSSession

logger = logging.getLogger(__name__)

class AliyunStreamTranscription:
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        app_key: str,
        region: str = 'cn-shanghai',
        session_options: Optional[Dict[str, Any]] = None
    ):
        self.provider = AliyunNLSProvider(access_key_id, access_key_secret, app_key, region)
        self.session = AliyunNLSSession(self.provider)
        self.session_options = session_options
        self.websocket = None
        self.running = False
        self._on_sentence_final = None
        self._on_result_changed = None

    async def start(self, audio_generator: Callable[[], AsyncGenerator[bytes, None]]):
        url = await self.provider.get_websocket_url()
        self.running = True

        async with websockets.connect(url) as ws:
            self.websocket = ws
            await self.session.start(ws, self.session_options)

            # Create tasks for reading messages and sending audio
            receive_task = asyncio.create_task(self._receive_messages())
            send_task = asyncio.create_task(self._send_audio(audio_generator))

            try:
                # Wait for send_task to complete, which means audio_generator is exhausted
                await send_task
                # After audio is sent, send the stop command to trigger TranscriptionCompleted
                if self.running and not ws.closed:
                    await self.session.stop(ws)
                # Now wait for receive_task to process the final events and TranscriptionCompleted
                await receive_task
            except Exception as e:
                logger.error(f"Error in Aliyun streaming transcription: {e}")
            finally:
                self.running = False
                if not ws.closed:
                    await ws.close()

    async def _send_audio(self, audio_generator: Callable[[], AsyncGenerator[bytes, None]]):
        async for chunk in audio_generator():
            if not self.running or self.websocket.closed:
                break
            await self.websocket.send(chunk)
            # Yield to other tasks
            await asyncio.sleep(0)

    async def _receive_messages(self):
        async for message in self.websocket:
            if not self.running:
                break

            data = json.loads(message)
            self.session.on_event(data, self._handle_event)

            if data['header']['name'] == 'TranscriptionCompleted':
                break

    def _handle_event(self, event: Dict[str, Any]):
        name = event['header']['name']
        payload = event.get('payload', {})

        if name == 'SentenceEnd' and self._on_sentence_final:
            asyncio.create_task(self._on_sentence_final(payload))
        elif name == 'TranscriptionResultChanged' and self._on_result_changed:
            asyncio.create_task(self._on_result_changed(payload))

    def on_sentence_final(self, callback: Callable[[Dict[str, Any]], Any]):
        self._on_sentence_final = callback

    def on_result_changed(self, callback: Callable[[Dict[str, Any]], Any]):
        self._on_result_changed = callback

    async def stop(self):
        self.running = False
        if self.websocket and not self.websocket.closed:
            await self.session.stop(self.websocket)
