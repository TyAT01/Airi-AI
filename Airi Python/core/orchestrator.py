import time
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from nanoid import generate
from pydantic import BaseModel

from core.character import CharacterStore as CharacterState
from core.notebook import CharacterNotebook
from llm.client import LLMClient
from schemas.protocol import SparkNotifyEvent, SparkCommandEvent
from agents.spark_handler import SparkNotifyAgent

logger = logging.getLogger(__name__)

class CharacterOrchestrator:
    """
    Main orchestrator for character reactions and task management.
    Mimics packages/stage-ui/src/stores/character/orchestrator/store.ts.
    """
    def __init__(
        self,
        character: CharacterState,
        notebook: CharacterNotebook,
        llm: LLMClient,
        active_model: str = "gpt-4o",
        stt = None,
        tts = None,
        mods_server_channel_store = None
    ):
        self.character = character
        self.notebook = notebook
        self.llm = llm
        self.active_model = active_model
        self.stt = stt
        self.tts = tts
        self.mods_server_channel_store = mods_server_channel_store

        self.processing = False
        self.pending_notifies: List[SparkNotifyEvent] = []
        self.scheduled_notifies: List[Dict[str, Any]] = []

        self.tick_interval_ms = 2000
        self.task_notify_window_ms = 60000
        self.requeue_delay_ms = 30000
        self.max_attempts = 3

        self.running = False
        self.tick_task: Optional[asyncio.Task] = None

        self.spark_agent = SparkNotifyAgent(character, llm, active_model)

    async def start(self):
        if self.running:
            return
        self.running = True
        self.tick_task = asyncio.create_task(self.ticker())
        logger.info("CharacterOrchestrator started.")

    async def stop(self):
        self.running = False
        if self.tick_task:
            self.tick_task.cancel()
            try:
                await self.tick_task
            except asyncio.CancelledError:
                pass
        logger.info("CharacterOrchestrator stopped.")

    async def ticker(self):
        while self.running:
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Error in orchestrator tick: {e}")
            await asyncio.sleep(self.tick_interval_ms / 1000.0)

    async def tick(self):
        if self.processing:
            return

        now = time.time() * 1000 # Use milliseconds to match TS
        self.enqueue_due_tasks(now)

        if not self.scheduled_notifies:
            return

        # Find first due task
        now_ms = time.time() * 1000
        due_notifies = [n for n in self.scheduled_notifies if n["next_run_at"] <= now_ms]

        if not due_notifies:
            return

        # Take the first one
        next_item = due_notifies[0]
        self.scheduled_notifies.remove(next_item)
        self.remove_pending(next_item["event"].id)

        try:
            await self.process_spark_notify(next_item["event"])
        except Exception as e:
            logger.error(f"Failed to process spark:notify: {e}")
            if next_item["attempts"] + 1 < next_item["max_attempts"]:
                next_item["attempts"] += 1
                next_item["next_run_at"] = self.compute_next_run_at(next_item["event"], next_item["attempts"])
                self.scheduled_notifies.append(next_item)
                self.pending_notifies.append(next_item["event"])
            else:
                logger.warning(f"Dropped spark:notify {next_item['event'].id} after max attempts.")

    def compute_next_run_at(self, event: SparkNotifyEvent, attempts: int) -> float:
        now_ms = time.time() * 1000
        base_delay = 30000
        if event.urgency == "immediate":
            base_delay = 0
        elif event.urgency == "soon":
            base_delay = 10000
        elif event.urgency == "later":
            base_delay = 60000

        return now_ms + base_delay + (attempts * self.requeue_delay_ms)

    def remove_pending(self, event_id: str):
        self.pending_notifies = [n for n in self.pending_notifies if n.id != event_id]

    def enqueue_due_tasks(self, now_ms: float):
        due_tasks = self.notebook.get_due_tasks(now_ms / 1000.0, self.task_notify_window_ms)
        for task in due_tasks:
            # Check if already enqueued
            if any(n.event_id == task.id for n in self.pending_notifies):
                continue

            event = SparkNotifyEvent(
                id=f"task-{task.id}",
                eventId=task.id,
                kind="reminder",
                urgency="immediate" if task.priority == "critical" else "soon",
                headline=f"Task reminder: {task.title}",
                note=task.details,
                destinations=["character"],
                payload={"taskId": task.id, "priority": task.priority, "dueAt": task.due_at}
            )
            self.enqueue_spark_notify(event, reason="task:due")
            self.notebook.mark_task_notified(task.id, (now_ms + self.requeue_delay_ms) / 1000.0)

    def enqueue_spark_notify(self, event: SparkNotifyEvent, reason: str = None, next_run_at: float = None, max_attempts: int = None):
        if not any(n.id == event.id for n in self.pending_notifies):
            self.pending_notifies.append(event)

        self.scheduled_notifies.append({
            "event": event,
            "enqueued_at": time.time() * 1000,
            "next_run_at": next_run_at or self.compute_next_run_at(event, 0),
            "attempts": 0,
            "max_attempts": max_attempts or self.max_attempts,
            "reason": reason
        })

    async def process_spark_notify(self, event: SparkNotifyEvent):
        self.processing = True
        logger.info(f"Processing spark:notify: {event.headline}")

        try:
            # Use the specialized SparkNotifyAgent
            source_key = event.metadata.get("source", "unknown") if event.metadata else "unknown"
            result = await self.spark_agent.handle(event, source_key)

            if not result:
                return None

            reaction = result.get("reaction")
            if reaction:
                await self.character.on_spark_notify_reaction_stream_end(event.id, reaction)
                if self.tts:
                    await self.tts.speak(reaction)

            # Broadcast generated commands
            commands = result.get("commands", [])
            if commands and self.mods_server_channel_store:
                logger.info(f"Generated {len(commands)} commands from spark notify.")
                for command in commands:
                    self.mods_server_channel_store.send({
                        "type": "spark:command",
                        "data": command.dict(by_alias=True)
                    })

            return result

        except Exception as e:
            logger.error(f"Error processing spark notify: {e}")
            raise e
        finally:
            self.processing = False

    async def handle_incoming_spark_notify(self, event: SparkNotifyEvent):
        if event.urgency == "immediate" and not self.processing:
            return await self.process_spark_notify(event)

        self.enqueue_spark_notify(event, reason="incoming")
        return None

    def initialize(self):
        if self.mods_server_channel_store:
            # In a real system, you'd register event listeners here
            # self.mods_server_channel_store.on_event("spark:notify", self.handle_incoming_spark_notify)
            pass
        asyncio.create_task(self.start())
