import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger("airi_chat_hooks")

class ChatHooks:
    def __init__(self):
        self._on_before_message_composed: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_after_message_composed: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_before_send: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_after_send: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_token_literal: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_token_special: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_stream_end: List[Callable[[Dict[str, Any]], Awaitable[None]]] = []
        self._on_assistant_response_end: List[Callable[[str, Dict[str, Any]], Awaitable[None]]] = []

    def on_before_message_composed(self, cb):
        self._on_before_message_composed.append(cb)
        return lambda: self._on_before_message_composed.remove(cb)

    def on_after_message_composed(self, cb):
        self._on_after_message_composed.append(cb)
        return lambda: self._on_after_message_composed.remove(cb)

    async def emit_before_message_composed(self, message: str, context: Dict[str, Any]):
        for hook in self._on_before_message_composed:
            await hook(message, context)

    async def emit_after_message_composed(self, message: str, context: Dict[str, Any]):
        for hook in self._on_after_message_composed:
            await hook(message, context)

    # ... and so on for other hooks
    def clear_hooks(self):
        self._on_before_message_composed.clear()
        self._on_after_message_composed.clear()
        self._on_before_send.clear()
        self._on_after_send.clear()
        self._on_token_literal.clear()
        self._on_token_special.clear()
        self._on_stream_end.clear()
        self._on_assistant_response_end.clear()
        logger.debug("Cleared all chat hooks")

def create_chat_hooks() -> ChatHooks:
    return ChatHooks()
