import logging
import json
import os
import hashlib
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_providers")

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    capabilities: List[str] = []
    context_length: int = Field(0, alias="contextLength")
    deprecated: bool = False

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

class ProviderRuntimeState(BaseModel):
    is_configured: bool = Field(False, alias="isConfigured")
    validated_credential_hash: Optional[str] = Field(None, alias="validatedCredentialHash")
    models: List[ModelInfo] = []
    is_loading_models: bool = Field(False, alias="isLoadingModels")
    model_load_error: Optional[str] = Field(None, alias="modelLoadError")

class ProvidersStore:
    def __init__(self, persistence_path: str = "settings/credentials/providers.json"):
        self.providers: Dict[str, Dict[str, Any]] = {}
        self.added_providers: Dict[str, bool] = {}
        self.provider_runtime_state: Dict[str, ProviderRuntimeState] = {}
        self.persistence_path = persistence_path
        self._load_from_persistence()

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    self.providers = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load provider credentials: {e}")

    def _save_to_persistence(self):
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        try:
            with open(self.persistence_path, "w") as f:
                json.dump(self.providers, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save provider credentials: {e}")

    def mark_provider_added(self, provider_id: str):
        self.added_providers[provider_id] = True

    def unmark_provider_added(self, provider_id: str):
        if provider_id in self.added_providers:
            del self.added_providers[provider_id]

    async def validate_provider(self, provider_id: str, force: bool = False) -> bool:
        config = self.providers.get(provider_id, {})
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()

        state = self.provider_runtime_state.get(provider_id)
        if not state:
            state = ProviderRuntimeState()
            self.provider_runtime_state[provider_id] = state

        if not force and state.validated_credential_hash == config_hash:
            return state.is_configured

        # Placeholder validation logic - in TS it depends on specific provider validators
        is_valid = bool(config.get("apiKey", "").strip() or provider_id == 'browser-web-speech-api')

        state.is_configured = is_valid
        state.validated_credential_hash = config_hash

        if is_valid and provider_id in ['browser-web-speech-api', 'player2']:
            self.mark_provider_added(provider_id)

        return is_valid

    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        return self.providers.get(provider_id, {})

    async def fetch_models_for_provider(self, provider_id: str) -> List[ModelInfo]:
        logger.info(f"Fetching models for provider {provider_id}")
        # In Python, this would call the respective provider's API
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
