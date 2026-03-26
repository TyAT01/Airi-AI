import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_mocap")

class MocapConfig(BaseModel):
    enabled: Dict[str, bool] = {"pose": True, "hands": True, "face": True}
    hz: Dict[str, int] = {"pose": 30, "hands": 30, "face": 60}
    backend: str = "python-mediapipe"

class MocapQuality(BaseModel):
    fps: float = 0.0
    latency_ms: float = Field(0.0, alias="latencyMs")
    dropped_frames: int = Field(0, alias="droppedFrames")
    backend: str = "unknown"

class MocapStats:
    def __init__(self):
        self.last_ts = 0
        self.smoothed_fps = 0

    def tick(self, now_ms: float) -> float:
        if not self.last_ts:
            self.last_ts = now_ms
            return 0.0

        dt = now_ms - self.last_ts
        self.last_ts = now_ms

        if dt <= 0:
            return self.smoothed_fps

        fps = 1000.0 / dt
        # EMA smoothing for FPS
        self.smoothed_fps = (self.smoothed_fps * 0.9 + fps * 0.1) if self.smoothed_fps else fps
        return self.smoothed_fps

class MocapScheduler:
    def __init__(self, config: MocapConfig):
        self.config = config
        self.last_run: Dict[str, float] = {"pose": 0.0, "hands": 0.0, "face": 0.0}

    def plan(self, now_ms: float) -> List[str]:
        jobs = []
        for job in ["pose", "hands", "face"]:
            if not self.config.enabled.get(job):
                continue

            hz = self.config.hz.get(job, 0)
            if hz <= 0:
                continue

            # Check if enough time has passed for this specific job
            if now_ms - self.last_run[job] >= (1000.0 / hz):
                jobs.append(job)
                self.last_run[job] = now_ms
        return jobs

class MocapEngine:
    """
    Python Mocap engine mirroring MediaPipe driver logic.
    Handles scheduling, quality metrics, and async state emission.
    """
    def __init__(self, config: Optional[MocapConfig] = None):
        self.config = config or MocapConfig()
        self.scheduler = MocapScheduler(self.config)
        self.stats = MocapStats()
        self.running = False
        self.dropped_frames = 0

    async def start(self, on_state: Callable[[Dict[str, Any]], None]):
        self.running = True
        logger.info(f"Mocap Engine started with backend: {self.config.backend}")

        while self.running:
            now_ms = time.time() * 1000
            jobs = self.scheduler.plan(now_ms)

            if jobs:
                t0 = time.time() * 1000
                # Real implementation would call MediaPipe/OpenCV here
                # result = await self._process_frames(jobs)
                latency = (time.time() * 1000) - t0

                state = {
                    "t": now_ms,
                    "jobs": jobs,
                    "quality": MocapQuality(
                        fps=self.stats.tick(now_ms),
                        latencyMs=latency,
                        droppedFrames=self.dropped_frames,
                        backend=self.config.backend
                    ).dict(by_alias=True)
                }
                on_state(state)

            await asyncio.sleep(0.01) # Yield to event loop

    def stop(self):
        self.running = False
        logger.info("Mocap Engine stopped.")
