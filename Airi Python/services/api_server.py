from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

logger = logging.getLogger("airi_api_server")

class AiriAPIServer:
    def __init__(self):
        self.app = FastAPI(title="Project AIRI API")
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {"status": "ok"}

        @self.app.get("/api/characters")
        async def get_characters():
            # Placeholder for character service
            return []

        @self.app.get("/api/providers")
        async def get_providers():
            # Placeholder for provider service
            return []

    def get_app(self):
        return self.app
