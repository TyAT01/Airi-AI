import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_chat_stream_store")

class StreamingAssistantMessage(BaseModel):
    role: str = "assistant"
    content: str = ""
    slices: List[Dict[str, Any]] = []
    tool_results: List[Any] = Field([], alias="tool_results")
    created_at: float = Field(default_factory=time.time, alias="createdAt")

class ChatStreamStore:
    def __init__(self, chat_session_store=None):
        self.chat_session = chat_session_store
        self.streaming_message = StreamingAssistantMessage()

    def begin_stream(self):
        self.streaming_message = StreamingAssistantMessage()
        logger.debug("Began chat stream")

    def append_stream_literal(self, literal: str):
        self.streaming_message.content += literal

        if self.streaming_message.slices and self.streaming_message.slices[-1].get("type") == "text":
            self.streaming_message.slices[-1]["text"] += literal
        else:
            self.streaming_message.slices.append({
                "type": "text",
                "text": literal
            })

    async def finalize_stream(self, full_text: str = None):
        if self.chat_session:
            session_id = self.chat_session.active_session_id
            messages = self.chat_session.get_session_messages(session_id)
            if self.streaming_message.slices:
                # In a real app, convert streaming_message to ChatHistoryItem
                pass

            # Persist session messages logic here

        self.streaming_message = StreamingAssistantMessage()
        if full_text:
            self.streaming_message.content = full_text
        logger.debug("Finalized chat stream")

    def reset_stream(self):
        self.streaming_message = StreamingAssistantMessage()
        logger.debug("Reset chat stream")
