import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_characters")

class CharacterCapability(BaseModel):
    id: str = Field(default_factory=generate)
    character_id: str = Field(..., alias="characterId")
    type: str
    config: Dict[str, Any] = {}

class CharacterAvatarModel(BaseModel):
    id: str = Field(default_factory=generate)
    character_id: str = Field(..., alias="characterId")
    name: str
    type: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}

class CharacterPrompt(BaseModel):
    id: str = Field(default_factory=generate)
    character_id: str = Field(..., alias="characterId")
    language: str
    type: str
    content: str

class Character(BaseModel):
    id: str = Field(default_factory=generate)
    version: str = "1.0.0"
    character_id: str = Field(..., alias="characterId")
    creator_id: str = Field(..., alias="creatorId")
    owner_id: str = Field(..., alias="ownerId")
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    updated_at: float = Field(default_factory=time.time, alias="updatedAt")
    capabilities: List[CharacterCapability] = []
    avatar_models: List[CharacterAvatarModel] = Field([], alias="avatarModels")
    prompts: List[CharacterPrompt] = []

class CharacterManager:
    """
    Manages characters and their relations.
    Mimics packages/stage-ui/src/stores/characters.ts.
    """
    def __init__(self):
        self.characters: Dict[str, Character] = {}

    def add_character(self, character: Character):
        self.characters[character.id] = character
        logger.info(f"Character {character.character_id} added.")

    def get_character(self, character_id: str) -> Optional[Character]:
        return self.characters.get(character_id)

    def list_characters(self) -> List[Character]:
        return list(self.characters.values())

    def update_character(self, character_id: str, updates: Dict[str, Any]):
        if character_id in self.characters:
            char_dict = self.characters[character_id].dict()
            char_dict.update(updates)
            char_dict["updatedAt"] = time.time()
            self.characters[character_id] = Character(**char_dict)
            logger.info(f"Character {character_id} updated.")
