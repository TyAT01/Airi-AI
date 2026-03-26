import logging
from typing import Dict, Any
from core.configurator import Configurator

logger = logging.getLogger("airi_settings_twitter")

class TwitterSettings:
    def __init__(self, configurator: Configurator):
        self.configurator = configurator
        self.enabled: bool = False
        self.api_key: str = ""
        self.api_secret: str = ""
        self.access_token: str = ""
        self.access_token_secret: str = ""

    def save_settings(self):
        self.configurator.update_for("twitter", {
            "enabled": self.enabled,
            "apiKey": self.api_key,
            "apiSecret": self.api_secret,
            "accessToken": self.access_token,
            "accessTokenSecret": self.access_token_secret,
        })

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip() and self.api_secret.strip() and self.access_token.strip() and self.access_token_secret.strip())

    def reset_state(self):
        self.enabled = False
        self.api_key = ""
        self.api_secret = ""
        self.access_token = ""
        self.access_token_secret = ""
        self.save_settings()
        logger.info("Twitter settings reset")
