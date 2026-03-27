import time
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

class CharacterReaction(BaseModel):
    id: str = Field(default_factory=generate)
    message: str
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    source_event_id: Optional[str] = Field(None, alias="sourceEventId")
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True

class StreamingReactionState(BaseModel):
    reaction: CharacterReaction
    intent: Any # Should be an IntentHandle equivalent
    # parser: Any # LLMMarkerParser equivalent

    class Config:
        arbitrary_types_allowed = True

class CharacterState:
    """
    Manages the state and reactions of a character.
    Mimics packages/stage-ui/src/stores/character/index.ts.
    """
    def __init__(self, name: str = "Airi", speech_runtime_store=None):
        self.name = name
        self.reactions: List[CharacterReaction] = []
        self.streaming_reactions: Dict[str, StreamingReactionState] = {}
        self.system_prompt: str = f"You are {name}, a helpful AI companion."
        self.max_reactions = 200
        self.speech_runtime = speech_runtime_store

    @property
    def owner_id(self) -> str:
        return self.name or "default"

    def record_reaction(self, message: str, source_event_id: str = None, metadata: Dict[str, Any] = None) -> CharacterReaction:
        reaction = CharacterReaction(
            id=generate(),
            message=message,
            sourceEventId=source_event_id,
            metadata=metadata,
            createdAt=time.time()
        )
        self.reactions.append(reaction)
        if len(self.reactions) > self.max_reactions:
            self.reactions.pop(0)
        return reaction

    async def emit_text_output(self, text: str):
        """
        Emits text output via the speech runtime system.
        """
        if not self.speech_runtime:
            logger.warning("Speech runtime not available, cannot emit text output.")
            return

        intent = self.speech_runtime.open_intent(
            ownerId=self.owner_id,
            priority='normal',
            behavior='queue'
        )

        # In a full implementation, we'd use a parser here to stream tokens
        # For now, we write the full text.
        if hasattr(intent, 'write_literal'):
            intent.write_literal(text)
        elif hasattr(intent, 'writeLiteral'):
            intent.writeLiteral(text)

        if hasattr(intent, 'write_flush'):
            intent.write_flush()
            intent.end()
        elif hasattr(intent, 'writeFlush'):
            intent.writeFlush()
            intent.end()

    def on_spark_notify_reaction_stream_event(self, spark_event_id: str, chunk: str, metadata: Dict[str, Any] = None):
        if spark_event_id not in self.streaming_reactions:
            new_reaction = CharacterReaction(
                id=generate(),
                message='',
                sourceEventId=spark_event_id,
                metadata=metadata,
                createdAt=time.time()
            )

            intent = None
            if self.speech_runtime:
                intent = self.speech_runtime.open_intent(
                    intentId=f"spark:{spark_event_id}",
                    ownerId=self.owner_id,
                    priority='high',
                    behavior='interrupt'
                )

            self.streaming_reactions[spark_event_id] = StreamingReactionState(
                reaction=new_reaction,
                intent=intent
            )

        state = self.streaming_reactions[spark_event_id]
        state.reaction.message += chunk

        if state.intent:
            if hasattr(state.intent, 'write_literal'):
                state.intent.write_literal(chunk)
            elif hasattr(state.intent, 'writeLiteral'):
                state.intent.writeLiteral(chunk)

    def on_spark_notify_reaction_stream_end(self, spark_event_id: str, full_text: str, metadata: Dict[str, Any] = None):
        state = self.streaming_reactions.get(spark_event_id)
        if not state:
            # Fallback if stream event wasn't received
            self.record_reaction(message=full_text, source_event_id=spark_event_id, metadata=metadata)
            return

        state.reaction.message = full_text
        self.record_reaction(message=full_text, source_event_id=spark_event_id, metadata=metadata)

        if state.intent:
            if hasattr(state.intent, 'write_flush'):
                state.intent.write_flush()
                state.intent.end()
            elif hasattr(state.intent, 'writeFlush'):
                state.intent.writeFlush()
                state.intent.end()

        del self.streaming_reactions[spark_event_id]

    def clear_reactions(self):
        self.reactions = []

    def update_system_prompt(self, prompt: str):
        self.system_prompt = prompt
