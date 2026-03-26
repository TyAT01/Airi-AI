import time
import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel

logger = logging.getLogger("airi_mocap")

class MocapConfig(BaseModel):
    enabled: Dict[str, bool] = {"pose": True, "hands": True, "face": True}
    hz: Dict[str, int] = {"pose": 30, "hands": 30, "face": 60}

class MocapStats:
    def __init__(self):
        self.last_ts = 0
        self.smoothed_fps = 0

    def tick(self, now_ms: float) -> float:
        if not self.last_ts:
            self.last_ts = now_ms
            return 0

        dt = now_ms - self.last_ts
        self.last_ts = now_ms

        if dt <= 0:
            return self.smoothed_fps

        fps = 1000 / dt
        self.smoothed_fps = (self.smoothed_fps * 0.9 + fps * 0.1) if self.smoothed_fps else fps
        return self.smoothed_fps

class MocapScheduler:
    def __init__(self, config: MocapConfig):
        self.config = config
        self.last_run: Dict[str, float] = {"pose": 0, "hands": 0, "face": 0}

    def plan(self, now_ms: float) -> List[str]:
        jobs = []
        for job in ["pose", "hands", "face"]:
            if not self.config.enabled.get(job):
                continue

            hz = self.config.hz.get(job, 0)
            if hz <= 0:
                continue

            if now_ms - self.last_run[job] >= (1000 / hz):
                jobs.append(job)
                self.last_run[job] = now_ms
        return jobs

class MocapEngine:
    def __init__(self, config: Optional[MocapConfig] = None):
        self.config = config or MocapConfig()
        self.scheduler = MocapScheduler(self.config)
        self.stats = MocapStats()
        self.running = False
        self.dropped_frames = 0
        self.last_state: Dict[str, Any] = {}

    async def start(self, on_state: Callable[[Dict[str, Any]], None]):
        self.running = True
        logger.info("Mocap Engine started")

        while self.running:
            now = time.time() * 1000
            jobs = self.scheduler.plan(now)

            if jobs:
                # Simulate backend processing
                t0 = time.time() * 1000
                # In a real app, call MediaPipe/OpenCV here
                latency = (time.time() * 1000) - t0

                state = {
                    "t": now,
                    "jobs": jobs,
                    "quality": {
                        "fps": self.stats.tick(now),
                        "latencyMs": latency,
                        "droppedFrames": self.dropped_frames,
                        "backend": "python-mocap"
                    }
                }
                on_state(state)

            await asyncio.sleep(0.01) # Yield to event loop

    def stop(self):
        self.running = False
        logger.info("Mocap Engine stopped")
