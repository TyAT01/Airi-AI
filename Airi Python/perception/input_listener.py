import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class InputListener:
    def __init__(self):
        self.enabled = False

    def start(self, on_event: Callable[[str, Any], None]):
        logger.info("Starting global input listener (placeholder)...")
        self.enabled = True
        # Logic for pynput or similar would go here

    def stop(self):
        logger.info("Stopping global input listener.")
        self.enabled = False
