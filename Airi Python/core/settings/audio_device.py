import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from core.audio import AudioDeviceManager

logger = logging.getLogger(__name__)

class AudioDeviceSettings:
    def __init__(self, audio_device_manager: AudioDeviceManager):
        self.manager = audio_device_manager
        self.selected_input: str = ""
        self.enabled: bool = False

    async def start_stream(self):
        if self.enabled:
            await self.manager.start_stream()

    async def stop_stream(self):
        await self.manager.stop_stream()

    def reset_state(self):
        self.selected_input = ""
        self.enabled = False
        logger.info("Audio device settings reset")
