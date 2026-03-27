import logging
from typing import Dict, Any
from core.configurator import Configurator

logger = logging.getLogger(__name__)

class DiscordSettings:
    def __init__(self, configurator: Configurator):
        self.configurator = configurator
        self.enabled: bool = False
        self.token: str = ""

    def save_settings(self):
        self.configurator.update_for("discord", {
            "token": self.token,
            "enabled": self.enabled,
        })

    @property
    def configured(self) -> bool:
        return bool(self.token.strip())

    def reset_state(self):
        self.enabled = False
        self.token = ""
        self.save_settings()
        logger.info("Discord settings reset")
