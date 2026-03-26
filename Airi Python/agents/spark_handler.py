import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable
from nanoid import generate
from pydantic import BaseModel

from schemas.protocol import SparkNotifyEvent, SparkCommandEvent, SparkCommandGuidance
from llm.client import LLMClient
from core.character import CharacterState

logger = logging.getLogger("airi_spark_handler")

class SparkNotifyResponse(BaseModel):
    reaction: Optional[str] = None
    commands: List[Dict[str, Any]] = []

class SparkNotifyAgent:
    def __init__(self, character: CharacterState, llm: LLMClient, active_model: str = "gpt-4o"):
        self.character = character
        self.llm = llm
        self.active_model = active_model

    def get_instruction(self, source_name: str) -> str:
        return (
            "This is AIRI system, the life pod hosting your consciousness. "
            "You don't need to respond to me or every spark:notify event directly.\n"
            f"Another module \"{source_name}\" triggered spark:notify event for you to checkout.\n"
            "You may call the built-in tool \"builtIn_sparkCommand\" to issue spark:command to sub-agents as needed.\n"
            "For any of the output that is not a tool call, it will be streamed to user's interface."
        )

    async def handle_event(self, event: SparkNotifyEvent, source_key: str = "unknown") -> SparkNotifyResponse:
        system_prompt = f"{self.character.system_prompt}\n\n{self.get_instruction(source_key)}"

        user_msg = json.dumps({
            "notify": event.dict(by_alias=True),
        }, indent=2)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        # Simplified tool handling logic for Python port
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "builtIn_sparkNoResponse",
                    "description": "Indicate that no response or action is needed.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "builtIn_sparkCommand",
                    "description": "Issue a spark:command to sub-agents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "destinations": {"type": "array", "items": {"type": "string"}},
                                        "priority": {"type": "string", "enum": ["critical", "high", "normal", "low"]},
                                        "ack": {"type": "string"}
                                    },
                                    "required": ["destinations", "ack"]
                                }
                            }
                        },
                        "required": ["commands"]
                    }
                }
            }
        ]

        response = await self.llm.stream_chat(
            model=self.active_model,
            messages=messages,
            tools=tools
        )

        reaction = response.get("text", "")
        commands = []

        for tc in response.get("tool_calls", []):
            if tc["function"]["name"] == "builtIn_sparkCommand":
                try:
                    args = json.loads(tc["function"]["arguments"])
                    for cmd_draft in args.get("commands", []):
                        command = SparkCommandEvent(
                            id=generate(),
                            commandId=generate(),
                            parentEventId=event.id,
                            interrupt=False, # Default
                            priority=cmd_draft.get("priority", "normal"),
                            intent="action",
                            ack=cmd_draft.get("ack"),
                            destinations=cmd_draft.get("destinations")
                        )
                        commands.append(command.dict(by_alias=True))
                except Exception as e:
                    logger.error(f"Failed to parse spark command tools: {e}")

        return SparkNotifyResponse(reaction=reaction, commands=commands)
