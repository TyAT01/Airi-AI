import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from core.providers import ProvidersStore

logger = logging.getLogger(__name__)

class ConsciousnessStore:
    def __init__(self, providers_store: ProvidersStore):
        self.providers_store = providers_store
        self.active_provider: str = ""
        self.active_model: str = ""
        self.active_custom_model_name: str = ""
        self.model_search_query: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.active_provider and self.active_model)

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

    async def load_models_for_provider(self, provider: str):
        if provider:
            await self.providers_store.fetch_models_for_provider(provider)

    def reset_model_selection(self):
        self.active_model = ""
        self.active_custom_model_name = ""
        self.model_search_query = ""

    def reset_state(self):
        self.active_provider = ""
        self.reset_model_selection()
        logger.info("Consciousness store reset")
