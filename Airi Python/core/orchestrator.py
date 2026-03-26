import time
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from nanoid import generate
from pydantic import BaseModel

from core.character import CharacterState
from core.notebook import CharacterNotebook
from llm.client import LLMClient
from schemas.protocol import SparkNotifyEvent, SparkCommandEvent
from agents.spark_handler import SparkNotifyAgent

logger = logging.getLogger("airi_orchestrator")

class CharacterOrchestrator:
    def __init__(
        self,
        character: CharacterState,
        notebook: CharacterNotebook,
        llm: LLMClient,
        active_model: str = "gpt-4o",
        stt = None,
        tts = None
    ):
        self.character = character
        self.notebook = notebook
        self.llm = llm
        self.active_model = active_model
        self.stt = stt
        self.tts = tts
        self.processing = False
        self.pending_notifies: List[SparkNotifyEvent] = []
        self.scheduled_notifies: List[Dict[str, Any]] = []
        self.tick_interval_ms = 2000
        self.task_notify_window_ms = 60000
        self.requeue_delay_ms = 30000
        self.max_attempts = 3
        self.running = False
        self.spark_agent = SparkNotifyAgent(character, llm, active_model)

    async def start(self):
        self.running = True
        asyncio.create_task(self.ticker())

    async def ticker(self):
        while self.running:
            await self.tick()
            await asyncio.sleep(self.tick_interval_ms / 1000.0)

    async def tick(self):
        if self.processing:
            return

        now = time.time()
        self.enqueue_due_tasks(now)

        if not self.scheduled_notifies:
            return

        # Find next due task
        self.scheduled_notifies.sort(key=lambda x: x["next_run_at"])
        next_item = self.scheduled_notifies[0]

        if next_item["next_run_at"] <= now:
            self.scheduled_notifies.pop(0)
            await self.process_spark_notify(next_item["event"])

    def enqueue_due_tasks(self, now: float):
        due_tasks = self.notebook.get_due_tasks(now, self.task_notify_window_ms)
        for task in due_tasks:
            # Check if already enqueued
            if any(n.event_id == task.id for n in self.pending_notifies):
                continue

            event = SparkNotifyEvent(
                id=generate(),
                eventId=task.id,
                kind="reminder",
                urgency="immediate" if task.priority == "critical" else "soon",
                headline=f"Task reminder: {task.title}",
                note=task.details,
                destinations=["character"],
                payload={"taskId": task.id, "priority": task.priority}
            )
            self.enqueue_spark_notify(event, reason="task:due")
            self.notebook.mark_task_notified(task.id, now + self.requeue_delay_ms / 1000.0)

    def enqueue_spark_notify(self, event: SparkNotifyEvent, reason: str = None):
        if not any(n.id == event.id for n in self.pending_notifies):
            self.pending_notifies.append(event)

        self.scheduled_notifies.append({
            "event": event,
            "enqueued_at": time.time(),
            "next_run_at": self.compute_next_run_at(event, 0),
            "attempts": 0,
            "max_attempts": self.max_attempts,
            "reason": reason
        })

    def compute_next_run_at(self, event: SparkNotifyEvent, attempts: int) -> float:
        now = time.time()
        base_delay = 0
        if event.urgency == "soon":
            base_delay = 10
        elif event.urgency == "later":
            base_delay = 60

        return now + base_delay + (attempts * self.requeue_delay_ms / 1000.0)

    async def process_spark_notify(self, event: SparkNotifyEvent):
        self.processing = True
        logger.info(f"Processing spark:notify: {event.headline}")

        try:
            # Use the specialized SparkNotifyAgent
            response = await self.spark_agent.handle_event(event)

            self.character.record_reaction(
                message=response.reaction,
                source_event_id=event.id
            )

            if self.tts and response.reaction:
                await self.tts.speak(response.reaction)

            # Broadcast generated commands if any
            if response.commands:
                logger.info(f"Generated {len(response.commands)} commands from spark notify.")
                # Logic to send commands to server would go here

            # Remove from pending
            self.pending_notifies = [n for n in self.pending_notifies if n.id != event.id]

        except Exception as e:
            logger.error(f"Error processing spark notify: {e}")
        finally:
            self.processing = False

    async def handle_incoming_spark_notify(self, event: SparkNotifyEvent):
        if event.urgency == "immediate" and not self.processing:
            await self.process_spark_notify(event)
        else:
            self.enqueue_spark_notify(event, reason="incoming")
