import asyncio
import json
import re
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable, TypeVar, Generic
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T')

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

class HandlerContext(Generic[T]):
    def __init__(self, data: T, emit: Callable[[str, Any], None]):
        self.data = data
        self.emit = emit

class Queue(Generic[T]):
    def __init__(self, handlers: List[Callable[[HandlerContext[T]], Awaitable[None]]]):
        self.handlers = handlers
        self.queue: List[T] = []
        self._processing = False
        self.event_listeners: Dict[str, List[Callable]] = {
            'enqueue': [],
            'dequeue': [],
            'process': [],
            'error': [],
            'result': [],
            'drain': []
        }
        self.handler_event_listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, listener: Callable):
        if event_name in self.event_listeners:
            self.event_listeners[event_name].append(listener)

    def emit(self, event_name: str, *args):
        if event_name in self.event_listeners:
            for listener in self.event_listeners[event_name]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        # Use call_soon to avoid blocking
                        asyncio.get_event_loop().call_soon(lambda: asyncio.create_task(listener(*args)))
                    else:
                        listener(*args)
                except Exception as e:
                    logger.error(f"Error in event listener {event_name}: {e}")

    def on_handler_event(self, event_name: str, listener: Callable):
        if event_name not in self.handler_event_listeners:
            self.handler_event_listeners[event_name] = []
        self.handler_event_listeners[event_name].append(listener)

    def _emit_handler_event(self, event_name: str, *args):
        if event_name in self.handler_event_listeners:
            for listener in self.handler_event_listeners[event_name]:
                try:
                    listener(*args)
                except Exception as e:
                    logger.error(f"Error in handler event listener {event_name}: {e}")

    async def enqueue(self, payload: T):
        self.queue.append(payload)
        self.emit('enqueue', payload, len(self.queue))
        if not self._processing:
            asyncio.create_task(self._drain())

    def clear(self):
        self.queue.clear()

    async def _drain(self):
        if self._processing:
            return
        self._processing = True
        try:
            while self.queue:
                payload = self.queue.pop(0)
                self.emit('dequeue', payload, len(self.queue))
                for handler in self.handlers:
                    self.emit('process', payload, handler)
                    try:
                        ctx = HandlerContext(data=payload, emit=self._emit_handler_event)
                        result = await handler(ctx)
                        self.emit('result', payload, result, handler)
                    except Exception as e:
                        self.emit('error', payload, e, handler)
                        continue

            self.emit('drain')
        finally:
            self._processing = False

    def length(self) -> int:
        return len(self.queue)

def create_queue(handlers: List[Callable[[HandlerContext[T]], Awaitable[None]]]) -> Queue[T]:
    return Queue(handlers)
