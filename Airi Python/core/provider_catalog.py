import logging
import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

class ProviderCatalogProvider(BaseModel):
    id: str
    definitionId: str
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    validated: bool = False
    validationBypassed: bool = Field(False, alias="validationBypassed")

    class Config:
        populate_by_name = True

class ProviderCatalogStore:
    def __init__(self, persistence_file: str = "settings/provider_catalog.json"):
        self.configs: Dict[str, ProviderCatalogProvider] = {}
        self.persistence_file = persistence_file
        self._load_from_persistence()

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    for pid, config_data in data.items():
                        self.configs[pid] = ProviderCatalogProvider(**config_data)
                logger.info(f"Loaded {len(self.configs)} provider configurations from catalog.")
            except Exception as e:
                logger.error(f"Failed to load provider catalog persistence: {e}")

    def _save_to_persistence(self):
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        try:
            with open(self.persistence_file, "w") as f:
                data = {pid: config.dict(by_alias=True) for pid, config in self.configs.items()}
                json.dump(data, f, indent=2)
            logger.info("Saved provider catalog configurations.")
        except Exception as e:
            logger.error(f"Failed to save provider catalog persistence: {e}")

    async def fetch_list(self):
        """
        In TS, this handles local-first request with remote sync.
        For Python, we focus on local persistence for now.
        """
        self._load_from_persistence()
        return list(self.configs.values())

    async def add_provider(self, definition_id: str, name: str, initial_config: Dict[str, Any] = {}):
        provider_id = generate()
        provider = ProviderCatalogProvider(
            id=provider_id,
            definitionId=definition_id,
            name=name,
            config=initial_config,
            validated=False,
            validationBypassed=False
        )
        self.configs[provider_id] = provider
        self._save_to_persistence()
        return provider

    async def remove_provider(self, provider_id: str):
        if provider_id in self.configs:
            del self.configs[provider_id]
            self._save_to_persistence()

    async def commit_provider_config(
        self,
        provider_id: str,
        new_config: Dict[str, Any],
        validated: bool,
        validation_bypassed: bool
    ):
        provider = self.configs.get(provider_id)
        if not provider:
            return None

        provider.config = new_config
        provider.validated = validated
        provider.validationBypassed = validation_bypassed
        self._save_to_persistence()
        return provider
