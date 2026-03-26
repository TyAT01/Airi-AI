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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("airi_main")

async def main():
    # Load configuration from environment or use defaults
    api_key = os.getenv("OPENAI_API_KEY", "placeholder_key")
    base_url = os.getenv("OPENAI_BASE_URL", None)

    # 1. Initialize Core components
    character_card_manager = CharacterCardManager()
    character = CharacterState(name="Airi")
    notebook = CharacterNotebook()
    memory = MemorySystem()
    llm = LLMClient(api_key=api_key, base_url=base_url)

    # 2. Initialize Perception & Expression
    hearing = HearingStore()
    vision = VisionStore()
    speech = SpeechPipeline()

    # 3. Initialize Orchestrator
    orchestrator = CharacterOrchestrator(
        character=character,
        notebook=notebook,
        llm=llm,
        active_model="gpt-4o",
        tts=speech
    )

    # 4. Initialize Gaming Modules
    minecraft = MinecraftModule()
    factorio = FactorioModule()

    # 5. Initialize Plugin Manager
    plugin_manager = PluginManager()
    # (Future: dynamic plugin loading)

    # 6. Initialize Server
    server = AiriServer()

    # 7. Integration Logic
    async def on_server_event(event_dict: Dict[str, Any]):
        event_type = event_dict.get("type")

        # Broadcast to plugins
        await plugin_manager.broadcast_event(event_dict)

        if event_type == "spark:notify":
            try:
                event = SparkNotifyEvent(**event_dict["data"])
                await orchestrator.handle_incoming_spark_notify(event)
            except Exception as e:
                logger.error(f"Failed to handle spark:notify in orchestrator: {e}")

        elif event_type == "input:text":
            # Direct text input handling
            text = event_dict["data"].get("text", "")
            logger.info(f"Direct text input received: {text}")
            # Could trigger orchestrator directly here

    server.set_on_event_callback(on_server_event)

    # 8. Startup
    logger.info("Starting Airi Python Core...")
    await orchestrator.start()
    await plugin_manager.initialize_all()

    # 9. Start Server
    config = uvicorn.Config(server.app, host="0.0.0.0", port=8000, log_level="info")
    uvicorn_server = uvicorn.Server(config)

    logger.info("Airi Python is fully initialized and ready.")
    await uvicorn_server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down Airi Python...")
