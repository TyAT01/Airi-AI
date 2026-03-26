import asyncio
from typing import Callable, Awaitable, Optional

TAG_OPEN = '<|'
TAG_CLOSE = '|>'

class LLMMarkerParser:
    def __init__(
        self,
        on_literal: Callable[[str], Awaitable[None]] = None,
        on_special: Callable[[str], Awaitable[None]] = None,
        on_end: Callable[[str], Awaitable[None]] = None
    ):
        self.on_literal = on_literal
        self.on_special = on_special
        self.on_end = on_end
        self.buffer = ""
        self.in_tag = False
        self.full_text = ""

    async def consume(self, text_part: str):
        self.full_text += text_part
        self.buffer += text_part

        # Simple implementation of tag parsing
        while self.buffer:
            if not self.in_tag:
                open_idx = self.buffer.find(TAG_OPEN)
                if open_idx == -1:
                    # No tag start, emit literal if buffer is long enough to not be a partial tag
                    if len(self.buffer) > len(TAG_OPEN):
                        emit_len = len(self.buffer) - len(TAG_OPEN) + 1
                        emit = self.buffer[:emit_len]
                        self.buffer = self.buffer[emit_len:]
                        if self.on_literal:
                            await self.on_literal(emit)
                    break
                else:
                    if open_idx > 0:
                        emit = self.buffer[:open_idx]
                        self.buffer = self.buffer[open_idx:]
                        if self.on_literal:
                            await self.on_literal(emit)
                    self.in_tag = True
            else:
                close_idx = self.buffer.find(TAG_CLOSE)
                if close_idx == -1:
                    break
                else:
                    emit = self.buffer[:close_idx + len(TAG_CLOSE)]
                    self.buffer = self.buffer[close_idx + len(TAG_CLOSE):]
                    if self.on_special:
                        await self.on_special(emit)
                    self.in_tag = False

    async def end(self):
        if self.buffer and not self.in_tag:
            if self.on_literal:
                await self.on_literal(self.buffer)
        self.buffer = ""
        if self.on_end:
            await self.on_end(self.full_text)
