import logging
import random
import time
import asyncio
from typing import List, Dict, Any, Optional, Literal, Union, Callable, Awaitable
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_markdown_stress")

class TraceEvent(BaseModel):
    tracer_id: str = Field(..., alias="tracerId")
    name: str
    ts: float
    duration: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

class DeterministicTimer:
    def __init__(self, start_at: float = 0.0):
        self._now = start_at
        self._next_id = 1
        self._queue: List[Dict[str, Any]] = []

    def now(self) -> float:
        return self._now

    def schedule(self, delay_ms: float, fn: Callable[[], Union[None, Awaitable[None]]]) -> int:
        job_id = self._next_id
        self._next_id += 1
        at = self._now + max(0.0, delay_ms)
        self._queue.append({"id": job_id, "at": at, "fn": fn})
        self._queue.sort(key=lambda x: (x["at"], x["id"]))
        return job_id

    def cancel(self, job_id: int):
        self._queue = [job for job in self._queue if job["id"] != job_id]

    async def tick(self, ms: float):
        target = self._now + max(0.0, ms)
        while self._queue and self._queue[0]["at"] <= target:
            job = self._queue.pop(0)
            self._now = job["at"]
            res = job["fn"]()
            if asyncio.iscoroutine(res):
                await res
        self._now = target

    def clear(self):
        self._queue = []
        self._now = 0.0

def chunk_text(text: str, size: int) -> List[str]:
    if size <= 0:
        return [text]
    return [text[i:i+size] for i in range(0, len(text), size)]

class DevtoolsChatScenario(BaseModel):
    user_messages: List[Dict[str, Union[float, str]]] = Field(..., alias="userMessages")
    assistant: Dict[str, Any]

class MockStream:
    def __init__(self, scenario: DevtoolsChatScenario, timer: DeterministicTimer, on_event: Callable[[Dict[str, Any]], Awaitable[None]]):
        self.scenario = scenario
        self.timer = timer
        self.on_event = on_event
        self.cancelled = False

    async def run(self):
        text = self.scenario.assistant["text"]
        first_token_delay = self.scenario.assistant.get("firstTokenDelayMs", 0.0)
        rate = self.scenario.assistant.get("rate", {})
        tokens_per_second = rate.get("tokensPerSecond", 40)
        max_chunk_size = rate.get("maxChunkSize", 96)

        chunks = chunk_text(text, max(1, max_chunk_size))
        interval_ms = 1000.0 / max(1.0, tokens_per_second)

        last_ts = self.timer.now()
        base = last_ts + first_token_delay

        for i, chunk in enumerate(chunks):
            if self.cancelled:
                return
            target = base + i * interval_ms
            await self.timer.tick(target - last_ts)
            last_ts = target
            await self.on_event({"type": "text-delta", "text": chunk})
            # Brief yield
            await asyncio.sleep(0)

        if self.cancelled:
            return

        finish_at = base + len(chunks) * interval_ms
        await self.timer.tick(finish_at - last_ts)
        await self.on_event({"type": "finish"})

    def cancel(self):
        self.cancelled = True

class MarkdownStressStore:
    def __init__(self, providers_store=None, consciousness_store=None, perf_tracer_bridge=None, chat_orchestrator=None):
        self.providers_store = providers_store
        self.consciousness_store = consciousness_store
        self.perf_tracer_bridge = perf_tracer_bridge
        self.chat_orchestrator = chat_orchestrator

        self.capturing = False
        self.events: List[TraceEvent] = []
        self.last_run: Optional[Dict[str, Any]] = None
        self.payload_preview = ""
        self.schedule_delay_ms = 10000
        self.run_state: Literal['idle', 'scheduled', 'running'] = 'idle'
        self.scenario: Optional[DevtoolsChatScenario] = None
        self.is_mock = False
        self.can_run_online = True
        self.mock_timer = DeterministicTimer()
        self._mock_stream_cancel: Optional[Callable[[], None]] = None

    async def start_capture(self):
        if self.capturing:
            return

        self.capturing = True
        self.events = []
        logger.info("Starting markdown stress test capture")

        if self.perf_tracer_bridge:
            await self.perf_tracer_bridge.request_enable('markdown-stress')

    async def stop_capture(self):
        if not self.capturing:
            return

        self.capturing = False
        self.run_state = 'idle'
        logger.info("Stopping markdown stress test capture")

        if self.perf_tracer_bridge:
            await self.perf_tracer_bridge.request_disable('markdown-stress')

    def generate_scenario(self) -> DevtoolsChatScenario:
        user_prompt = 'Give me a huge stress-test JavaScript block with 2000 occurrences of the keyword `for` wrapped in ```javascript```.'

        line = 'for for for for for'
        flood = "\n".join([line for _ in range(800)])

        assistant_text = (
            "Here is a large JS `for` block:\n\n"
            "```javascript\n"
            f"{flood}\n"
            "```\n\n"
            "Done."
        )

        scenario = DevtoolsChatScenario(
            userMessages=[
                {"atMs": 0.0, "text": user_prompt},
                {"atMs": 1200.0, "text": "I really need it."}
            ],
            assistant={
                "text": assistant_text,
                "firstTokenDelayMs": 150,
                "rate": {"tokensPerSecond": 120, "maxChunkSize": 96}
            }
        )
        self.scenario = scenario
        return scenario

    async def schedule_run(self):
        if self.run_state == 'scheduled':
            await self.cancel_scheduled_run()
            return

        if self.run_state == 'running':
            await self.stop_capture()
            return

        self.run_state = 'scheduled'
        logger.info(f"Scheduled markdown stress test run in {self.schedule_delay_ms}ms")
        # In actual app loop, use asyncio.sleep

    async def cancel_scheduled_run(self):
        self.run_state = 'idle'
        logger.info("Cancelled scheduled markdown stress test run")

    def export_csv(self):
        logger.info("Exporting stress test events to CSV")
        pass
