import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EmotionPayload(BaseModel):
    name: str
    intensity: float = 1.0

class EmotionQueue:
    def __init__(self, on_emotion: Callable[[EmotionPayload], Awaitable[None]]):
        self.on_emotion = on_emotion
        self.queue = asyncio.Queue()
        self.is_running = False

    async def enqueue(self, text: str):
        # Extract <|ACT:{"emotion": "happy"}|>
        match = re.search(r"<\|ACT\s*(?::\s*)?({.*?})\|>", text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                payload = json.loads(match.group(1))
                emotion_name = payload.get("emotion")
                if isinstance(emotion_name, str):
                    intensity = payload.get("intensity", 1.0)
                    emotion = EmotionPayload(name=emotion_name.lower(), intensity=float(intensity))
                    await self.queue.put(emotion)
                    if not self.is_running:
                        asyncio.create_task(self._process())
            except Exception as e:
                logger.warning(f"Failed to parse ACT emotion: {e}")

    async def _process(self):
        self.is_running = True
        while not self.queue.empty():
            emotion = await self.queue.get()
            await self.on_emotion(emotion)
            self.queue.task_done()
        self.is_running = False

class DelayQueue:
    async def process_text(self, text: str):
        # Extract <|DELAY:5|>
        match = re.search(r"<\|DELAY:(\d+)\|>", text, re.IGNORECASE)
        if match:
            delay_seconds = float(match.group(1))
            if delay_seconds > 0:
                logger.info(f"Applying delay: {delay_seconds}s")
                await asyncio.sleep(delay_seconds)
