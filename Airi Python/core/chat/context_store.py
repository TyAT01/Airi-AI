import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_chat_context_store")

CONTEXT_HISTORY_LIMIT = 400

class ContextMessage(BaseModel):
    role: str
    content: str
    strategy: str = "replace-self"
    metadata: Optional[Dict[str, Any]] = None

class ContextHistoryEntry(ContextMessage):
    source_key: str = Field(..., alias="sourceKey")

class ChatContextStore:
    def __init__(self):
        self.active_contexts: Dict[str, List[ContextMessage]] = {}
        self.context_history: List[ContextHistoryEntry] = []

    def ingest_context_message(self, envelope: ContextMessage, source_key: str):
        if source_key not in self.active_contexts:
            self.active_contexts[source_key] = []

        if envelope.strategy == "replace-self":
            self.active_contexts[source_key] = [envelope]
        elif envelope.strategy == "append-self":
            self.active_contexts[source_key].append(envelope)

        history_entry = ContextHistoryEntry(
            role=envelope.role,
            content=envelope.content,
            strategy=envelope.strategy,
            metadata=envelope.metadata,
            sourceKey=source_key
        )
        self.context_history.append(history_entry)

        if len(self.context_history) > CONTEXT_HISTORY_LIMIT:
            self.context_history = self.context_history[-CONTEXT_HISTORY_LIMIT:]

        logger.debug(f"Ingested context message from {source_key}")

    def reset_contexts(self):
        self.active_contexts = {}
        self.context_history = []
        logger.info("Chat contexts reset")

    def get_contexts_snapshot(self) -> Dict[str, List[ContextMessage]]:
        return self.active_contexts
