import logging
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel
from llm.client import LLMClient

logger = logging.getLogger(__name__)

def build_openai_compatible_provider(options: Dict[str, Any]):
    provider_id = options.get("id")
    name = options.get("name")
    category = options.get("category")
    tasks = options.get("tasks", [])
    default_base_url = options.get("defaultBaseUrl")

    def create_provider(config: Dict[str, Any]) -> LLMClient:
        api_key = str(config.get("apiKey", "")).strip()
        base_url = str(config.get("baseUrl", default_base_url)).strip()
        if not api_key:
            raise ValueError(f"API key is required for provider {provider_id}")
        return LLMClient(api_key=api_key, base_url=base_url)

    metadata = {
        "id": provider_id,
        "name": name,
        "category": category,
        "tasks": tasks,
        "create_provider": create_provider,
        "capabilities": {
            "list_models": options.get("capabilities", {}).get("listModels"),
            "list_voices": options.get("capabilities", {}).get("listVoices")
        }
    }

    return metadata

async def list_openai_compatible_models(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    api_key = str(config.get("apiKey", "")).strip()
    base_url = str(config.get("baseUrl", "")).strip()
    if not api_key or not base_url:
        return []

    client = LLMClient(api_key=api_key, base_url=base_url)
    models = await client.list_models()
    return [{"id": m, "name": m} for m in models]
