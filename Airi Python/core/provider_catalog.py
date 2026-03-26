import logging
import json
import os
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_provider_catalog")

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    context_length: int = Field(0, alias="contextLength")
    deprecated: bool = False

class ProviderMetadata(BaseModel):
    id: str
    name: str
    category: Literal["chat", "embed", "speech", "transcription"]
    tasks: List[str]
    description: Optional[str] = None
    icon: Optional[str] = None
    default_options: Dict[str, Any] = Field(default_factory=dict, alias="defaultOptions")

class ProviderRuntimeState(BaseModel):
    is_configured: bool = Field(False, alias="isConfigured")
    models: List[ModelInfo] = []
    is_loading_models: bool = Field(False, alias="isLoadingModels")
    model_load_error: Optional[str] = Field(None, alias="modelLoadError")

class ProviderCatalog:
    def __init__(self, persistence_file: str = "provider_configs.json"):
        self.credentials: Dict[str, Dict[str, Any]] = {}
        self.runtime_states: Dict[str, ProviderRuntimeState] = {}
        self.persistence_file = persistence_file
        self._load_from_persistence()

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    self.credentials = data.get("credentials", {})
                    states_data = data.get("runtime_states", {})
                    for pid, sdata in states_data.items():
                        self.runtime_states[pid] = ProviderRuntimeState(**sdata)
                logger.info(f"Loaded {len(self.credentials)} provider configurations.")
            except Exception as e:
                logger.error(f"Failed to load provider persistence: {e}")

    def _save_to_persistence(self):
        try:
            with open(self.persistence_file, "w") as f:
                data = {
                    "credentials": self.credentials,
                    "runtime_states": {pid: s.dict(by_alias=True) for pid, s in self.runtime_states.items()}
                }
                json.dump(data, f, indent=2)
            logger.info("Saved provider configurations.")
        except Exception as e:
            logger.error(f"Failed to save provider persistence: {e}")

    def get_provider_config(self, provider_id: str) -> Dict[str, Any]:
        return self.credentials.get(provider_id, {})

    def set_provider_config(self, provider_id: str, config: Dict[str, Any]):
        self.credentials[provider_id] = config
        self._save_to_persistence()

    def update_runtime_state(self, provider_id: str, updates: Dict[str, Any]):
        if provider_id not in self.runtime_states:
            self.runtime_states[provider_id] = ProviderRuntimeState()

        state_dict = self.runtime_states[provider_id].dict()
        state_dict.update(updates)
        self.runtime_states[provider_id] = ProviderRuntimeState(**state_dict)
        self._save_to_persistence()
