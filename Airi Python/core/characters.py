import logging
import time
from typing import List, Dict, Any, Optional, Union
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
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    updated_at: float = Field(default_factory=time.time, alias="updatedAt")

class CharacterPrompt(BaseModel):
    id: str = Field(default_factory=generate)
    character_id: str = Field(..., alias="characterId")
    language: str
    type: str
    content: str

class CharacterI18n(BaseModel):
    id: str = Field(default_factory=generate)
    character_id: str = Field(..., alias="characterId")
    language: str
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    updated_at: float = Field(default_factory=time.time, alias="updatedAt")

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
    i18n: List[CharacterI18n] = []
    likes_count: int = Field(0, alias="likesCount")
    bookmarks_count: int = Field(0, alias="bookmarksCount")

class CharacterManager:
    """
    Manages characters and their relations.
    Mimics packages/stage-ui/src/stores/characters.ts.
    """
    def __init__(self):
        self.characters: Dict[str, Character] = {}

    async def fetch_list(self, all_chars: bool = False):
        logger.info(f"Fetching character list (all={all_chars})")
        # In Python, this would call the API or database
        return list(self.characters.values())

    async def fetch_by_id(self, char_id: str) -> Optional[Character]:
        logger.info(f"Fetching character by id: {char_id}")
        return self.characters.get(char_id)

    def add_character(self, character: Character):
        self.characters[character.id] = character
        logger.info(f"Character {character.character_id} added.")

    async def update_character(self, character_id: str, updates: Dict[str, Any]):
        if character_id in self.characters:
            char_data = self.characters[character_id].dict(by_alias=True)
            char_data.update(updates)
            char_data["updatedAt"] = time.time()
            self.characters[character_id] = Character(**char_data)
            logger.info(f"Character {character_id} updated.")

    async def remove_character(self, character_id: str):
        if character_id in self.characters:
            del self.characters[character_id]
            logger.info(f"Character {character_id} removed.")
