import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_speech")

class SpeechConfig(BaseModel):
    active_provider: str = Field("elevenlabs", alias="activeProvider")
    active_voice_id: str = Field("alloy", alias="activeVoiceId")
    active_model: str = Field("eleven_multilingual_v2", alias="activeModel")

class SpeechPipeline:
    def __init__(self):
        self.config = SpeechConfig()
        self.queue = asyncio.Queue()
        self.is_speaking = False

    async def speak(self, text: str, priority: int = 1):
        logger.info(f"Adding to speech queue: {text}")
        await self.queue.put({
            "text": text,
            "priority": priority,
            "id": generate()
        })
        if not self.is_speaking:
            asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        self.is_speaking = True
        while not self.queue.empty():
            item = await self.queue.get()
            logger.info(f"Speaking: {item['text']}")
            # Implementation for TTS provider here
            await asyncio.sleep(len(item['text']) * 0.05) # Dummy speaking time
            self.queue.task_done()
        self.is_speaking = False

    def interrupt(self):
        logger.info("Interrupting speech...")
        # Clear queue and stop current speech
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
