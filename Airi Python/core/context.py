import logging
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from core.utils.event_source import get_event_source_key

logger = logging.getLogger("airi_context")

class ContextMessage(BaseModel):
    id: str
    context_id: str = Field(..., alias="contextId")
    strategy: Literal["replace-self", "append-self"] = "replace-self"
    text: str
    metadata: Optional[Dict[str, Any]] = None

class ContextHistoryEntry(ContextMessage):
    source_key: str = Field(..., alias="sourceKey")

class ContextStore:
    def __init__(self, history_limit: int = 400):
        self.active_contexts: Dict[str, List[ContextMessage]] = {}
        self.context_history: List[ContextHistoryEntry] = []
        self.history_limit = history_limit

    def ingest_context_message(self, envelope: Dict[str, Any]):
        source_key = get_event_source_key(envelope)

        # Extract context message from envelope data
        data = envelope.get("data", {})
        try:
            message = ContextMessage(**data)
        except Exception as e:
            logger.error(f"Failed to parse context message: {e}")
            return

        if source_key not in self.active_contexts:
            self.active_contexts[source_key] = []

        if message.strategy == "replace-self":
            self.active_contexts[source_key] = [message]
        elif message.strategy == "append-self":
            self.active_contexts[source_key].append(message)

        history_entry = ContextHistoryEntry(
            **message.dict(by_alias=True),
            sourceKey=source_key
        )
        self.context_history.append(history_entry)

        if len(self.context_history) > self.history_limit:
            self.context_history.pop(0)

    def reset(self):
        self.active_contexts = {}
        self.context_history = []

    def get_contexts_snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        return {k: [m.dict(by_alias=True) for m in v] for k, v in self.active_contexts.items()}
