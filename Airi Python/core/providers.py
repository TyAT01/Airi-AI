import logging
import json
import os
import hashlib
import asyncio
from typing import List, Dict, Any, Optional, Literal, Union, Callable, Awaitable
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    capabilities: List[str] = []
    context_length: int = Field(0, alias="contextLength")
    deprecated: bool = False

    class Config:
        populate_by_name = True
        populate_by_name = True

class VoiceInfo(BaseModel):
    id: str
    name: str
    provider: str
    compatible_models: List[str] = Field([], alias="compatibleModels")
    description: Optional[str] = None
    gender: Optional[str] = None
    deprecated: bool = False
    preview_url: Optional[str] = Field(None, alias="previewURL")
    languages: List[Dict[str, str]] = []

    class Config:
        populate_by_name = True
        populate_by_name = True

class ProviderMetadata(BaseModel):
    id: str
    order: Optional[int] = None
    category: Literal['chat', 'embed', 'speech', 'transcription']
    tasks: List[str]
    name: str
    description: str
    icon: Optional[str] = None
    iconColor: Optional[str] = None
    iconImage: Optional[str] = None
    defaultOptions: Optional[Callable[[], Dict[str, Any]]] = None

    class Config:
        arbitrary_types_allowed = True

class ProviderRuntimeState(BaseModel):
    is_configured: bool = Field(False, alias="isConfigured")
    validated_credential_hash: Optional[str] = Field(None, alias="validatedCredentialHash")
    models: List[ModelInfo] = []
    is_loading_models: bool = Field(False, alias="isLoadingModels")
    model_load_error: Optional[str] = Field(None, alias="modelLoadError")

    class Config:
        populate_by_name = True
        populate_by_name = True

class ProvidersStore:
    def __init__(self, persistence_path: str = "settings/credentials/providers.json"):
        self.provider_credentials: Dict[str, Dict[str, Any]] = {}
        self.added_providers: Dict[str, bool] = {}
        self.provider_runtime_state: Dict[str, ProviderRuntimeState] = {}
        self.provider_instance_cache: Dict[str, Any] = {}
        self.persistence_path = persistence_path

        self.provider_metadata: Dict[str, ProviderMetadata] = self._initialize_metadata()
        self._load_from_persistence()
        self._initialize_runtime_states()

    def _initialize_metadata(self) -> Dict[str, ProviderMetadata]:
        # Mirroring some of the metadata from providers.ts
        metadata = {
            'speech-noop': ProviderMetadata(
                id='speech-noop',
                category='speech',
                tasks=['text-to-speech', 'tts'],
                name='None',
                description='No speech output.',
                icon='i-solar:volume-cross-bold-duotone',
                defaultOptions=lambda: {}
            ),
            'openai': ProviderMetadata(
                id='openai',
                category='chat',
                tasks=['chat'],
                name='OpenAI',
                description='openai.com',
                icon='i-lobe-icons:openai'
            ),
            'anthropic': ProviderMetadata(
                id='anthropic',
                category='chat',
                tasks=['chat'],
                name='Anthropic',
                description='anthropic.com',
                icon='i-lobe-icons:anthropic'
            ),
            'google-generative-ai': ProviderMetadata(
                id='google-generative-ai',
                category='chat',
                tasks=['chat'],
                name='Google Generative AI',
                description='ai.google.dev',
                icon='i-lobe-icons:google'
            ),
            'openrouter-ai': ProviderMetadata(
                id='openrouter-ai',
                category='chat',
                tasks=['chat'],
                name='OpenRouter',
                description='openrouter.ai',
                icon='i-lobe-icons:openrouter'
            ),
            'ollama': ProviderMetadata(
                id='ollama',
                category='chat',
                tasks=['chat'],
                name='Ollama',
                description='ollama.com',
                icon='i-lobe-icons:ollama'
            ),
            'deepseek': ProviderMetadata(
                id='deepseek',
                category='chat',
                tasks=['chat'],
                name='DeepSeek',
                description='deepseek.com',
                icon='i-lobe-icons:deepseek'
            ),
            'openai-compatible': ProviderMetadata(
                id='openai-compatible',
                category='chat',
                tasks=['chat'],
                name='OpenAI Compatible',
                description='Connect to any API that follows the OpenAI specification.',
                icon='i-lobe-icons:openai'
            ),
            'openai-audio-speech': ProviderMetadata(
                id='openai-audio-speech',
                category='speech',
                tasks=['text-to-speech'],
                name='OpenAI',
                description='openai.com',
                icon='i-lobe-icons:openai'
            ),
            'elevenlabs': ProviderMetadata(
                id='elevenlabs',
                category='speech',
                tasks=['text-to-speech'],
                name='ElevenLabs',
                description='elevenlabs.io',
                icon='i-simple-icons:elevenlabs'
            ),
            'deepgram-tts': ProviderMetadata(
                id='deepgram-tts',
                category='speech',
                tasks=['text-to-speech'],
                name='Deepgram',
                description='deepgram.com',
                icon='i-simple-icons:deepgram'
            ),
            'microsoft-speech': ProviderMetadata(
                id='microsoft-speech',
                category='speech',
                tasks=['text-to-speech'],
                name='Microsoft / Azure Speech',
                description='speech.microsoft.com',
                iconColor='i-lobe-icons:microsoft'
            ),
            'aliyun-nls-transcription': ProviderMetadata(
                id='aliyun-nls-transcription',
                category='transcription',
                tasks=['speech-to-text', 'automatic-speech-recognition', 'asr', 'stt', 'streaming-transcription'],
                name='Aliyun NLS',
                description='nls-console.aliyun.com',
                icon='i-lobe-icons:alibabacloud'
            )
        }
        return metadata

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    self.provider_credentials = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load provider credentials: {e}")

    def _save_to_persistence(self):
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        try:
            with open(self.persistence_path, "w") as f:
                json.dump(self.provider_credentials, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save provider credentials: {e}")

    def _initialize_runtime_states(self):
        for provider_id in self.provider_metadata:
            if provider_id not in self.provider_runtime_state:
                self.provider_runtime_state[provider_id] = ProviderRuntimeState()

    def mark_provider_added(self, provider_id: str):
        self.added_providers[provider_id] = True

    def unmark_provider_added(self, provider_id: str):
        if provider_id in self.added_providers:
            del self.added_providers[provider_id]

    async def validate_provider(self, provider_id: str, force: bool = False) -> bool:
        config = self.provider_credentials.get(provider_id, {})
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()

        state = self.provider_runtime_state.get(provider_id)
        if not state:
            state = ProviderRuntimeState()
            self.provider_runtime_state[provider_id] = state

        if not force and state.validated_credential_hash == config_hash:
            return state.is_configured

        # Placeholder validation logic
        is_valid = bool(config.get("apiKey", "").strip() or provider_id == 'speech-noop')

        state.is_configured = is_valid
        state.validated_credential_hash = config_hash

        if is_valid and provider_id in ['speech-noop']:
            self.mark_provider_added(provider_id)

        return is_valid

    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        return self.provider_credentials.get(provider_id, {})

    async def fetch_models_for_provider(self, provider_id: str) -> List[ModelInfo]:
        logger.info(f"Fetching models for provider {provider_id}")
        state = self.provider_runtime_state.get(provider_id)
        if state:
            state.is_loading_models = True
            # Mocking model fetching
            await asyncio.sleep(0.5)
            state.is_loading_models = False
        return []

    def get_models_for_provider(self, provider_id: str) -> List[ModelInfo]:
        state = self.provider_runtime_state.get(provider_id)
        return state.models if state else []

    @property
    def all_available_models(self) -> List[ModelInfo]:
        models = []
        for provider_id, state in self.provider_runtime_state.items():
            if state.is_configured:
                models.extend(state.models)
        return models

    @property
    def providers(self) -> Dict[str, Dict[str, Any]]:
        return self.provider_credentials

    @property
    def configured_providers(self) -> Dict[str, bool]:
        return {pid: state.is_configured for pid, state in self.provider_runtime_state.items()}

    async def get_provider_instance(self, provider_id: str) -> Any:
        if provider_id in self.provider_instance_cache:
            return self.provider_instance_cache[provider_id]

        # Placeholder for creating actual provider instances
        # In a real app, this would instantiate classes from perception/expression providers
        logger.info(f"Creating instance for provider: {provider_id}")
        return None
