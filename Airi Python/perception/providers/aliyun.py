import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
import websockets

logger = logging.getLogger("airi_aliyun")

class AliyunTranscriptionProvider:
    def __init__(self, access_key_id: str, access_key_secret: str, app_key: str):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.app_key = app_key
        self.websocket_url = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"

    async def transcribe_stream(self, audio_generator, on_text: Callable[[str], Awaitable[None]]):
        # Implementation of Aliyun NLS protocol
        logger.info("Starting Aliyun transcription stream...")
        try:
            async with websockets.connect(self.websocket_url) as ws:
                # 1. Send start command
                start_cmd = {
                    "header": {
                        "message_id": "mock_id",
                        "task_id": "mock_task",
                        "namespace": "SpeechTranscriber",
                        "name": "StartTranscription",
                        "appkey": self.app_key
                    },
                    "payload": {
                        "format": "pcm",
                        "sample_rate": 16000
                    }
                }
                await ws.send(json.dumps(start_cmd))

                # 2. Receive start confirmation
                resp = await ws.recv()
                logger.info(f"Aliyun response: {resp}")

                # 3. Stream audio and listen for messages
                async for chunk in audio_generator():
                    await ws.send(chunk)
                    # Non-blocking check for messages
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
                        data = json.loads(msg)
                        if data["header"]["name"] == "TranscriptionResultChanged":
                            await on_text(data["payload"]["result"])
                    except asyncio.TimeoutError:
                        continue
        except Exception as e:
            logger.error(f"Aliyun transcription error: {e}")
