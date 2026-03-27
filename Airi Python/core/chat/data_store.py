import logging
import json
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ChatDataAccess:
    def __init__(self):
        self.active_session_id = "default"
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
        self.generations: Dict[str, int] = {}

    def get_active_session_id(self) -> str:
        return self.active_session_id

    def set_active_session_id(self, session_id: str):
        self.active_session_id = session_id

    def get_sessions(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.sessions

    def set_sessions(self, sessions: Dict[str, List[Dict[str, Any]]]):
        self.sessions = sessions

    def get_generations(self) -> Dict[str, int]:
        return self.generations

    def set_generations(self, generations: Dict[str, int]):
        self.generations = generations

class ChatDataStore:
    def __init__(self, access: ChatDataAccess):
        self.access = access

    def ensure_generation(self, session_id: str):
        generations = self.access.get_generations()
        if session_id not in generations:
            generations[session_id] = 0
            self.access.set_generations(generations)

    def get_session_generation(self, session_id: str) -> int:
        self.ensure_generation(session_id)
        return self.access.get_generations().get(session_id, 0)

    def bump_session_generation(self, session_id: str) -> int:
        next_gen = self.get_session_generation(session_id) + 1
        generations = self.access.get_generations()
        generations[session_id] = next_gen
        self.access.set_generations(generations)
        return next_gen

    def ensure_session(self, session_id: str, create_initial_message: Callable[[], Dict[str, Any]]):
        self.ensure_generation(session_id)
        sessions = self.access.get_sessions()
        if not sessions.get(session_id):
            sessions[session_id] = [create_initial_message()]
            self.access.set_sessions(sessions)

    def get_session_messages(self, session_id: str, create_initial_message: Callable[[], Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.ensure_session(session_id, create_initial_message)
        return self.access.get_sessions().get(session_id, [])

    def set_session_messages(self, session_id: str, next_messages: List[Dict[str, Any]]):
        sessions = self.access.get_sessions()
        sessions[session_id] = next_messages
        self.access.set_sessions(sessions)

    def set_active_session(self, session_id: str, create_initial_message: Callable[[], Dict[str, Any]]):
        self.access.set_active_session_id(session_id)
        self.ensure_session(session_id, create_initial_message)

    def get_active_session_id(self) -> str:
        return self.access.get_active_session_id()

    def reset_session(self, session_id: str, create_initial_message: Callable[[], Dict[str, Any]]):
        self.bump_session_generation(session_id)
        self.set_session_messages(session_id, [create_initial_message()])

    def refresh_system_messages(self, create_initial_message: Callable[[], Dict[str, Any]]):
        sessions = self.access.get_sessions()
        next_sessions = {}
        for session_id, history in sessions.items():
            if history and history[0].get("role") == "system":
                next_sessions[session_id] = [create_initial_message()] + history[1:]
            else:
                next_sessions[session_id] = history
        self.access.set_sessions(next_sessions)

    def reset_all_sessions(self, create_initial_message: Callable[[], Dict[str, Any]]):
        self.access.set_sessions({})
        self.access.set_generations({})
        self.access.set_active_session_id("default")
        self.ensure_session("default", create_initial_message)

    def get_all_sessions(self) -> Dict[str, List[Dict[str, Any]]]:
        return json.loads(json.dumps(self.access.get_sessions()))

def create_chat_data_store(access: ChatDataAccess) -> ChatDataStore:
    return ChatDataStore(access)
