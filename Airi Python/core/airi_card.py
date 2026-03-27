import logging
import time
import os
import json
from typing import Dict, Any, Optional, List, Union, Literal
from pydantic import BaseModel, Field
from nanoid import generate

from core.settings.stage_model import StageModelSettings
from core.consciousness import ConsciousnessStore
from expression.speech import SpeechStore

logger = logging.getLogger(__name__)

class AiriExtensionModules(BaseModel):
    consciousness: Dict[str, str] = Field(default_factory=lambda: {"provider": "", "model": ""})
    speech: Dict[str, Any] = Field(default_factory=lambda: {"provider": "", "model": "", "voice_id": ""})
    vrm: Optional[Dict[str, str]] = None
    live2d: Optional[Dict[str, str]] = None
    display_model_id: Optional[str] = Field(None, alias="displayModelId")

    class Config:
        populate_by_name = True

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

    class Config:
        populate_by_name = True

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
        stage_model_settings: StageModelSettings,
        persistence_file: str = "settings/airi_cards.json"
    ):
        self.consciousness_store = consciousness_store
        self.speech_store = speech_store
        self.stage_model_settings = stage_model_settings
        self.persistence_file = persistence_file

        self.cards: Dict[str, AiriCard] = {}
        self.active_card_id: str = "default"

        self._load_from_persistence()
        self._initialize_default()

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    self.active_card_id = data.get("active_card_id", "default")
                    cards_data = data.get("cards", {})
                    for cid, cdata in cards_data.items():
                        self.cards[cid] = AiriCard(**cdata)
                logger.info(f"Loaded {len(self.cards)} Airi cards.")
            except Exception as e:
                logger.error(f"Failed to load Airi cards persistence: {e}")

    def _save_to_persistence(self):
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        try:
            with open(self.persistence_file, "w") as f:
                data = {
                    "active_card_id": self.active_card_id,
                    "cards": {cid: card.dict(by_alias=True) for cid, card in self.cards.items()}
                }
                json.dump(data, f, indent=2)
            logger.info("Saved Airi cards.")
        except Exception as e:
            logger.error(f"Failed to save Airi cards persistence: {e}")

    def _initialize_default(self):
        if "default" not in self.cards:
            self.cards["default"] = self.new_airi_card({
                "name": "ReLU",
                "description": "Default character prompt and personality."
            })
            self._save_to_persistence()

    @property
    def active_card(self) -> Optional[AiriCard]:
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
            "displayModelId": self.stage_model_settings.stage_model_selected,
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

    def new_airi_card(self, card_data: Dict[str, Any]) -> AiriCard:
        # Simplified version of newAiriCard from TS
        extension = self.resolve_airi_extension(card_data)
        if "extensions" not in card_data:
            card_data["extensions"] = {}
        card_data["extensions"]["airi"] = extension.dict(by_alias=True)
        return AiriCard(**card_data)

    def add_card(self, card_data: Dict[str, Any]) -> str:
        card_id = generate()
        self.cards[card_id] = self.new_airi_card(card_data)
        self._save_to_persistence()
        return card_id

    def remove_card(self, card_id: str):
        if card_id in self.cards:
            del self.cards[card_id]
            self._save_to_persistence()

    def update_card(self, card_id: str, updates: Dict[str, Any]) -> bool:
        if card_id not in self.cards:
            return False

        existing = self.cards[card_id].dict(by_alias=True)
        existing.update(updates)
        self.cards[card_id] = self.new_airi_card(existing)
        self._save_to_persistence()
        return True

    def get_card(self, card_id: str) -> Optional[AiriCard]:
        return self.cards.get(card_id)

    async def set_active_card(self, card_id: str):
        if card_id in self.cards:
            self.active_card_id = card_id
            await self._apply_card_extension(self.cards[card_id])
            self._save_to_persistence()

    async def _apply_card_extension(self, card: AiriCard):
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
            self.stage_model_settings.stage_model_selected = ext.modules.display_model_id
            await self.stage_model_settings.update_stage_model()

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
            "displayModelId": self.stage_model_settings.stage_model_selected,
        }

    @property
    def system_prompt(self) -> str:
        card = self.active_card
        if not card:
            return ""

        prompts = [card.system_prompt, card.description, card.personality]
        return "\n".join([p for p in prompts if p])
