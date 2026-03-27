import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class GamingModuleConfig(BaseModel):
    enabled: bool = False
    server_address: str = Field("", alias="serverAddress")
    server_port: Optional[int] = Field(None, alias="serverPort")
    username: str = ""

class GamingModule:
    def __init__(self, name: str, default_port: int, configurator=None):
        self.name = name
        self.default_port = default_port
        self.config = GamingModuleConfig(serverPort=default_port)
        self.configurator = configurator

    def save_settings(self):
        logger.info(f"Saving settings for gaming module: {self.name}")
        if self.configurator:
            self.configurator.update_for(self.name, self.config.dict(by_alias=True))

    def update_config(self, updates: Dict[str, Any]):
        # Mimics Pinia store saving settings
        new_config_dict = self.config.dict(by_alias=True)
        new_config_dict.update(updates)
        self.config = GamingModuleConfig(**new_config_dict)
        self.save_settings()

    def reset_state(self):
        self.config = GamingModuleConfig(serverPort=self.default_port)
        self.save_settings()
        logger.info(f"Reset state for gaming module: {self.name}")

    @property
    def configured(self) -> bool:
        return bool(self.config.server_address.strip() and self.config.username.strip() and self.config.server_port is not None)

class MinecraftModule(GamingModule):
    def __init__(self, configurator=None):
        super().__init__("minecraft", 25565, configurator)

class FactorioModule(GamingModule):
    def __init__(self, configurator=None):
        super().__init__("factorio", 34197, configurator)

# Factory equivalent
def create_gaming_module(name: str, default_port: int, configurator=None) -> GamingModule:
    return GamingModule(name, default_port, configurator)
