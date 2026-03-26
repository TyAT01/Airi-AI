import logging
import asyncio
import time
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from nanoid import generate

from core.chat.session_store import ChatSessionStore
from core.chat.stream_store import ChatStreamStore
from core.chat.context_store import ChatContextStore
from core.chat.hooks import ChatHooks
from core.chat.context_providers import create_datetime_context
from core.utils.queues import create_queue
from llm.client import LLMClient

logger = logging.getLogger("airi_chat_orchestrator")

class QueuedSend(BaseModel):
    id: str = Field(default_factory=generate)
    sending_message: str
    session_id: str
    generation: int
    options: Dict[str, Any]
    cancelled: bool = False
    # In real Python, use Future or Deferred equivalent
    future: Optional[asyncio.Future] = None

    class Config:
        arbitrary_types_allowed = True

class ChatOrchestratorStore:
    def __init__(
        self,
        chat_session_store: ChatSessionStore,
        chat_stream_store: ChatStreamStore,
        chat_context_store: ChatContextStore,
        llm_client: LLMClient
    ):
        self.chat_session = chat_session_store
        self.chat_stream = chat_stream_store
        self.chat_context = chat_context_store
        self.llm = llm_client
        self.hooks = ChatHooks()

        self.sending = False
        self.pending_queued_sends: List[QueuedSend] = []

        self.send_queue = create_queue(
            handlers=[self._handle_queued_send]
        )

    async def ingest(self, message: str, options: Dict[str, Any], target_session_id: str = None):
        session_id = target_session_id or self.chat_session.active_session_id
        generation = self.chat_session.get_session_generation(session_id)

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        queued_send = QueuedSend(
            sending_message=message,
            session_id=session_id,
            generation=generation,
            options=options,
            future=future
        )
        self.pending_queued_sends.append(queued_send)
        await self.send_queue.enqueue(queued_send)
        return await future

    async def _handle_queued_send(self, queued_send: QueuedSend):
        if queued_send.cancelled:
            return

        if self.chat_session.get_session_generation(queued_send.session_id) != queued_send.generation:
            if queued_send.future:
                queued_send.future.set_exception(RuntimeError("Session reset"))
            return

        try:
            await self.perform_send(
                queued_send.sending_message,
                queued_send.options,
                queued_send.generation,
                queued_send.session_id
            )
            if queued_send.future:
                queued_send.future.set_result(None)
        except Exception as e:
            if queued_send.future:
                queued_send.future.set_exception(e)
        finally:
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.id != queued_send.id]

    async def perform_send(self, message: str, options: Dict[str, Any], generation: int, session_id: str):
        if not message and not options.get("attachments"):
            return

        self.chat_session.ensure_active_session_for_character()

        # Ingest datetime context
        self.chat_context.ingest_context_message(create_datetime_context())

        if self.chat_session.get_session_generation(session_id) != generation:
            return

        self.sending = True
        logger.info(f"Performing send for session {session_id}")

        try:
            await self.hooks.emit_before_message_composed(message, {})

            # Composed message logic
            session_messages = self.chat_session.get_session_messages(session_id)
            session_messages.append({
                "role": "user",
                "content": message,
                "createdAt": time.time(),
                "id": generate()
            })

            # Placeholder for final LLM call logic
            # await self.llm.stream_chat(model=options["model"], messages=session_messages)

            await self.chat_stream.finalize_stream()

        finally:
            self.sending = False

    async def cancel_pending_sends(self, session_id: str = None):
        for s in self.pending_queued_sends:
            if session_id and s.session_id != session_id:
                continue
            s.cancelled = True
            if s.future:
                s.future.set_exception(RuntimeError("Cancelled"))

        if session_id:
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.session_id != session_id]
        else:
            self.pending_queued_sends = []
        logger.info(f"Cancelled pending sends for session: {session_id or 'all'}")
