import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_plugin_host_debug")

class PluginMessage(BaseModel):
    id: str
    plugin_id: str
    direction: str
    type: str
    data: Optional[Any] = None
    timestamp: float

class PluginHostDebugStore:
    def __init__(self, max_messages: int = 1000):
        self.messages: List[PluginMessage] = []
        self.max_messages = max_messages
        self.is_debugging = False

    def log_message(self, message: PluginMessage):
        if not self.is_debugging:
            return

        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        logger.debug(f"Logged plugin message: {message.type} from {message.plugin_id}")

    def clear(self):
        self.messages = []
        logger.info("Plugin host debug logs cleared")

    def toggle_debugging(self):
        self.is_debugging = not self.is_debugging
        logger.info(f"Plugin host debugging set to: {self.is_debugging}")
