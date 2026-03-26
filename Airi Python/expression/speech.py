import logging
import asyncio
import time
from typing import Optional, Dict, Any, List, Union, Literal
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_speech")

class SpeechConfig(BaseModel):
    active_provider: str = "elevenlabs"
    active_voice_id: str = "alloy"
    active_model: str = "eleven_multilingual_v2"

class TextToken(BaseModel):
    type: Literal["literal", "special", "flush"]
    value: Optional[str] = None
    stream_id: str
    intent_id: str
    sequence: int
    created_at: float = Field(default_factory=time.time)

class TtsRequest(BaseModel):
    stream_id: str
    intent_id: str
    segment_id: str
    text: str
    special: Optional[str] = None
    priority: int
    created_at: float

class IntentState:
    def __init__(self, intent_id: str, stream_id: str, priority: int, behavior: str, owner_id: str = None):
        self.intent_id = intent_id
        self.stream_id = stream_id
        self.priority = priority
        self.behavior = behavior
        self.owner_id = owner_id
        self.created_at = time.time()
        self.tokens = asyncio.Queue()
        self.canceled = False
        self.done = False

class SpeechPipeline:
    def __init__(self, tts_provider=None):
        self.config = SpeechConfig()
        self.tts_provider = tts_provider
        self.intents: Dict[str, IntentState] = {}
        self.pending: List[IntentState] = []
        self.active_intent: Optional[IntentState] = None
        self.is_running = False

    async def open_intent(self, intent_id: str = None, priority: int = 100, behavior: str = "queue", owner_id: str = None) -> str:
        intent_id = intent_id or f"intent-{generate()}"
        stream_id = f"stream-{generate()}"

        intent = IntentState(intent_id, stream_id, priority, behavior, owner_id)
        self.intents[intent_id] = intent

        if not self.active_intent:
            asyncio.create_task(self._run_intent(intent))
        elif behavior == "replace":
            await self.cancel_intent(self.active_intent.intent_id, "replace")
            asyncio.create_task(self._run_intent(intent))
        elif behavior == "interrupt" and priority >= self.active_intent.priority:
            await self.cancel_intent(self.active_intent.intent_id, "interrupt")
            asyncio.create_task(self._run_intent(intent))
        else:
            self.pending.append(intent)

        return intent_id

    async def write_literal(self, intent_id: str, text: str):
        if intent_id in self.intents:
            intent = self.intents[intent_id]
            await intent.tokens.put(TextToken(
                type="literal", value=text, stream_id=intent.stream_id,
                intent_id=intent_id, sequence=0
            ))

    async def cancel_intent(self, intent_id: str, reason: str = "canceled"):
        if intent_id in self.intents:
            intent = self.intents[intent_id]
            intent.canceled = True
            logger.info(f"Intent {intent_id} canceled: {reason}")

            if self.active_intent and self.active_intent.intent_id == intent_id:
                # Stop current playback if possible
                pass

    async def _run_intent(self, intent: IntentState):
        self.active_intent = intent
        logger.info(f"Starting intent: {intent.intent_id}")

        try:
            while not intent.done and not intent.canceled:
                token = await intent.tokens.get()
                if token.type == "literal" and token.value:
                    await self._speak_text(token.value, intent)
                elif token.type == "flush":
                    intent.done = True
                intent.tokens.task_done()
        except Exception as e:
            logger.error(f"Error in intent {intent.intent_id}: {e}")
        finally:
            if intent.intent_id in self.intents:
                del self.intents[intent.intent_id]
            self.active_intent = None

            next_intent = self._pick_next_intent()
            if next_intent:
                asyncio.create_task(self._run_intent(next_intent))

    def _pick_next_intent(self) -> Optional[IntentState]:
        if not self.pending:
            return None
        self.pending.sort(key=lambda x: (-x.priority, x.created_at))
        return self.pending.pop(0)

    async def _speak_text(self, text: str, intent: IntentState):
        logger.info(f"Speaking: {text}")
        if self.tts_provider:
            await self.tts_provider.text_to_speech(text, self.config.active_voice_id)
        await asyncio.sleep(len(text) * 0.05) # Dummy delay

    async def speak(self, text: str, priority: int = 100, behavior: str = "queue"):
        intent_id = await self.open_intent(priority=priority, behavior=behavior)
        await self.write_literal(intent_id, text)
        await self.intents[intent_id].tokens.put(TextToken(
            type="flush", stream_id=self.intents[intent_id].stream_id,
            intent_id=intent_id, sequence=1
        ))
