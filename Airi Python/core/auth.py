import logging
import asyncio
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_auth")

class User(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    image: Optional[str] = None

class Session(BaseModel):
    id: str
    user_id: str
    expires_at: float

class AuthStore:
    def __init__(self):
        self.user: Optional[User] = None
        self.session: Optional[Session] = None
        self.is_login_drawer_open = False
        self.initialized = False

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None and self.session is not None

    @property
    def user_id(self) -> str:
        return self.user.id if self.user else "local"

    async def initialize(self):
        if self.initialized:
            return

        logger.info("Initializing authentication state")
        await self.fetch_session()
        self.initialized = True

    async def fetch_session(self):
        # In a real Python app, we might check an OAuth session or similar
        # For now, it's a placeholder as in the original TS code (which just catches any errors)
        try:
            # Refresh or fetch the current session
            pass
        except Exception as e:
            logger.error(f"Failed to fetch session: {e}")
