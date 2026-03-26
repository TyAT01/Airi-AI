import logging
import re
from typing import List, Dict, Any, Optional, Callable, Awaitable
from llm.client import LLMClient

logger = logging.getLogger("airi_core_llm")

# Runtime auto-degrade: patterns that indicate the model/provider does not support tool calling.
TOOLS_RELATED_ERROR_PATTERNS = [
    re.compile(r"does not support tools", re.IGNORECASE), # Ollama
    re.compile(r"no endpoints found that support tool use", re.IGNORECASE), # OpenRouter
    re.compile(r"invalid schema for function", re.IGNORECASE), # OpenAI-compatible
    re.compile(r"invalid.?function.?parameters", re.IGNORECASE), # OpenAI-compatible
    re.compile(r"functions are not supported", re.IGNORECASE), # Azure AI Foundry
    re.compile(r"unrecognized request argument.+tools", re.IGNORECASE), # Azure AI Foundry
    re.compile(r"tool use with function calling is unsupported", re.IGNORECASE), # Google Generative AI
    re.compile(r"tool_use_failed", re.IGNORECASE), # Groq
    re.compile(r"does not support function.?calling", re.IGNORECASE), # Anthropic
    re.compile(r"tools?\s+(is|are)\s+not\s+supported", re.IGNORECASE), # Cloudflare Workers AI
]

def is_tool_related_error(err: Exception) -> bool:
    msg = str(err)
    return any(p.search(msg) for p in TOOLS_RELATED_ERROR_PATTERNS)

def sanitize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sanitized = []
    for m in messages:
        role = m.get("role")
        content = m.get("content")

        if role == "error":
            sanitized.append({
                "role": "user",
                "content": f"User encountered error: {str(content or '')}"
            })
            continue

        # NOTICE: Flatten array content for providers (e.g. DeepSeek) that expect string,
        # not content-part arrays. Skipped when image_url parts are present.
        if isinstance(content, list):
            has_image = any(isinstance(p, dict) and p.get("type") == "image_url" for p in content)
            if not has_image:
                text_content = "".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in content])
                sanitized.append({**m, "content": text_content})
                continue

        sanitized.append(m)
    return sanitized

class LLMStore:
    def __init__(self):
        self.tools_compatibility: Dict[str, bool] = {}

    def _model_key(self, model: str, base_url: str) -> str:
        return f"{base_url}-{model}"

    async def stream(
        self,
        llm_client: LLMClient,
        model: str,
        messages: List[Dict[str, Any]],
        on_delta: Optional[Callable[[str], Awaitable[None]]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        base_url = str(llm_client.client.base_url)
        key = self._model_key(model, base_url)

        sanitized = sanitize_messages(messages)

        effective_tools = tools
        if self.tools_compatibility.get(key) is False:
            effective_tools = None

        try:
            return await llm_client.stream_chat(
                model=model,
                messages=sanitized,
                on_delta=on_delta,
                tools=effective_tools,
                tool_choice=tool_choice if effective_tools else None
            )
        except Exception as e:
            if is_tool_related_error(e):
                logger.warning(f"[llm] Auto-disabling tools for \"{key}\" due to tool-related error")
                self.tools_compatibility[key] = False
            raise e

    async def models(self, llm_client: LLMClient) -> List[str]:
        return await llm_client.list_models()
