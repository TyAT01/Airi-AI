import asyncio
import json
import logging
from nanoid import generate

from core.character import CharacterState
from core.notebook import CharacterNotebook
from core.orchestrator import CharacterOrchestrator
from core.memory import MemorySystem, EmbeddingClient
from core.body import BodyController
from schemas.protocol import SparkNotifyEvent
from expression.speech import SpeechPipeline
from expression.providers.elevenlabs import ElevenLabsProvider

# Mock LLM Client
class MockLLMClient:
    async def stream_chat(self, model, messages, on_delta=None, tools=None):
        response_text = "Verification successful: Advanced modules are online."
        if on_delta:
            await on_delta(response_text)
        return {"text": response_text, "tool_calls": []}

async def verify_advanced():
    print("--- Starting Advanced Integration Verification ---")

    # 1. Setup
    character = CharacterState(name="AiriAdvanced")
    notebook = CharacterNotebook()

    # Mock embedding client for memory
    embedding = EmbeddingClient(api_key="mock")
    memory = MemorySystem(embedding_client=embedding)

    llm = MockLLMClient()

    # Setup speech with a mock provider
    speech = SpeechPipeline(tts_provider=None)

    body = BodyController()

    orchestrator = CharacterOrchestrator(
        character=character,
        notebook=notebook,
        llm=llm,
        tts=speech
    )

    print("1. All advanced modules initialized.")

    # 2. Test Body Controller
    print("2. Testing body controller...")
    await body.start()
    await asyncio.sleep(0.1)
    body.look_at(0.5, 0.5, 1.0)
    if body.state.look_at["x"] == 0.5:
        print(f"SUCCESS: Body controller responding.")
    else:
        print("FAILURE: Body controller failed.")
        body.running = False
        return False
    body.running = False

    # 3. Test Memory with Mock Embedding
    print("3. Testing RAG memory...")
    await memory.store("Airi's favorite food is RAM.")
    context = await memory.get_relevant_context("food")
    if "RAM" in context:
        print(f"SUCCESS: RAG context retrieved.")
    else:
        print("FAILURE: RAG memory retrieval failed.")
        return False

    # 4. Trigger Orchestrator
    print("4. Triggering orchestrator with advanced setup...")
    notify_event = SparkNotifyEvent(
        id=generate(),
        eventId=generate(),
        kind="ping",
        urgency="immediate",
        headline="Advanced Verification",
        destinations=["character"]
    )
    await orchestrator.handle_incoming_spark_notify(notify_event)

    if len(character.reactions) > 0:
        print(f"SUCCESS: Advanced reaction generated: '{character.reactions[0].message}'")
    else:
        print("FAILURE: Advanced reaction failed.")
        return False

    print("--- Advanced Integration Verification Passed! ---")
    return True

if __name__ == "__main__":
    asyncio.run(verify_advanced())
