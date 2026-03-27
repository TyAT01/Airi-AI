import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ChatSlice(BaseModel):
    type: str = "text"
    text: str = ""

class StreamingAssistantMessage(BaseModel):
    role: str = "assistant"
    content: str = ""
    slices: List[ChatSlice] = []
    tool_results: List[Dict[str, Any]] = []
    created_at: float = Field(default_factory=time.time)

class ChatStreamStore:
    def __init__(self, chat_session_store):
        self.chat_session = chat_session_store
        self.streaming_message = StreamingAssistantMessage()

    def begin_stream(self):
        self.streaming_message = StreamingAssistantMessage()

    def append_stream_literal(self, literal: str):
        self.streaming_message.content += literal

        if self.streaming_message.slices and self.streaming_message.slices[-1].type == "text":
            self.streaming_message.slices[-1].text += literal
        else:
            self.streaming_message.slices.append(ChatSlice(type="text", text=literal))

    def finalize_stream(self, full_text: Optional[str] = None):
        session_id = self.chat_session.active_session_id
        session_messages = self.chat_session.get_session_messages(session_id)

        if self.streaming_message.slices:
            session_messages.append(self.streaming_message.dict())

        # Reset streaming message
        self.streaming_message = StreamingAssistantMessage()
        if full_text:
            self.streaming_message.content = full_text

    def reset_stream(self):
        self.streaming_message = StreamingAssistantMessage()
