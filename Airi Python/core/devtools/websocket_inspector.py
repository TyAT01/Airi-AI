import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger("airi_websocket_inspector")

class WebSocketMessage(Dict):
    pass

class WebSocketInspectorStore:
    def __init__(self, max_messages: int = 500):
        self.messages: List[WebSocketMessage] = []
        self.max_messages = max_messages
        self.is_capturing = True

    def add(self, direction: str, event: Dict[str, Any]):
        if not self.is_capturing:
            return

        message = WebSocketMessage({
            "direction": direction,
            "event": event,
            "timestamp": time.time()
        })
        self.messages.append(message)

        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

        logger.debug(f"Added {direction} WebSocket message")

    def clear(self):
        self.messages = []
        logger.info("WebSocket inspector messages cleared")

    def set_capturing(self, capturing: bool):
        self.is_capturing = capturing
        logger.info(f"WebSocket inspector capturing set to: {capturing}")
