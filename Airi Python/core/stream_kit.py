import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger("airi_stream_kit")

class StreamQueue:
    def __init__(self, handlers: List[Callable[[Dict[str, Any]], Awaitable[None]]]):
        self.handlers = handlers
        self.queue = asyncio.Queue()
        self.is_draining = False

    async def enqueue(self, payload: Any):
        await self.queue.put(payload)
        logger.debug(f"Enqueued: {payload}")
        if not self.is_draining:
            asyncio.create_task(self.drain())

    async def drain(self):
        self.is_draining = True
        while not self.queue.empty():
            payload = await self.queue.get()
            logger.debug(f"Processing: {payload}")
            for handler in self.handlers:
                try:
                    await handler({"data": payload})
                except Exception as e:
                    logger.error(f"Handler error: {e}")
            self.queue.task_done()
        self.is_draining = False

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
