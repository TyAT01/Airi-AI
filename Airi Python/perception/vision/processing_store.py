import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class VisionTickOutcome(BaseModel):
    captured_at: Optional[float] = None
    context_updates: Optional[int] = None

class VisionProcessingStore:
    def __init__(self):
        self.capture_interval_ms = 3000
        self.is_running = False
        self.is_processing = False
        self.tick_count = 0
        self.skipped_ticks = 0
        self.capture_count = 0
        self.context_update_count = 0

        self.last_tick_at: Optional[float] = None
        self.last_capture_at: Optional[float] = None
        self.last_context_update_at: Optional[float] = None
        self.last_processing_duration_ms: Optional[float] = None

        self.processing_history_ms: List[float] = []
        self.capture_history: List[float] = []
        self.context_update_history: List[float] = []

    def record_capture(self, captured_at: float = None):
        if captured_at is None:
            captured_at = time.time()
        self.capture_count += 1
        self.last_capture_at = captured_at
        self.capture_history.append(captured_at)

    def record_context_updates(self, count: int = 1, updated_at: float = None):
        if updated_at is None:
            updated_at = time.time()
        self.context_update_count += count
        self.last_context_update_at = updated_at
        for _ in range(count):
            self.context_update_history.append(updated_at)

    @property
    def capture_rate_per_minute(self) -> int:
        cutoff = time.time() - 60
        return len([t for t in self.capture_history if t > cutoff])

    @property
    def context_update_rate_per_minute(self) -> int:
        cutoff = time.time() - 60
        return len([t for t in self.context_update_history if t > cutoff])

    @property
    def average_processing_ms(self) -> float:
        if not self.processing_history_ms:
            return 0.0
        return sum(self.processing_history_ms) / len(self.processing_history_ms)

    def record_processing_duration(self, duration_ms: float):
        self.last_processing_duration_ms = duration_ms
        self.processing_history_ms.append(duration_ms)
        if len(self.processing_history_ms) > 240:
            self.processing_history_ms.pop(0)

    async def run_tick(self, handler: Callable[[], Awaitable[Optional[VisionTickOutcome]]]):
        if self.is_processing:
            self.skipped_ticks += 1
            return

        self.is_processing = True
        self.last_tick_at = time.time()
        self.tick_count += 1
        start_time = time.perf_counter()

        try:
            outcome = await handler()
            if outcome:
                if outcome.captured_at:
                    self.record_capture(outcome.captured_at)
                if outcome.context_updates:
                    self.record_context_updates(outcome.context_updates)
        except Exception as e:
            logger.error(f"Vision tick error: {e}")
        finally:
            self.record_processing_duration((time.perf_counter() - start_time) * 1000.0)
            self.is_processing = False

    async def start_ticker(self, handler: Callable[[], Awaitable[Optional[VisionTickOutcome]]]):
        if self.is_running:
            return
        self.is_running = True
        logger.info("Vision ticker started")
        while self.is_running:
            await self.run_tick(handler)
            await asyncio.sleep(self.capture_interval_ms / 1000.0)

    def stop_ticker(self):
        self.is_running = False
        logger.info("Vision ticker stopped")

    def reset_state(self):
        self.stop_ticker()
        self.tick_count = 0
        self.skipped_ticks = 0
        self.capture_count = 0
        self.context_update_count = 0
        self.processing_history_ms = []
        self.capture_history = []
        self.context_update_history = []
        logger.info("Vision processing store reset")
