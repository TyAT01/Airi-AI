import httpx
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

logger = logging.getLogger("airi_openai_compatible")

class OpenAICompatibleProvider:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            models = await self.client.models.list()
            return [{"id": m.id, "name": m.id} for m in models.data]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def chat_completion(self, model: str, messages: List[Dict[str, str]], stream: bool = False):
        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )
