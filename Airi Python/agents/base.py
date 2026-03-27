import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from nanoid import generate

from schemas.protocol import SparkNotifyEvent, SparkCommandEvent

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name

    async def handle_command(self, command: SparkCommandEvent):
        logger.info(f"Agent {self.name} received command: {command.ack}")
        # Implement logic for sub-agents here
        pass

    async def emit_notify(self, headline: str, note: str = None, urgency: str = "soon") -> SparkNotifyEvent:
        event = SparkNotifyEvent(
            id=generate(),
            eventId=generate(),
            kind="ping",
            urgency=urgency,
            headline=headline,
            note=note,
            destinations=["character"]
        )
        return event
