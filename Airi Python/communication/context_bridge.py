import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable
from nanoid import generate
from pydantic import BaseModel

from core.chat.orchestrator import ChatOrchestratorStore
from core.chat.session_store import ChatSessionStore
from core.chat.stream_store import ChatStreamStore
from core.chat.context_store import ChatContextStore
from core.consciousness import ConsciousnessStore
from core.providers import ProvidersStore
from communication.server import AiriServer

logger = logging.getLogger(__name__)

class ContextMessage(BaseModel):
    id: str
    contextId: str
    content: Any
    metadata: Dict[str, Any] = {}
    createdAt: float

class ContextBridge:
    def __init__(
        self,
        chat_orchestrator: ChatOrchestratorStore,
        chat_session: ChatSessionStore,
        chat_stream: ChatStreamStore,
        chat_context: ChatContextStore,
        server: AiriServer,
        consciousness: ConsciousnessStore,
        providers: ProvidersStore
    ):
        self.chat_orchestrator = chat_orchestrator
        self.chat_session = chat_session
        self.chat_stream = chat_stream
        self.chat_context = chat_context
        self.server = server
        self.consciousness = consciousness
        self.providers = providers
        self.is_processing_remote_stream = False
        self.remote_stream_guard = None
        self.dispose_fns = []

    async def initialize(self):
        # Register for server events
        self.server.set_on_event_callback(self.handle_server_event)

        # Register hooks for chat orchestrator
        # Porting JS hooks to Python hooks (assuming ChatOrchestratorStore has similar hook registration)
        self.chat_orchestrator.hooks.on_before_message_composed(self.on_before_message_composed)
        self.chat_orchestrator.hooks.on_after_message_composed(self.on_after_message_composed)
        self.chat_orchestrator.hooks.on_before_send(self.on_before_send)
        self.chat_orchestrator.hooks.on_after_send(self.on_after_send)
        self.chat_orchestrator.hooks.on_assistant_message(self.on_assistant_message)
        # ... others

    async def handle_server_event(self, event: Dict[str, Any]):
        event_type = event.get("type")
        if event_type == "context:update":
            context_message = ContextMessage(
                id=event["data"].get("id", generate()),
                contextId=event["data"].get("contextId", generate()),
                content=event["data"].get("content"),
                metadata=event.get("metadata", {}),
                createdAt=time.time() * 1000
            )
            self.chat_context.ingest_context_message(context_message.dict())
            # In Python, we might not need broadcast channel if it's one process,
            # but we can notify other components if needed.

        elif event_type == "input:text":
            await self.handle_input_text(event)

    async def handle_input_text(self, event: Dict[str, Any]):
        data = event.get("data", {})
        text = data.get("text", "")
        context_updates = data.get("contextUpdates", [])

        if context_updates:
            for update in context_updates:
                update["id"] = update.get("id", generate())
                update["contextId"] = update.get("contextId", update["id"])
                self.chat_context.ingest_context_message({
                    **update,
                    "metadata": event.get("metadata", {}),
                    "createdAt": time.time() * 1000
                })

        if self.consciousness.active_provider and self.consciousness.active_model:
            # Simplified ingestion
            message_text = text
            overrides = data.get("overrides", {})
            if overrides.get("messagePrefix"):
                message_text = f"{overrides['messagePrefix']}{text}"

            target_session_id = overrides.get("sessionId")

            # Simulate Lock or sequential execution
            await self.chat_orchestrator.ingest(
                message_text,
                {
                    "model": self.consciousness.active_model,
                    "input": {
                        "type": "input:text",
                        "data": data
                    }
                },
                target_session_id
            )

    async def on_before_message_composed(self, message, context):
        if self.is_processing_remote_stream:
            return
        # Broadcast logic if needed

    async def on_assistant_message(self, message, message_text, context):
        await self.server.broadcast({
            "type": "output:gen-ai:chat:message",
            "data": {
                **context.get("input", {}).get("data", {}),
                "message": message,
                "gen-ai:chat": {
                    "message": context.get("message"),
                    "composedMessage": context.get("composedMessage"),
                    "contexts": context.get("contexts"),
                    "input": context.get("input")
                }
            }
        })

    def dispose(self):
        # Cleanup logic
        pass
