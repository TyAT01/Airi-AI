import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from nanoid import generate

class CharacterReaction(BaseModel):
    id: str = Field(default_factory=generate)
    message: str
    created_at: float = Field(default_factory=time.time)
    source_event_id: Optional[str] = Field(None, alias="sourceEventId")
    metadata: Optional[Dict[str, Any]] = None

class CharacterState:
    def __init__(self, name: str = "Airi"):
        self.name = name
        self.reactions: List[CharacterReaction] = []
        self.system_prompt: str = f"You are {name}, a helpful AI companion."
        self.max_reactions = 200

    def record_reaction(self, message: str, source_event_id: str = None, metadata: Dict[str, Any] = None) -> CharacterReaction:
        reaction = CharacterReaction(message=message, sourceEventId=source_event_id, metadata=metadata)
        self.reactions.append(reaction)
        if len(self.reactions) > self.max_reactions:
            self.reactions.pop(0)
        return reaction

    def on_spark_notify_reaction_stream_event(self, spark_event_id: str, chunk: str, metadata: Dict[str, Any] = None):
        # In Python we can just update the reaction directly or handle streaming state
        # Find if there is an existing reaction for this event
        existing = next((r for r in self.reactions if r.source_event_id == spark_event_id), None)
        if existing:
            existing.message += chunk
        else:
            self.record_reaction(message=chunk, source_event_id=spark_event_id, metadata=metadata)

    def on_spark_notify_reaction_stream_end(self, spark_event_id: str, full_text: str, metadata: Dict[str, Any] = None):
        existing = next((r for r in self.reactions if r.source_event_id == spark_event_id), None)
        if existing:
            existing.message = full_text
            if metadata:
                existing.metadata = metadata
        else:
            self.record_reaction(message=full_text, source_event_id=spark_event_id, metadata=metadata)

    def clear_reactions(self):
        self.reactions = []

    def update_system_prompt(self, prompt: str):
        self.system_prompt = prompt
