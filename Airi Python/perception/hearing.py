import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.providers import ProvidersStore

logger = logging.getLogger("airi_hearing")

class HearingStore:
    def __init__(self, providers_store: ProvidersStore):
        self.providers_store = providers_store
        self.active_transcription_provider: str = ""
        self.active_transcription_model: str = ""
        self.active_custom_model_name: str = ""
        self.transcription_model_search_query: str = ""
        self.auto_send_enabled: bool = False
        self.auto_send_delay: int = 2000

    @property
    def configured(self) -> bool:
        if not self.active_transcription_provider:
            return False
        if self.active_transcription_provider == 'browser-web-speech-api':
            return True
        return bool(self.active_transcription_model)

    async def load_models_for_provider(self, provider: str):
        if provider:
            await self.providers_store.fetch_models_for_provider(provider)

    def reset_state(self):
        self.active_transcription_provider = ""
        self.active_transcription_model = ""
        self.active_custom_model_name = ""
        self.transcription_model_search_query = ""
        self.auto_send_enabled = False
        self.auto_send_delay = 2000
        logger.info("Hearing store reset")

    async def transcribe(self, provider_id: str, model: str, audio_data: Any) -> str:
        logger.info(f"Transcribing audio with {provider_id} and model {model}")
        # Placeholder for STT call
        return "Transcribed text"

class VisionStore:
    # Ported in perception/vision/index.py
    pass
