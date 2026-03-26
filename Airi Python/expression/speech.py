import logging
import asyncio
import time
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_speech")

class SpeechConfig(BaseModel):
    active_provider: str = "elevenlabs"
    active_voice_id: str = "alloy"
    active_model: str = "eleven_multilingual_v2"

class TextToken(BaseModel):
    type: str # 'literal', 'special', 'flush'
    value: Optional[str] = None
    stream_id: str
    intent_id: str
    sequence: int
    created_at: float = Field(default_factory=time.time)

class SpeechPipeline:
    def __init__(self, tts_provider=None):
        self.config = SpeechConfig()
        self.tts_provider = tts_provider
        self.queue = asyncio.PriorityQueue()
        self.active_intent = None
        self.is_processing = False
        self.intents = {}

    async def open_intent(self, intent_id: str = None, priority: int = 100, behavior: str = "queue"):
        intent_id = intent_id or f"intent-{generate()}"
        stream_id = f"stream-{generate()}"

        intent = {
            "id": intent_id,
            "stream_id": stream_id,
            "priority": priority,
            "behavior": behavior,
            "tokens": asyncio.Queue(),
            "canceled": False
        }
        self.intents[intent_id] = intent

        if behavior == "interrupt" and self.active_intent and priority > self.active_intent["priority"]:
            await self.cancel_intent(self.active_intent["id"], reason="interrupted")

        if not self.is_processing:
            asyncio.create_task(self._run_pipeline())

        return intent_id

    async def write_literal(self, intent_id: str, text: str):
        if intent_id in self.intents:
            intent = self.intents[intent_id]
            await intent["tokens"].put(TextToken(
                type="literal", value=text, stream_id=intent["stream_id"],
                intent_id=intent_id, sequence=0
            ))

    async def cancel_intent(self, intent_id: str, reason: str = "canceled"):
        if intent_id in self.intents:
            self.intents[intent_id]["canceled"] = True
            logger.info(f"Intent {intent_id} canceled: {reason}")

    async def _run_pipeline(self):
        self.is_processing = True
        while self.intents:
            # Sort intents by priority
            sorted_intents = sorted(
                [i for i in self.intents.values() if not i["canceled"]],
                key=lambda x: x["priority"], reverse=True
            )

            if not sorted_intents:
                await asyncio.sleep(0.1)
                continue

            intent = sorted_intents[0]
            self.active_intent = intent

            while not intent["tokens"].empty() and not intent["canceled"]:
                token = await intent["tokens"].get()
                if token.type == "literal" and token.value:
                    await self._speak_text(token.value, intent)
                intent["tokens"].task_done()

            if intent["tokens"].empty() or intent["canceled"]:
                del self.intents[intent["id"]]

        self.is_processing = False
        self.active_intent = None

    async def speak(self, text: str, priority: int = 100, behavior: str = "queue"):
        intent_id = await self.open_intent(priority=priority, behavior=behavior)
        await self.write_literal(intent_id, text)

    async def _speak_text(self, text: str, intent: Dict[str, Any]):
        logger.info(f"Speaking segment: {text}")
        if self.tts_provider:
            try:
                audio = await self.tts_provider.text_to_speech(text, self.config.active_voice_id)
                # In a real app, send audio to playback system
            except Exception as e:
                logger.error(f"TTS Error: {e}")
        await asyncio.sleep(len(text) * 0.05) # Dummy playback delay
