import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable, TypeVar, Generic

T = TypeVar('T')

logger = logging.getLogger(__name__)

class HandlerContext(Generic[T]):
    def __init__(self, data: T, emit_cb: Callable[[str, Any], None]):
        self.data = data
        self.emit_cb = emit_cb

    def emit(self, event_name: str, *params):
        self.emit_cb(event_name, *params)

class StreamQueue(Generic[T]):
    def __init__(self, handlers: List[Callable[[HandlerContext[T]], Awaitable[None]]]):
        self.handlers = handlers
        self.queue = asyncio.Queue()
        self.is_draining = False
        self.listeners = {
            "enqueue": [],
            "dequeue": [],
            "process": [],
            "error": [],
            "result": [],
            "drain": []
        }
        self.handler_listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, callback: Callable):
        if event_name in self.listeners:
            self.listeners[event_name].append(callback)

    def on_handler_event(self, event_name: str, callback: Callable):
        if event_name not in self.handler_listeners:
            self.handler_listeners[event_name] = []
        self.handler_listeners[event_name].append(callback)

    def _emit(self, event_name: str, *params):
        for callback in self.listeners.get(event_name, []):
            callback(*params)

    def _emit_handler(self, event_name: str, *params):
        for callback in self.handler_listeners.get(event_name, []):
            callback(*params)

    async def enqueue(self, payload: T):
        await self.queue.put(payload)
        self._emit("enqueue", payload, self.queue.qsize())
        if not self.is_draining:
            asyncio.create_task(self.drain())

    async def drain(self):
        self.is_draining = True
        while not self.queue.empty():
            payload = await self.queue.get()
            self._emit("dequeue", payload, self.queue.qsize())
            ctx = HandlerContext(payload, self._emit_handler)
            for handler in self.handlers:
                self._emit("process", payload, handler)
                try:
                    result = await handler(ctx)
                    self._emit("result", payload, result, handler)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    self._emit("error", payload, e, handler)
            self.queue.task_done()
        self._emit("drain")
        self.is_draining = False

    def length(self) -> int:
        return self.queue.qsize()

class OBSIntegration:
    def __init__(self, host: str = "localhost", port: int = 4455, password: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.connected = False

    async def connect(self):
        logger.info(f"Connecting to OBS at {self.host}:{self.port}...")
        self.connected = True

    async def set_source_visibility(self, source_name: str, visible: bool):
        if not self.connected:
            await self.connect()
        logger.info(f"Setting OBS source {source_name} visibility to {visible}")
