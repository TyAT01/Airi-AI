import logging
import asyncio
import time
import json
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from nanoid import generate

from core.chat.session_store import ChatSessionStore, ChatHistoryItem
from core.chat.stream_store import ChatStreamStore, StreamingAssistantMessage, ChatSlice
from core.chat.context_store import ChatContextStore
from core.chat.hooks import ChatHooks
from core.chat.context_providers import create_datetime_context
from core.utils.queues import create_queue
from core.utils.llm_marker_parser import LLMMarkerParser
from core.utils.response_categoriser import StreamingCategorizer, categorize_response
from llm.client import LLMClient

logger = logging.getLogger("airi_chat_orchestrator")

class QueuedSend(BaseModel):
    id: str = Field(default_factory=generate)
    sending_message: str
    session_id: str
    generation: int
    options: Dict[str, Any]
    cancelled: bool = False
    # In real Python, use Future or Deferred equivalent
    future: Optional[asyncio.Future] = None

    class Config:
        arbitrary_types_allowed = True

class ChatOrchestratorStore:
    def __init__(
        self,
        chat_session_store: ChatSessionStore,
        chat_stream_store: ChatStreamStore,
        chat_context_store: ChatContextStore,
        llm_client: LLMClient
    ):
        self.chat_session = chat_session_store
        self.chat_stream = chat_stream_store
        self.chat_context = chat_context_store
        self.llm = llm_client
        self.hooks = ChatHooks()

        self.sending = False
        self.pending_queued_sends: List[QueuedSend] = []

        self.send_queue = create_queue(
            handlers=[self._handle_queued_send]
        )

    async def ingest(self, message: str, options: Dict[str, Any], target_session_id: str = None):
        session_id = target_session_id or self.chat_session.active_session_id
        generation = self.chat_session.get_session_generation(session_id)

        loop = asyncio.get_event_loop()
        future = loop.create_future()

        queued_send = QueuedSend(
            sending_message=message,
            session_id=session_id,
            generation=generation,
            options=options,
            future=future
        )
        self.pending_queued_sends.append(queued_send)
        await self.send_queue.enqueue(queued_send)
        return await future

    async def _handle_queued_send(self, queued_send: QueuedSend):
        if queued_send.cancelled:
            return

        if self.chat_session.get_session_generation(queued_send.session_id) != queued_send.generation:
            if queued_send.future:
                queued_send.future.set_exception(RuntimeError("Session reset"))
            return

        try:
            await self.perform_send(
                queued_send.sending_message,
                queued_send.options,
                queued_send.generation,
                queued_send.session_id
            )
            if queued_send.future:
                queued_send.future.set_result(None)
        except Exception as e:
            if queued_send.future:
                queued_send.future.set_exception(e)
        finally:
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.id != queued_send.id]

    async def perform_send(self, message: str, options: Dict[str, Any], generation: int, session_id: str):
        if not message and not options.get("attachments"):
            return

        self.chat_session.ensure_session(session_id)

        # Inject current datetime context before composing the message
        self.chat_context.ingest_context_message(create_datetime_context())

        is_stale_generation = lambda: self.chat_session.get_session_generation(session_id) != generation
        if is_stale_generation():
            return

        self.sending = True
        logger.info(f"Performing send for session {session_id}")

        building_message = StreamingAssistantMessage(
            role="assistant",
            content="",
            slices=[],
            tool_results=[],
            created_at=time.time()
        )

        user_msg_id = generate()
        user_msg_created_at = time.time()

        streaming_message_context = {
            "message": {"role": "user", "content": message, "createdAt": user_msg_created_at, "id": user_msg_id},
            "contexts": self.chat_context.get_contexts_snapshot(),
            "composedMessage": [],
            "input": options.get("input"),
        }

        try:
            await self.hooks.emit_before_message_composed(message, streaming_message_context)

            # Simplified message composition (attachments skip for now as per perform_send basic logic)
            final_content = message
            if not streaming_message_context.get("input"):
                streaming_message_context["input"] = {
                    "type": "input:text",
                    "data": {"text": message}
                }

            if is_stale_generation():
                return

            session_messages = self.chat_session.get_session_messages(session_id)
            session_messages.append(ChatHistoryItem(
                role="user",
                content=final_content,
                createdAt=user_msg_created_at,
                id=user_msg_id
            ))

            categorizer = StreamingCategorizer()
            stream_position = [0] # Use list for mutability in closure

            async def on_literal(literal: str):
                if is_stale_generation():
                    return

                categorizer.consume(literal)
                speech_only = categorizer.filter_to_speech(literal, stream_position[0])
                stream_position[0] += len(literal)

                if speech_only:
                    building_message.content += speech_only
                    await self.hooks.emit_token_literal(speech_only, streaming_message_context)

                    if building_message.slices and building_message.slices[-1].type == "text":
                        building_message.slices[-1].text += speech_only
                    else:
                        building_message.slices.append(ChatSlice(type="text", text=speech_only))

                    self.chat_stream.streaming_message = building_message

            async def on_special(special: str):
                if is_stale_generation():
                    return
                await self.hooks.emit_token_special(special, streaming_message_context)

            async def on_end(full_text: str):
                if is_stale_generation():
                    return

                final_cat = categorize_response(full_text)
                building_message.metadata = {
                    "categorization": {
                        "speech": final_cat.speech,
                        "reasoning": final_cat.reasoning
                    }
                }
                self.chat_stream.streaming_message = building_message

            parser = LLMMarkerParser(on_literal=on_literal, on_special=on_special, on_end=on_end)

            # Build new messages with context snapshot
            new_messages = []
            for msg in session_messages:
                new_messages.append({"role": msg.role, "content": msg.content})

            contexts_snapshot = self.chat_context.get_contexts_snapshot()
            if contexts_snapshot:
                system_msg = new_messages[:1]
                after_system = new_messages[1:]

                context_text = "These are the contextual information retrieved or on-demand updated from other modules:\n"
                for key, value in contexts_snapshot.items():
                    context_text += f"Module {key}: {json.dumps(value)}\n"

                new_messages = system_msg + [{"role": "user", "content": context_text}] + after_system

            streaming_message_context["composedMessage"] = new_messages

            await self.hooks.emit_after_message_composed(message, streaming_message_context)
            await self.hooks.emit_before_send(message, streaming_message_context)

            if is_stale_generation():
                return

            full_text = [""]

            async def handle_delta(delta: str):
                full_text[0] += delta
                await parser.consume(delta)

            # Final LLM call
            await self.llm.stream_chat(
                model=options.get("model", "gpt-4o"),
                messages=new_messages,
                on_delta=handle_delta,
                tools=options.get("tools")
            )

            await parser.end()

            if not is_stale_generation():
                if building_message.slices:
                    session_messages.append(ChatHistoryItem(
                        role="assistant",
                        content=building_message.content,
                        id=generate(),
                        createdAt=time.time()
                    ))

                await self.hooks.emit_stream_end(streaming_message_context)
                await self.hooks.emit_assistant_response_end(full_text[0], streaming_message_context)
                await self.hooks.emit_after_send(message, streaming_message_context)
                await self.hooks.emit_assistant_message(building_message.dict(), full_text[0], streaming_message_context)

                await self.hooks.emit_chat_turn_complete({
                    "output": building_message.dict(),
                    "outputText": full_text[0],
                    "toolCalls": [] # Placeholder
                }, streaming_message_context)

            await self.chat_stream.finalize_stream(full_text[0])

        finally:
            self.sending = False

    async def cancel_pending_sends(self, session_id: str = None):
        for s in self.pending_queued_sends:
            if session_id and s.session_id != session_id:
                continue
            s.cancelled = True
            if s.future:
                s.future.set_exception(RuntimeError("Cancelled"))

        if session_id:
            self.pending_queued_sends = [s for s in self.pending_queued_sends if s.session_id != session_id]
        else:
            self.pending_queued_sends = []
        logger.info(f"Cancelled pending sends for session: {session_id or 'all'}")
