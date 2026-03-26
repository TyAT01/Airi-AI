import logging
import random
import time
from typing import List, Dict, Any, Optional, Literal, Union, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_markdown_stress")

class TraceEvent(BaseModel):
    tracer_id: str = Field(..., alias="tracerId")
    name: str
    ts: float
    duration: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

class DevtoolsChatScenario(BaseModel):
    user_messages: List[Dict[str, Union[float, str]]] = Field(..., alias="userMessages")
    assistant: Dict[str, Any]

class MarkdownStressStore:
    def __init__(self, providers_store=None, consciousness_store=None, perf_tracer_bridge=None):
        self.providers_store = providers_store
        self.consciousness_store = consciousness_store
        self.perf_tracer_bridge = perf_tracer_bridge

        self.capturing = False
        self.events: List[TraceEvent] = []
        self.last_run: Optional[Dict[str, Any]] = None
        self.payload_preview = ""
        self.schedule_delay_ms = 10000
        self.run_state: Literal['idle', 'scheduled', 'running'] = 'idle'
        self.scenario: Optional[DevtoolsChatScenario] = None
        self.is_mock = False
        self.can_run_online = True

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
        user_prompt = 'Give me a huge stress-test JavaScript block.'
        assistant_text = '```javascript\nfor (let i = 0; i < 2000; i++) {\n  console.log("Stress test");\n}\n```'

        scenario = DevtoolsChatScenario(
            userMessages=[
                {"atMs": 0.0, "text": user_prompt},
                {"atMs": 1200.0, "text": "I really need a large block."}
            ],
            assistant={
                "text": assistant_text,
                "firstTokenDelayMs": 150,
                "rate": {"tokensPerSecond": 120}
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
        # In a real app, use asyncio.sleep or a task scheduler

    async def cancel_scheduled_run(self):
        self.run_state = 'idle'
        logger.info("Cancelled scheduled markdown stress test run")

    def export_csv(self):
        logger.info("Exporting stress test events to CSV")
        # Implementation to write self.events to CSV
        pass
