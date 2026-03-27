import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable, Awaitable
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
    def supports_ssml(self) -> bool:
        # Currently only ElevenLabs and some other providers support SSML
        # only part voices are support SSML in cosyvoice-v2 which is provided by alibaba
        if self.active_speech_provider == 'alibaba-cloud-model-studio' and self.active_speech_model == 'cosyvoice-v2':
            return True
        return self.active_speech_provider in ['elevenlabs', 'microsoft-speech', 'azure-speech']

    @property
    def supports_model_listing(self) -> bool:
        # Placeholder logic
        return True

    @property
    def provider_models(self) -> List[Any]:
        return self.providers_store.get_models_for_provider(self.active_speech_provider)

    @property
    def is_loading_active_provider_models(self) -> bool:
        state = self.providers_store.provider_runtime_state.get(self.active_speech_provider)
        return state.is_loading_models if state else False

    @property
    def active_provider_model_error(self) -> Optional[str]:
        state = self.providers_store.provider_runtime_state.get(self.active_speech_provider)
        return state.model_load_error if state else None

    @property
    def filtered_models(self) -> List[Any]:
        models = self.provider_models
        if not self.model_search_query.strip():
            return models
        query = self.model_search_query.lower().strip()
        # Basic filtering logic
        return [m for m in models if query in m.name.lower() or query in m.id.lower()]

    @property
    def configured(self) -> bool:
        if self.active_speech_provider == "speech-noop":
            return False
        if not self.active_speech_provider:
            return False

        has_model = bool(self.active_speech_model)
        has_voice = bool(self.active_speech_voice_id)

        # For OpenAI Compatible providers, check provider config as fallback
        if self.active_speech_provider == 'openai-compatible-audio-speech':
            provider_config = self.providers_store.get_provider_config(self.active_speech_provider)
            has_model |= bool(provider_config.get("model", ""))
            has_voice |= bool(provider_config.get("voice", ""))

        return has_model and has_voice

    async def load_voices_for_provider(self, provider: str):
        if not provider:
            return []

        self.is_loading_voices = True
        self.speech_provider_error = None

        try:
            # Simplified for porting logic
            metadata = self.providers_store.provider_metadata.get(provider)
            if not metadata:
                return []

            # Use capabilities to fetch voices if metadata has list_voices function
            # This logic mimics store.ts
            voices = [] # Placeholder for real call
            self.available_voices[provider] = voices
            return voices
        except Exception as e:
            logger.error(f"Error fetching voices for {provider}: {e}")
            self.speech_provider_error = str(e)
            return []
        finally:
            self.is_loading_voices = False

    def get_voices_for_provider(self, provider: str):
        return self.available_voices.get(provider, [])

    async def speech(
        self,
        provider: Any, # Provider instance
        model: str,
        input_text: str,
        voice: str,
        provider_config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        logger.info(f"Generating speech with {model} for: {input_text[:50]}...")
        # Placeholder for TTS call
        return b"audio data placeholder"

    def generate_ssml(
        self,
        text: str,
        voice: VoiceInfo,
        provider_config: Optional[Dict[str, Any]] = None
    ) -> str:
        # Simplified SSML generation for Python port
        pitch = provider_config.get("pitch", 0.0) if provider_config else 0.0
        rate = provider_config.get("rate", 1.0) if provider_config else 1.0

        lang = voice.languages[0].get("code", "en-US") if voice.languages else "en-US"

        return (
            f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{lang}'>"
            f"<voice name='{voice.id}'>"
            f"<prosody pitch='{pitch}' rate='{rate}'>"
            f"{text}"
            f"</prosody></voice></speak>"
        )

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

class SpeechPipeline:
    def __init__(self):
        self.active_intent_id: Optional[str] = None
        self.is_speaking: bool = False

    async def speak(self, text: str):
        logger.info(f"Speaking: {text}")
        self.is_speaking = True
        # Logic to send audio to output
        self.is_speaking = False

    def stop(self):
        logger.info("Stopping speech")
        self.is_speaking = False
