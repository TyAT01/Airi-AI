import logging
import asyncio
from typing import List, Dict, Any, Optional, Union, Callable, Awaitable
from pydantic import BaseModel, Field
from core.providers import ProvidersStore

logger = logging.getLogger(__name__)

class StreamTranscriptionOptions(BaseModel):
    language: Optional[str] = None
    continuous: bool = True
    interim_results: bool = Field(True, alias="interimResults")
    max_alternatives: int = Field(1, alias="maxAlternatives")

class HearingStore:
    def __init__(self, providers_store: ProvidersStore):
        self.providers_store = providers_store
        self.active_transcription_provider: str = ""
        self.active_transcription_model: str = ""
        self.active_custom_model_name: str = ""
        self.transcription_model_search_query: str = ""
        self.auto_send_enabled: bool = False
        self.auto_send_delay: int = 2000
        self.isLoadingModels: Dict[str, bool] = {}
        self.modelLoadError: Dict[str, Optional[str]] = {}

    @property
    def supports_model_listing(self) -> bool:
        # In TS: providersStore.getProviderMetadata(activeTranscriptionProvider.value)?.capabilities.listModels !== undefined
        # For now, we assume all providers support it if they are configured
        return True

    @property
    def provider_models(self) -> List[Any]:
        return self.providers_store.get_models_for_provider(self.active_transcription_provider)

    @property
    def is_loading_active_provider_models(self) -> bool:
        state = self.providers_store.provider_runtime_state.get(self.active_transcription_provider)
        return state.is_loading_models if state else False

    @property
    def active_provider_model_error(self) -> Optional[str]:
        state = self.providers_store.provider_runtime_state.get(self.active_transcription_provider)
        return state.model_load_error if state else None

    @property
    def configured(self) -> bool:
        if not self.active_transcription_provider:
            return False
        if self.active_transcription_provider == 'browser-web-speech-api':
            return True

        # For OpenAI Compatible providers, check provider config as fallback
        if self.active_transcription_provider == 'openai-compatible-audio-transcription':
            provider_config = self.providers_store.get_provider_config(self.active_transcription_provider)
            if provider_config.get('model'):
                return True

        return bool(self.active_transcription_model)

    async def load_models_for_provider(self, provider: str):
        if provider:
            await self.providers_store.fetch_models_for_provider(provider)

    async def get_models_for_provider(self, provider: str):
        if provider:
            return self.providers_store.get_models_for_provider(provider)
        return []

    def reset_state(self):
        self.active_transcription_provider = ""
        self.active_transcription_model = ""
        self.active_custom_model_name = ""
        self.transcription_model_search_query = ""
        self.auto_send_enabled = False
        self.auto_send_delay = 2000
        logger.info("Hearing store reset")

    async def transcription(
        self,
        provider_id: str,
        model: str,
        input_data: Any,
        format_type: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        logger.info(f"Transcribing audio with {provider_id} and model {model}")
        # Placeholder for real STT call
        return {"mode": "generate", "text": "Transcribed text placeholder"}

class HearingSpeechInputPipeline:
    def __init__(self, hearing_store: HearingStore, providers_store: ProvidersStore):
        self.hearing_store = hearing_store
        self.providers_store = providers_store
        self.error: Optional[str] = None
        self.streaming_session: Optional[Dict[str, Any]] = None

    @property
    def supports_stream_input(self) -> bool:
        provider_id = self.hearing_store.active_transcription_provider
        if not provider_id:
            return False
        if provider_id == 'browser-web-speech-api':
            return True
        # Check features from providers store
        return True # Placeholder

    async def transcribe_for_media_stream(
        self,
        stream: Any,
        options: Optional[Dict[str, Any]] = None
    ):
        logger.info(f"Transcribing media stream with provider: {self.hearing_store.active_transcription_provider}")
        if not self.supports_stream_input:
            logger.warning("Stream input not supported")
            return

        # Simplified logic for Python port
        self.error = None
        try:
            provider_id = self.hearing_store.active_transcription_provider
            if not provider_id:
                self.error = "No transcription provider selected"
                return

            # Placeholder for streaming session logic
            self.streaming_session = {
                "providerId": provider_id,
                "active": True
            }
            logger.info(f"Started streaming transcription session for {provider_id}")

        except Exception as e:
            self.error = str(e)
            logger.error(f"Error in transcribe_for_media_stream: {e}")

    async def stop_streaming_transcription(self, abort: bool = False):
        if not self.streaming_session:
            return
        logger.info(f"Stopping streaming transcription (abort={abort})")
        self.streaming_session = None

    async def transcribe_for_recording(self, recording: Any) -> Optional[str]:
        self.error = None
        if not recording:
            return None

        try:
            provider_id = self.hearing_store.active_transcription_provider
            model = self.hearing_store.active_transcription_model
            result = await self.hearing_store.transcription(provider_id, model, recording)
            return result.get("text")
        except Exception as e:
            self.error = str(e)
            logger.error(f"Error in transcribe_for_recording: {e}")
            return None
