import logging
import time
import json
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_chat_session_store")

class ChatHistoryItem(BaseModel):
    id: str = Field(default_factory=generate)
    role: str
    content: Any
    created_at: float = Field(default_factory=time.time, alias="createdAt")

class ChatSessionMeta(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    user_id: str = Field(..., alias="userId")
    character_id: str = Field(..., alias="characterId")
    title: Optional[str] = None
    created_at: float = Field(..., alias="createdAt")
    updated_at: float = Field(..., alias="updatedAt")

class ChatSessionRecord(BaseModel):
    meta: ChatSessionMeta
    messages: List[ChatHistoryItem]

class ChatSessionsIndex(BaseModel):
    user_id: str = Field(..., alias="userId")
    characters: Dict[str, Dict[str, Any]] = {}

class ChatSessionStore:
    def __init__(self, auth_store=None, airi_card_store=None):
        self.auth_store = auth_store
        self.airi_card_store = airi_card_store

        self.active_session_id: str = ""
        self.session_messages: Dict[str, List[ChatHistoryItem]] = {}
        self.session_metas: Dict[str, ChatSessionMeta] = {}
        self.session_generations: Dict[str, int] = {}
        self.index: Optional[ChatSessionsIndex] = None

        self.ready = False
        self.loaded_sessions: Set[str] = set()

    def get_current_user_id(self) -> str:
        return self.auth_store.user_id if self.auth_store else "local"

    def get_current_character_id(self) -> str:
        # In TS it uses active_card_id from airi_card_store
        return "default"

    async def initialize(self):
        if self.ready:
            return
        logger.info("Initializing chat session store")
        await self.ensure_active_session_for_character()
        self.ready = True

    async def create_session(self, character_id: str, title: str = None, messages: List[ChatHistoryItem] = None, set_active: bool = True) -> str:
        session_id = generate()
        now = time.time()
        user_id = self.get_current_user_id()

        meta = ChatSessionMeta(
            sessionId=session_id,
            userId=user_id,
            character_id=character_id,
            title=title,
            createdAt=now,
            updatedAt=now
        )

        initial_messages = messages if messages else [] # Should include system prompt

        self.session_metas[session_id] = meta
        self.session_messages[session_id] = initial_messages
        self.session_generations[session_id] = 0

        if set_active:
            self.active_session_id = session_id

        logger.info(f"Created chat session: {session_id}")
        return session_id

    async def ensure_active_session_for_character(self):
        character_id = self.get_current_character_id()
        if not self.active_session_id:
            await self.create_session(character_id)

    def get_session_messages(self, session_id: str) -> List[ChatHistoryItem]:
        return self.session_messages.get(session_id, [])

    def get_session_generation(self, session_id: str) -> int:
        return self.session_generations.get(session_id, 0)

    def bump_session_generation(self, session_id: str) -> int:
        gen = self.session_generations.get(session_id, 0) + 1
        self.session_generations[session_id] = gen
        return gen

    async def cleanup_messages(self, session_id: str):
        # In TS this resets the session with the initial message
        self.bump_session_generation(session_id)
        self.session_messages[session_id] = [] # Should be system message in real app
        logger.info(f"Cleaned up messages for session: {session_id}")

    async def reset_all_sessions(self):
        self.session_messages = {}
        self.session_metas = {}
        self.session_generations = {}
        self.loaded_sessions.clear()
        await self.ensure_active_session_for_character()
        logger.info("Reset all chat sessions")
