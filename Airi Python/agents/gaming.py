from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class GamingModuleConfig(BaseModel):
    enabled: bool = False
    server_address: str = Field("", alias="serverAddress")
    server_port: Optional[int] = Field(None, alias="serverPort")
    username: str = ""

class GamingModule:
    def __init__(self, name: str, default_port: int):
        self.name = name
        self.default_port = default_port
        self.config = GamingModuleConfig(serverPort=default_port)

    def update_config(self, updates: Dict[str, Any]):
        # Mimics Pinia store saving settings
        new_config_dict = self.config.dict(by_alias=True)
        new_config_dict.update(updates)
        self.config = GamingModuleConfig(**new_config_dict)

    def reset_state(self):
        self.config = GamingModuleConfig(serverPort=self.default_port)

    @property
    def configured(self) -> bool:
        return bool(self.config.server_address.strip() and self.config.username.strip() and self.config.server_port is not None)

class MinecraftModule(GamingModule):
    def __init__(self):
        super().__init__("minecraft", 25565)

class FactorioModule(GamingModule):
    def __init__(self):
        super().__init__("factorio", 34197)
