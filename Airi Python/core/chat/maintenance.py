import logging
from typing import Optional

logger = logging.getLogger("airi_chat_maintenance_store")

class ChatMaintenanceStore:
    def __init__(self, chat_session_store, chat_stream_store, chat_context_store, chat_orchestrator_store):
        self.chat_session = chat_session_store
        self.chat_stream = chat_stream_store
        self.chat_context = chat_context_store
        self.chat_orchestrator = chat_orchestrator_store

    async def cleanup_messages(self, session_id: Optional[str] = None):
        target_id = session_id or self.chat_session.active_session_id
        await self.chat_session.cleanup_messages(target_id)
        self.chat_context.reset_contexts()
        if self.chat_orchestrator:
            await self.chat_orchestrator.cancel_pending_sends(target_id)
        self.chat_stream.reset_stream()
        logger.info(f"Cleaned up chat messages for session: {target_id}")
