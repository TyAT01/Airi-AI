import logging
import time
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from nanoid import generate

from core.settings.stage_model import StageModelStore
from core.consciousness import ConsciousnessStore
from expression.speech import SpeechStore

logger = logging.getLogger("airi_card_store")

class AiriExtensionModules(BaseModel):
    consciousness: Dict[str, str] = Field(default_factory=lambda: {"provider": "", "model": ""})
    speech: Dict[str, Any] = Field(default_factory=lambda: {"provider": "", "model": "", "voice_id": ""})
    vrm: Optional[Dict[str, str]] = None
    live2d: Optional[Dict[str, str]] = None
    display_model_id: Optional[str] = Field(None, alias="displayModelId")

class AiriExtension(BaseModel):
    modules: AiriExtensionModules
    agents: Dict[str, Any] = Field(default_factory=dict)

class AiriCard(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    creator: str = ""
    notes: str = ""
    personality: str = ""
    scenario: str = ""
    system_prompt: str = Field("", alias="systemPrompt")
    greetings: List[str] = []
    tags: List[str] = []
    extensions: Dict[str, Any] = Field(default_factory=dict)

    @property
    def airi_extension(self) -> Optional[AiriExtension]:
        if "airi" in self.extensions:
            try:
                return AiriExtension(**self.extensions["airi"])
            except Exception:
                return None
        return None

class AiriCardStore:
    def __init__(
        self,
        consciousness_store: ConsciousnessStore,
        speech_store: SpeechStore,
        stage_model_store: StageModelStore
    ):
        self.consciousness_store = consciousness_store
        self.speech_store = speech_store
        self.stage_model_store = stage_model_store

        self.cards: Dict[str, AiriCard] = {}
        self.active_card_id: str = "default"
        self._initialize_default()

    def _initialize_default(self):
        self.cards["default"] = AiriCard(
            name="ReLU",
            description="Default character prompt and personality."
        )

    def get_active_card(self) -> Optional[AiriCard]:
        return self.cards.get(self.active_card_id)

    def resolve_airi_extension(self, card_data: Dict[str, Any]) -> AiriExtension:
        # Get existing extension if available
        existing_extension = card_data.get("extensions", {}).get("airi", {})

        # Create default modules config
        default_modules = {
            "consciousness": {
                "provider": self.consciousness_store.active_provider,
                "model": self.consciousness_store.active_model,
            },
            "speech": {
                "provider": self.speech_store.active_provider,
                "model": self.speech_store.active_model,
                "voice_id": self.speech_store.active_voice_id,
            },
            "displayModelId": self.stage_model_store.stage_model_selected,
        }

        # Merge existing extension with defaults
        modules = existing_extension.get("modules", {})
        merged_modules = {
            "consciousness": {
                "provider": modules.get("consciousness", {}).get("provider") or default_modules["consciousness"]["provider"],
                "model": modules.get("consciousness", {}).get("model") or default_modules["consciousness"]["model"],
            },
            "speech": {
                "provider": modules.get("speech", {}).get("provider") or default_modules["speech"]["provider"],
                "model": modules.get("speech", {}).get("model") or default_modules["speech"]["model"],
                "voice_id": modules.get("speech", {}).get("voice_id") or default_modules["speech"]["voice_id"],
                "pitch": modules.get("speech", {}).get("pitch"),
                "rate": modules.get("speech", {}).get("rate"),
                "ssml": modules.get("speech", {}).get("ssml"),
                "language": modules.get("speech", {}).get("language"),
            },
            "vrm": modules.get("vrm"),
            "live2d": modules.get("live2d"),
            "displayModelId": modules.get("displayModelId") or default_modules["displayModelId"],
        }

        return AiriExtension(
            modules=AiriExtensionModules(**merged_modules),
            agents=existing_extension.get("agents", {})
        )

    def add_card(self, card_data: Dict[str, Any]) -> str:
        card_id = generate()

        # Ensure airi extension is resolved/merged
        extension = self.resolve_airi_extension(card_data)
        if "extensions" not in card_data:
            card_data["extensions"] = {}
        card_data["extensions"]["airi"] = extension.dict(by_alias=True)

        card = AiriCard(**card_data)
        self.cards[card_id] = card
        return card_id

    def remove_card(self, card_id: str):
        if card_id in self.cards:
            del self.cards[card_id]

    def update_card(self, card_id: str, updates: Dict[str, Any]) -> bool:
        if card_id not in self.cards:
            return False

        existing = self.cards[card_id].dict(by_alias=True)
        existing.update(updates)
        self.cards[card_id] = AiriCard(**existing)
        return True

    def get_card(self, card_id: str) -> Optional[AiriCard]:
        return self.cards.get(card_id)

    def set_active_card(self, card_id: str):
        if card_id in self.cards:
            self.active_card_id = card_id
            self._apply_card_extension(self.cards[card_id])

    def _apply_card_extension(self, card: AiriCard):
        ext = card.airi_extension
        if not ext:
            return

        if ext.modules.consciousness:
            self.consciousness_store.active_provider = ext.modules.consciousness.get("provider", "")
            self.consciousness_store.active_model = ext.modules.consciousness.get("model", "")

        if ext.modules.speech:
            self.speech_store.active_provider = ext.modules.speech.get("provider", "")
            self.speech_store.active_model = ext.modules.speech.get("model", "")
            self.speech_store.active_voice_id = ext.modules.speech.get("voice_id", "")

        if ext.modules.display_model_id:
            self.stage_model_store.stage_model_selected = ext.modules.display_model_id

    @property
    def current_models(self) -> Dict[str, Any]:
        return {
            "consciousness": {
                "provider": self.consciousness_store.active_provider,
                "model": self.consciousness_store.active_model,
            },
            "speech": {
                "provider": self.speech_store.active_provider,
                "model": self.speech_store.active_model,
                "voice_id": self.speech_store.active_voice_id,
            },
            "displayModelId": self.stage_model_store.stage_model_selected,
        }

    @property
    def system_prompt(self) -> str:
        card = self.get_active_card()
        if not card:
            return ""

        prompts = [card.system_prompt, card.description, card.personality]
        return "\n".join([p for p in prompts if p])
