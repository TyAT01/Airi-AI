import asyncio
import logging
import os
import uvicorn
from typing import Optional, Dict, Any

from communication.server import AiriServer
from core.character import CharacterState
from core.notebook import CharacterNotebook
from core.orchestrator import CharacterOrchestrator
from core.character_cards import CharacterCardManager
from core.memory import MemorySystem
from llm.client import LLMClient
from perception.hearing import HearingStore, VisionStore
from expression.speech import SpeechPipeline
from agents.gaming import MinecraftModule, FactorioModule
from plugins.base import PluginManager
from schemas.protocol import SparkNotifyEvent

# Import new services
from services.api_server import AiriAPIServer
from services.discord_bot import DiscordService
from services.telegram_bot import TelegramService
from services.twitter import TwitterService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("airi_main")

async def main():
    # Load configuration
    api_key = os.getenv("OPENAI_API_KEY", "placeholder_key")
    discord_token = os.getenv("DISCORD_TOKEN", "")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # 1. Initialize Core components
    character = CharacterState(name="Airi")
    notebook = CharacterNotebook()
    memory = MemorySystem()
    llm = LLMClient(api_key=api_key)
    speech = SpeechPipeline()

    orchestrator = CharacterOrchestrator(
        character=character,
        notebook=notebook,
        llm=llm,
        tts=speech
    )

    # 2. Initialize Services
    api = AiriAPIServer()
    discord = DiscordService(discord_token, "ws://localhost:8000/ws")
    telegram = TelegramService(telegram_token)

    # 3. Initialize Server
    server = AiriServer()

    # 4. Mount API onto the main app or run separately
    # For this implementation, we combine them into the FastAPI app if possible
    # server.app.mount("/api", api.app) # Example integration

    # 5. Startup
    logger.info("Starting Airi Python Core and Services...")
    await orchestrator.start()

    # Background tasks for bots
    asyncio.create_task(discord.start())
    asyncio.create_task(telegram.start())

    # 6. Start Server
    config = uvicorn.Config(server.app, host="0.0.0.0", port=8000, log_level="info")
    uvicorn_server = uvicorn.Server(config)

    logger.info("Airi Python is fully operational.")
    await uvicorn_server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Airi Python...")
