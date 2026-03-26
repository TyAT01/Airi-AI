import logging
import asyncio
import random
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_body")

class BodyState(BaseModel):
    blink: bool = False
    look_at: Dict[str, float] = {"x": 0, "y": 0, "z": 0}
    expression: str = "neutral"

class BodyController:
    def __init__(self):
        self.state = BodyState()
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self._auto_blink())
        asyncio.create_task(self._idle_movement())

    async def _auto_blink(self):
        while self.running:
            await asyncio.sleep(random.uniform(2, 6))
            self.state.blink = True
            logger.debug("Blink start")
            await asyncio.sleep(0.1)
            self.state.blink = False
            logger.debug("Blink end")

    async def _idle_movement(self):
        while self.running:
            await asyncio.sleep(random.uniform(3, 10))
            self.state.look_at = {
                "x": random.uniform(-0.1, 0.1),
                "y": random.uniform(-0.1, 0.1),
                "z": 1.0
            }
            logger.debug(f"Idle movement: {self.state.look_at}")

    def set_expression(self, expression: str):
        self.state.expression = expression
        logger.info(f"Set expression to: {expression}")

    def look_at(self, x: float, y: float, z: float):
        self.state.look_at = {"x": x, "y": y, "z": z}
        logger.info(f"Looking at: {self.state.look_at}")
