from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class AiriCardModules(BaseModel):
    consciousness: Dict[str, str] = {"provider": "openai", "model": "gpt-4o"}
    speech: Dict[str, Any] = {"provider": "elevenlabs", "model": "eleven_multilingual_v2", "voice_id": "alloy"}
    display_model_id: Optional[str] = Field(None, alias="displayModelId")

class AiriCard(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    personality: str = ""
    system_prompt: str = Field("", alias="systemPrompt")
    modules: AiriCardModules = Field(default_factory=AiriCardModules)

class CharacterCardManager:
    def __init__(self):
        self.cards: Dict[str, AiriCard] = {}
        self.active_card_id: str = "default"
        self._initialize_default()

    def _initialize_default(self):
        self.cards["default"] = AiriCard(
            name="ReLU",
            description="Default character prompt and personality."
        )

    def get_active_card(self) -> AiriCard:
        return self.cards.get(self.active_card_id, self.cards["default"])

    def add_card(self, card_id: str, card: AiriCard):
        self.cards[card_id] = card

    def get_system_prompt(self) -> str:
        card = self.get_active_card()
        prompts = [card.system_prompt, card.description, card.personality]
        return "\n".join([p for p in prompts if p])
