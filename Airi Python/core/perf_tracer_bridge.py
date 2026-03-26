import logging
import random
import time
from typing import List, Dict, Any, Optional, Literal, Set, Union, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_perf_tracer_bridge")

class TraceEvent(BaseModel):
    tracer_id: str = Field(..., alias="tracerId")
    name: str
    ts: float
    duration: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

PerfTracerMode = Literal['forward', 'receive']
PerfTracerState = Literal['idle', 'forward', 'receive']

class PerfTracerMessageEnable(BaseModel):
    type: Literal['enable'] = 'enable'
    token: Optional[str] = None
    origin: str
    mode: Optional[PerfTracerMode] = 'forward'

class PerfTracerMessageDisable(BaseModel):
    type: Literal['disable'] = 'disable'
    token: Optional[str] = None
    origin: str

class PerfTracerMessageEvent(BaseModel):
    type: Literal['event'] = 'event'
    event: TraceEvent
    origin: str

PerfTracerMessage = Union[PerfTracerMessageEnable, PerfTracerMessageDisable, PerfTracerMessageEvent]

BRIDGE_TOKEN = 'perf-bridge'
RELAY_META_KEY = '__perfTracerRelayedFrom'
FORWARDED_TRACERS = {'chat', 'markdown'}

class PerfTracerBridge:
    def __init__(self):
        self.instance_id = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8))
        self.state: PerfTracerState = 'idle'
        self.active_token: Optional[str] = None

    async def transition(self, next_state: PerfTracerState, token: str = BRIDGE_TOKEN):
        if self.state == next_state:
            return

        if next_state == 'idle':
            await self._stop_forwarding()
            await self._disable_local()
        elif next_state == 'receive':
            await self._enable_local(token)
            await self._stop_forwarding()
        elif next_state == 'forward':
            await self._enable_local(token)
            await self._start_forwarding()

        self.state = next_state
        self.active_token = token
        logger.info(f"PerfTracerBridge transitioned to {next_state}")

    async def _enable_local(self, token: str):
        logger.info(f"Enabling local perf tracer with token: {token}")

    async def _disable_local(self):
        logger.info("Disabling local perf tracer")

    async def _start_forwarding(self):
        logger.info("Starting perf event forwarding")

    async def _stop_forwarding(self):
        logger.info("Stopping perf event forwarding")

    async def handle_message(self, message: PerfTracerMessage):
        if message.origin == self.instance_id:
            return

        if isinstance(message, PerfTracerMessageEnable):
            await self.transition(message.mode or 'forward', message.token or BRIDGE_TOKEN)
        elif isinstance(message, PerfTracerMessageDisable):
            await self.transition('idle')
        elif isinstance(message, PerfTracerMessageEvent):
            if self.state == 'idle':
                return
            logger.info(f"Replaying remote perf event: {message.event.name}")

    async def request_enable(self, token: str = None, mode: PerfTracerMode = 'forward'):
        await self.transition(mode, token or BRIDGE_TOKEN)
        # Broadcast logic would go here

    async def request_disable(self, token: str = None):
        await self.transition('idle')
        # Broadcast logic would go here
