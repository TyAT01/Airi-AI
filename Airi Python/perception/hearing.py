import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_hearing")

class HearingConfig(BaseModel):
    active_provider: str = Field("", alias="activeProvider")
    active_model: str = Field("", alias="activeModel")
    auto_send_enabled: bool = Field(False, alias="autoSendEnabled")
    auto_send_delay: int = Field(2000, alias="autoSendDelay")

class HearingStore:
    def __init__(self):
        self.config = HearingConfig()
        self.providers: Dict[str, Any] = {}

    def set_provider(self, provider_id: str, model: str):
        self.config.active_provider = provider_id
        self.config.active_model = model

    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        # Implementation for transcription providers (e.g. OpenAI Whisper, WebSpeech)
        logger.info(f"Transcribing audio with {self.config.active_provider}...")
        return "Transcribed text placeholder"

class VisionStore:
    def __init__(self):
        self.enabled = False
        self.active_camera: Optional[str] = None

    async def capture_and_analyze(self) -> Dict[str, Any]:
        logger.info("Capturing and analyzing vision data...")
        return {"objects": [], "faces": []}
