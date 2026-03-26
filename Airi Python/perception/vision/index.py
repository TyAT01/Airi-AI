import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from core.providers import ProvidersStore

logger = logging.getLogger("airi_vision_store")

class VisionStore:
    def __init__(self, providers_store: ProvidersStore):
        self.providers_store = providers_store
        self.active_provider: str = ""
        self.active_model: str = ""
        self.custom_model_name: str = ""
        self.ollama_thinking_enabled: bool = False
        self.model_search_query: str = ""

    @property
    def supports_model_listing(self) -> bool:
        if not self.active_provider:
            return False
        # Placeholder for checking provider capabilities
        return True

    @property
    def provider_models(self) -> List[Any]:
        if not self.active_provider:
            return []
        return self.providers_store.get_models_for_provider(self.active_provider)

    @property
    def is_loading_active_provider_models(self) -> bool:
        if not self.active_provider:
            return False
        return self.providers_store.provider_runtime_state.get(self.active_provider, {}).get("isLoadingModels", False)

    @property
    def configured(self) -> bool:
        return bool(self.active_provider and self.active_model)

    def reset_model_selection(self):
        self.active_model = ""
        self.custom_model_name = ""
        self.model_search_query = ""

    async def load_models_for_provider(self, provider: str):
        if provider:
            await self.providers_store.fetch_models_for_provider(provider)

    def reset_state(self):
        self.active_provider = ""
        self.reset_model_selection()
        logger.info("Vision store reset")
