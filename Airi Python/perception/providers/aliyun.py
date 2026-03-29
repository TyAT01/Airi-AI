import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, Callable, Union
from pydantic import BaseModel, Field

from perception.providers.aliyun_token import create_token
from perception.providers.aliyun_utils import nls_websocket_endpoint_from_region

logger = logging.getLogger(__name__)

# Aliyun NLS requires exact 32 character length in hex for IDs.
def generate_hex_id(length: int = 32) -> str:
    import secrets
    return secrets.token_hex(length // 2)

class BaseEventHeader(BaseModel):
    appkey: str
    message_id: str = Field(default_factory=generate_hex_id)
    task_id: str
    namespace: str = "SpeechTranscriber"
    name: str
    status: Optional[int] = None
    status_message: Optional[str] = None

class BaseEvent(BaseModel):
    header: BaseEventHeader
    payload: Any

class AliyunNLSProvider:
    def __init__(self, access_key_id: str, access_key_secret: str, app_key: str, region: str = 'cn-shanghai'):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.app_key = app_key
        self.region = region
        self._token = ""
        self._token_expires_at = 0

    async def get_websocket_url(self) -> str:
        now_ms = time.time() * 1000
        if not self._token or now_ms >= self._token_expires_at:
            created = await create_token(self.access_key_id, self.access_key_secret, {'region_id': self.region})
            self._token = created['token']
            self._token_expires_at = created['expires_at']

        url = nls_websocket_endpoint_from_region(self.region)
        if '?' in url:
            return f"{url}&token={self._token}"
        else:
            return f"{url}?token={self._token}"

class AliyunNLSSession:
    def __init__(self, provider: AliyunNLSProvider):
        self.provider = provider
        self.session_id = generate_hex_id()

    async def start(self, websocket, options: Optional[Dict[str, Any]] = None):
        payload = {
            'format': 'pcm',
            'sample_rate': 16000,
            'enable_intermediate_result': True,
            'enable_punctuation_prediction': True,
        }
        if options:
            payload.update(options)

        start_event = {
            'header': {
                'appkey': self.provider.app_key,
                'message_id': generate_hex_id(),
                'task_id': self.session_id,
                'namespace': 'SpeechTranscriber',
                'name': 'StartTranscription',
            },
            'payload': payload,
        }
        await websocket.send(json.dumps(start_event))

    async def stop(self, websocket):
        stop_event = {
            'header': {
                'appkey': self.provider.app_key,
                'message_id': generate_hex_id(),
                'task_id': self.session_id,
                'namespace': 'SpeechTranscriber',
                'name': 'StopTranscription',
            },
            'payload': {},
        }
        await websocket.send(json.dumps(stop_event))

    def on_event(self, data: Union[str, Dict[str, Any]], callback: Callable[[Dict[str, Any]], Any]):
        if isinstance(data, str):
            event = json.loads(data)
        else:
            event = data
        callback(event)
