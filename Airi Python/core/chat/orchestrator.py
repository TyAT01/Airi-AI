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
from llm.client import LLMClient

logger = logging.getLogger("airi_chat_orchestrator")

class QueuedSend(BaseModel):
    id: str = Field(default_factory=generate)
    sending_message: str
    session_id: str
    generation: int
    options: Dict[str, Any]
    cancelled: bool = False

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

    async def ingest(self, message: str, options: Dict[str, Any], target_session_id: str = None):
        session_id = target_session_id or self.chat_session.active_session_id
        generation = self.chat_session.get_session_generation(session_id)

        queued_send = QueuedSend(
            sending_message=message,
            session_id=session_id,
            generation=generation,
            options=options
        )
        self.pending_queued_sends.append(queued_send)
        logger.info(f"Queued message for session {session_id}")

        # In real app, trigger queue processing
        await self.perform_send(message, options, generation, session_id)

    async def perform_send(self, message: str, options: Dict[str, Any], generation: int, session_id: str):
        if self.chat_session.get_session_generation(session_id) != generation:
            return

        self.sending = True
        try:
            logger.info(f"Performing send for session {session_id}")
            # Context and prompt injection logic here

            # Call LLM
            # response = await self.llm.stream_chat(...)

            # Finalize stream
            await self.chat_stream.finalize_stream()

        finally:
            self.sending = False
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.session_id != session_id]

    async def cancel_pending_sends(self, session_id: str = None):
        if session_id:
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.session_id != session_id]
        else:
            self.pending_queued_sends = []
        logger.info(f"Cancelled pending sends for session: {session_id or 'all'}")
