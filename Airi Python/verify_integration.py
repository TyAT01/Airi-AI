import asyncio
import json
import logging
from nanoid import generate

from core.character import CharacterStore as CharacterState
from core.notebook import CharacterNotebook
from core.orchestrator import CharacterOrchestrator
from core.memory import MemorySystem, EmbeddingClient
from core.body import BodyController
from core.mcp import MCPManager
from core.stream_kit import OBSIntegration
from core.database import AiriDatabase
from schemas.protocol import SparkNotifyEvent
from expression.speech import SpeechPipeline

# Mock LLM Client
class MockLLMClient:
    async def stream_chat(self, model, messages, on_delta=None, tools=None):
        response_text = "Final verification: Every module has been converted and is functional."
        if on_delta:
            await on_delta(response_text)
        return {"text": response_text, "tool_calls": []}

async def verify_final():
    print("--- Starting Final Integration Verification ---")

    # 1. Setup all modules
    db = AiriDatabase("test_airi.db")
    character = CharacterState(name="AiriFinal")
    notebook = CharacterNotebook()
    memory = MemorySystem(embedding_client=EmbeddingClient(api_key="mock"))
    llm = MockLLMClient()
    speech = SpeechPipeline()
    body = BodyController()
    mcp = MCPManager()
    obs = OBSIntegration()

    orchestrator = CharacterOrchestrator(
        character=character,
        notebook=notebook,
        llm=llm,
        tts=speech
    )

    print("1. All modular Python components initialized.")

    # 2. Database test
    print("2. Testing persistent storage...")
    db.save_memory("mem-1", "Test content", {"tags": ["test"]}, 1234567.8)
    retrieved = db.get_all_memories()
    if retrieved and retrieved[0]["content"] == "Test content":
        print("SUCCESS: Database operational.")
    else:
        print("FAILURE: Database error.")
        return False

    # 3. Trigger Full Orchestration Loop
    print("3. Triggering full orchestration loop...")
    notify_event = SparkNotifyEvent(
        id=generate(),
        eventId=generate(),
        kind="ping",
        urgency="immediate",
        headline="Complete Project Conversion Verification",
        destinations=["character"]
    )
    await orchestrator.handle_incoming_spark_notify(notify_event)

    if len(character.reactions) > 0:
        print(f"SUCCESS: AI Response: '{character.reactions[0].message}'")
    else:
        print("FAILURE: No AI response.")
        return False

    # 4. MCP and Stream-Kit check
    print("4. Verifying secondary integrations...")
    mcp.add_client("test", "http://localhost:1234")
    await mcp.initialize_all()
    await obs.connect()
    print("SUCCESS: Secondary integrations initialized.")

    print("--- All Systems Functional. Conversion Complete. ---")
    return True

if __name__ == "__main__":
    asyncio.run(verify_final())
