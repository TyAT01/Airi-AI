import asyncio
import json
import logging
from nanoid import generate

from core.character import CharacterState
from core.notebook import CharacterNotebook
from core.orchestrator import CharacterOrchestrator
from core.memory import MemorySystem
from schemas.protocol import SparkNotifyEvent
from expression.speech import SpeechPipeline

# Mock LLM Client
class MockLLMClient:
    async def stream_chat(self, model, messages, on_delta=None, tools=None):
        response_text = "Verification successful: I am fully operational."
        if on_delta:
            await on_delta(response_text)
        return {"text": response_text, "tool_calls": []}

async def verify_comprehensive():
    print("--- Starting Comprehensive Integration Verification ---")

    # 1. Setup
    character = CharacterState(name="AiriVerified")
    notebook = CharacterNotebook()
    memory = MemorySystem()
    llm = MockLLMClient()
    speech = SpeechPipeline()

    orchestrator = CharacterOrchestrator(
        character=character,
        notebook=notebook,
        llm=llm,
        tts=speech
    )

    print("1. All core modules initialized.")

    # 2. Test Memory
    print("2. Testing memory system...")
    await memory.store("User's favorite color is blue.")
    context = await memory.get_relevant_context("color")
    if "blue" in context:
        print(f"SUCCESS: Memory retrieved: '{context.strip()}'")
    else:
        print("FAILURE: Memory retrieval failed.")
        return False

    # 3. Trigger a spark:notify event
    notify_event = SparkNotifyEvent(
        id=generate(),
        eventId=generate(),
        kind="alarm",
        urgency="immediate",
        headline="System Check Requested",
        destinations=["character"]
    )

    print(f"3. Triggering spark:notify: {notify_event.headline}")
    await orchestrator.handle_incoming_spark_notify(notify_event)

    # 4. Verify reaction and speech
    print(f"4. Verifying reaction...")
    if len(character.reactions) > 0:
        print(f"SUCCESS: Character reacted: '{character.reactions[0].message}'")
    else:
        print("FAILURE: No character reaction recorded.")
        return False

    print("--- Comprehensive Verification Passed! ---")
    return True

if __name__ == "__main__":
    asyncio.run(verify_comprehensive())
