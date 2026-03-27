import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, api_key: str, base_url: str = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        on_delta: Callable[[str], Awaitable[None]] = None,
        tools: List[Dict[str, Any]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:

        full_text = ""
        tool_calls = []

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                tools=tools,
                tool_choice=tool_choice if tools else None
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta

                if delta.content:
                    full_text += delta.content
                    if on_delta:
                        await on_delta(delta.content)

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls) <= tc.index:
                            tool_calls.append({
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": ""}
                            })
                        if tc.function.arguments:
                            tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

            return {
                "text": full_text,
                "tool_calls": tool_calls
            }

        except Exception as e:
            logger.error(f"LLM Stream Error: {e}")
            raise e

    async def list_models(self) -> List[str]:
        try:
            models = await self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
