import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.providers import ProvidersStore, VoiceInfo

logger = logging.getLogger("airi_speech")

class SpeechStore:
    def __init__(self, providers_store: ProvidersStore):
        self.providers_store = providers_store
        self.active_speech_provider: str = "speech-noop"
        self.active_speech_model: str = ""
        self.active_speech_voice_id: str = ""
        self.active_speech_voice: Optional[VoiceInfo] = None

        self.pitch: float = 0.0
        self.rate: float = 1.0
        self.ssml_enabled: bool = False
        self.is_loading_voices: bool = False
        self.speech_provider_error: Optional[str] = None
        self.available_voices: Dict[str, List[VoiceInfo]] = {}
        self.selected_language: str = "en-US"
        self.model_search_query: str = ""

    @property
    def configured(self) -> bool:
        if self.active_speech_provider == "speech-noop":
            return False
        return bool(self.active_speech_model and self.active_speech_voice_id)

    async def load_voices_for_provider(self, provider_id: str):
        if not provider_id:
            return []

        self.is_loading_voices = True
        self.speech_provider_error = None

        try:
            # Placeholder for listing voices via provider API
            voices = []
            self.available_voices[provider_id] = voices
            return voices
        except Exception as e:
            logger.error(f"Error fetching voices for {provider_id}: {e}")
            self.speech_provider_error = str(e)
            return []
        finally:
            self.is_loading_voices = False

    def reset_state(self):
        self.active_speech_provider = "speech-noop"
        self.active_speech_model = ""
        self.active_speech_voice_id = ""
        self.active_speech_voice = None
        self.pitch = 0.0
        self.rate = 1.0
        self.ssml_enabled = False
        self.selected_language = "en-US"
        self.available_voices = {}
        logger.info("Speech store reset")

    async def generate_speech(self, text: str) -> bytes:
        logger.info(f"Generating speech for: {text[:50]}...")
        # Placeholder for TTS generation
        return b"audio data"
