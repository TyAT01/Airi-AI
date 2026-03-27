import logging
import asyncio
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from nanoid import generate

from schemas.protocol import ModuleIdentity, PluginIdentity

logger = logging.getLogger(__name__)

class PluginSessionPhase(str, Literal):
    LOADING = "loading"
    LOADED = "loaded"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    ANNOUNCED = "announced"
    PREPARING = "preparing"
    WAITING_DEPS = "waiting-deps"
    PREPARED = "prepared"
    CONFIGURATION_NEEDED = "configuration-needed"
    CONFIGURED = "configured"
    READY = "ready"
    FAILED = "failed"
    STOPPED = "stopped"

class PluginSession(BaseModel):
    id: str = Field(default_factory=generate)
    name: str
    phase: PluginSessionPhase = PluginSessionPhase.LOADING
    identity: ModuleIdentity
    cwd: str = "."

class PluginHost:
    """
    Manages the lifecycle of AIRI plugins in Python.
    Mimics packages/plugin-sdk/src/plugin-host/core.ts logic.
    """
    def __init__(self):
        self.sessions: Dict[str, PluginSession] = {}
        self.registry: List[Dict[str, Any]] = []

    def load_plugin(self, name: str, plugin_id: str) -> str:
        session_id = generate()
        identity = ModuleIdentity(
            id=f"{plugin_id}-{generate(size=5)}",
            kind="plugin",
            plugin=PluginIdentity(id=plugin_id, version="0.1.0")
        )

        session = PluginSession(
            id=session_id,
            name=name,
            identity=identity,
            phase=PluginSessionPhase.LOADED
        )
        self.sessions[session_id] = session
        logger.info(f"Plugin {name} loaded in session {session_id}")
        return session_id

    async def start_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        try:
            session.phase = PluginSessionPhase.AUTHENTICATING
            await asyncio.sleep(0.1) # Simulate handshake

            session.phase = PluginSessionPhase.AUTHENTICATED
            session.phase = PluginSessionPhase.ANNOUNCED

            session.phase = PluginSessionPhase.PREPARING
            # Logic for dependencies would go here

            session.phase = PluginSessionPhase.PREPARED
            session.phase = PluginSessionPhase.CONFIGURED
            session.phase = PluginSessionPhase.READY

            logger.info(f"Plugin {session.name} is READY")
            self._update_registry()

        except Exception as e:
            session.phase = PluginSessionPhase.FAILED
            logger.error(f"Plugin {session.name} failed to start: {e}")

    def _update_registry(self):
        self.registry = [
            {"name": s.name, "identity": s.identity.dict()}
            for s in self.sessions.values() if s.phase == PluginSessionPhase.READY
        ]

    def stop_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].phase = PluginSessionPhase.STOPPED
            del self.sessions[session_id]
            self._update_registry()
            logger.info(f"Session {session_id} stopped.")

    def list_active_plugins(self) -> List[Dict[str, Any]]:
        return self.registry
