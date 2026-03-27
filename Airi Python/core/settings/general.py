import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GeneralSettings:
    def __init__(self):
        self.language: str = "en"
        self.disable_transitions: bool = True
        self.use_page_specific_transitions: bool = True
        self.websocket_secure_enabled: bool = False

    def reset_state(self):
        self.language = "en"
        self.disable_transitions = True
        self.use_page_specific_transitions = True
        self.websocket_secure_enabled = False
        logger.info("General settings reset")

    def get_language(self) -> str:
        return self.language
