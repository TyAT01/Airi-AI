import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Set, Union
from dataclasses import dataclass, field
from schemas.protocol import EventEnvelope as GatewayEvent

logger = logging.getLogger(__name__)

class GatewayChannel:
    def __init__(
        self,
        name: str,
        in_queue: Optional[asyncio.Queue] = None,
        out_handler: Optional[Callable[[GatewayEvent], Any]] = None,
        can_handle: Optional[Callable[[GatewayEvent], bool]] = None
    ):
        self.name = name
        self.in_queue = in_queue
        self.out_handler = out_handler
        self.can_handle = can_handle

@dataclass
class GatewayRoute:
    match_func: Callable[[GatewayEvent], bool]
    to: List[str]
    mode: str = "fan-out"  # 'fan-out' | 'first' | 'all'

class ChannelGateway:
    def __init__(self):
        self.channels: Dict[str, GatewayChannel] = {}
        self.routes: List[GatewayRoute] = []
        self.tasks: Dict[str, asyncio.Task] = {}

    def register(self, channel: GatewayChannel):
        self.channels[channel.name] = channel
        logger.info(f"Registered channel: {channel.name}")

        if channel.in_queue:
            task = asyncio.create_task(self._pump(channel))
            self.tasks[channel.name] = task

    async def _pump(self, channel: GatewayChannel):
        try:
            while True:
                event = await channel.in_queue.get()
                await self.dispatch(event, origin=channel.name)
                channel.in_queue.task_done()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Channel gateway pump error for {channel.name}: {e}")

    def unregister(self, name: str):
        if name in self.channels:
            del self.channels[name]
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
        logger.info(f"Unregistered channel: {name}")

    def route(self, rule: GatewayRoute):
        self.routes.append(rule)

    def clear_routes(self):
        self.routes.clear()

    async def dispatch(self, event: GatewayEvent, origin: Optional[str] = None):
        matched_routes = [r for r in self.routes if r.match_func(event)]

        if matched_routes:
            for rule in matched_routes:
                targets = [self.channels[name] for name in rule.to if name in self.channels]

                if rule.mode == 'first':
                    target = next((c for c in targets if c.out_handler and c.name != origin), None)
                    if target:
                        if asyncio.iscoroutinefunction(target.out_handler):
                            await target.out_handler(event)
                        else:
                            target.out_handler(event)
                    continue

                for target in targets:
                    if not target.out_handler:
                        continue
                    if target.name == origin:
                        continue

                    if asyncio.iscoroutinefunction(target.out_handler):
                        await target.out_handler(event)
                    else:
                        target.out_handler(event)
            return

        # Default dispatch if no routes match
        for channel in self.channels.values():
            if channel.name == origin:
                continue
            if channel.can_handle and not channel.can_handle(event):
                continue
            if channel.out_handler:
                if asyncio.iscoroutinefunction(channel.out_handler):
                    await channel.out_handler(event)
                else:
                    channel.out_handler(event)

def create_channel_gateway() -> ChannelGateway:
    return ChannelGateway()
