import time
import json
import logging
from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_chat_session")

class ChatMessage(BaseModel):
    id: str = Field(default_factory=generate)
    role: Literal["user", "assistant", "system", "tool"]
    content: Union[str, List[Dict[str, Any]]]
    created_at: float = Field(default_factory=time.ctime, alias="createdAt")
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionMeta(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    user_id: str = Field(..., alias="userId")
    character_id: str = Field(..., alias="characterId")
    title: Optional[str] = None
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    updated_at: float = Field(default_factory=time.time, alias="updatedAt")

class ChatSessionRecord(BaseModel):
    meta: ChatSessionMeta
    messages: List[ChatMessage]

class ChatSessionStore:
    def __init__(self, character_id: str = "default", user_id: str = "local"):
        self.character_id = character_id
        self.user_id = user_id
        self.active_session_id: Optional[str] = None
        self.session_messages: Dict[str, List[ChatMessage]] = {}
        self.session_metas: Dict[str, ChatSessionMeta] = {}
        self.session_generations: Dict[str, int] = {}

    def generate_initial_message(self, system_prompt: str) -> ChatMessage:
        content = system_prompt
        # Original adds code block and math syntax prompts here
        return ChatMessage(role="system", content=content)

    def ensure_session(self, session_id: str, system_prompt: str = ""):
        if session_id not in self.session_generations:
            self.session_generations[session_id] = 0
        if session_id not in self.session_messages or not self.session_messages[session_id]:
            self.session_messages[session_id] = [self.generate_initial_message(system_prompt)]
            # In a real app, persist here

    def create_session(self, character_id: str, system_prompt: str = "", title: str = None) -> str:
        session_id = generate()
        now = time.time()
        meta = ChatSessionMeta(
            sessionId=session_id,
            userId=self.user_id,
            characterId=character_id,
            title=title,
            createdAt=now,
            updatedAt=now
        )
        self.session_metas[session_id] = meta
        self.session_messages[session_id] = [self.generate_initial_message(system_prompt)]
        self.session_generations[session_id] = 0
        return session_id

    def fork_session(self, from_session_id: str, at_index: int = None) -> str:
        if from_session_id not in self.session_messages:
            raise ValueError(f"Session {from_session_id} not found")

        parent_messages = self.session_messages[from_session_id]
        fork_index = at_index if at_index is not None else len(parent_messages)
        new_messages = [m.copy(deep=True) for m in parent_messages[:fork_index]]

        new_session_id = self.create_session(self.character_id)
        self.session_messages[new_session_id] = new_messages
        return new_session_id

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self.session_messages.get(session_id, [])

    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self.session_messages:
            self.session_messages[session_id] = []
        self.session_messages[session_id].append(message)
        if session_id in self.session_metas:
            self.session_metas[session_id].updated_at = time.time()

    def bump_generation(self, session_id: str) -> int:
        gen = self.session_generations.get(session_id, 0) + 1
        self.session_generations[session_id] = gen
        return gen
