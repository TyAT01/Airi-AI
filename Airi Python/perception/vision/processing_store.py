import logging
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel

logger = logging.getLogger("airi_vision_processing")

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

    def reset_state(self):
        self.is_running = False
        self.tick_count = 0
        self.skipped_ticks = 0
        self.capture_count = 0
        self.context_update_count = 0
        self.processing_history_ms = []
        self.capture_history = []
        self.context_update_history = []
        logger.info("Vision processing store reset")
