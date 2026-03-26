from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class AiriExtensionModules(BaseModel):
    consciousness: Dict[str, str] = {"provider": "", "model": ""}
    speech: Dict[str, Any] = {"provider": "", "model": "", "voice_id": ""}
    display_model_id: Optional[str] = Field(None, alias="displayModelId")

class AiriCard(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    personality: str = ""
    scenario: str = ""
    system_prompt: str = Field("", alias="systemPrompt")
    greetings: List[str] = []
    tags: List[str] = []
    extensions: Dict[str, Any] = {}

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

    def add_card(self, card: AiriCard) -> str:
        import nanoid
        card_id = nanoid.generate()
        self.cards[card_id] = card
        return card_id

    def remove_card(self, card_id: str):
        if card_id in self.cards:
            del self.cards[card_id]

    def get_system_prompt(self) -> str:
        card = self.get_active_card()
        prompts = [card.system_prompt, card.description, card.personality]
        return "\n".join([p for p in prompts if p])

    @property
    def system_prompt(self) -> str:
        return self.get_system_prompt()
