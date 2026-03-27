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
        self._on_assistant_message: List[Callable[[Dict[str, Any], str, Dict[str, Any]], Awaitable[None]]] = []
        self._on_chat_turn_complete: List[Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[None]]] = []

    def on_before_message_composed(self, cb):
        self._on_before_message_composed.append(cb)
        return lambda: self._on_before_message_composed.remove(cb)

    def on_after_message_composed(self, cb):
        self._on_after_message_composed.append(cb)
        return lambda: self._on_after_message_composed.remove(cb)

    def on_before_send(self, cb):
        self._on_before_send.append(cb)
        return lambda: self._on_before_send.remove(cb)

    def on_after_send(self, cb):
        self._on_after_send.append(cb)
        return lambda: self._on_after_send.remove(cb)

    def on_token_literal(self, cb):
        self._on_token_literal.append(cb)
        return lambda: self._on_token_literal.remove(cb)

    def on_token_special(self, cb):
        self._on_token_special.append(cb)
        return lambda: self._on_token_special.remove(cb)

    def on_stream_end(self, cb):
        self._on_stream_end.append(cb)
        return lambda: self._on_stream_end.remove(cb)

    def on_assistant_response_end(self, cb):
        self._on_assistant_response_end.append(cb)
        return lambda: self._on_assistant_response_end.remove(cb)

    def on_assistant_message(self, cb):
        self._on_assistant_message.append(cb)
        return lambda: self._on_assistant_message.remove(cb)

    def on_chat_turn_complete(self, cb):
        self._on_chat_turn_complete.append(cb)
        return lambda: self._on_chat_turn_complete.remove(cb)

    async def emit_before_message_composed(self, message: str, context: Dict[str, Any]):
        for hook in self._on_before_message_composed:
            await hook(message, context)

    async def emit_after_message_composed(self, message: str, context: Dict[str, Any]):
        for hook in self._on_after_message_composed:
            await hook(message, context)

    async def emit_before_send(self, message: str, context: Dict[str, Any]):
        for hook in self._on_before_send:
            await hook(message, context)

    async def emit_after_send(self, message: str, context: Dict[str, Any]):
        for hook in self._on_after_send:
            await hook(message, context)

    async def emit_token_literal(self, literal: str, context: Dict[str, Any]):
        for hook in self._on_token_literal:
            await hook(literal, context)

    async def emit_token_special(self, special: str, context: Dict[str, Any]):
        for hook in self._on_token_special:
            await hook(special, context)

    async def emit_stream_end(self, context: Dict[str, Any]):
        for hook in self._on_stream_end:
            await hook(context)

    async def emit_assistant_response_end(self, message: str, context: Dict[str, Any]):
        for hook in self._on_assistant_response_end:
            await hook(message, context)

    async def emit_assistant_message(self, message: Dict[str, Any], message_text: str, context: Dict[str, Any]):
        for hook in self._on_assistant_message:
            await hook(message, message_text, context)

    async def emit_chat_turn_complete(self, chat: Dict[str, Any], context: Dict[str, Any]):
        for hook in self._on_chat_turn_complete:
            await hook(chat, context)

    def clear_hooks(self):
        self._on_before_message_composed.clear()
        self._on_after_message_composed.clear()
        self._on_before_send.clear()
        self._on_after_send.clear()
        self._on_token_literal.clear()
        self._on_token_special.clear()
        self._on_stream_end.clear()
        self._on_assistant_response_end.clear()
        self._on_assistant_message.clear()
        self._on_chat_turn_complete.clear()
        logger.debug("Cleared all chat hooks")

def create_chat_hooks() -> ChatHooks:
    return ChatHooks()
