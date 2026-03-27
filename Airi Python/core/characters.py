import logging
import time
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

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
    character_id: Optional[str] = Field(None, alias="characterId")
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
    cover_url: Optional[str] = Field(None, alias="coverUrl")

    class Config:
        populate_by_name = True

def build_local_character(user_id: str, payload: Dict[str, Any]) -> Character:
    char_id = payload.get("character", {}).get("id") or generate()
    now = time.time()

    character_data = payload.get("character", {})

    return Character(
        id=char_id,
        version=character_data.get("version", "1.0.0"),
        coverUrl=character_data.get("coverUrl"),
        creatorId=user_id,
        ownerId=user_id,
        characterId=character_data.get("characterId"),
        createdAt=now,
        updatedAt=now,
        capabilities=[
            CharacterCapability(
                id=generate(),
                characterId=char_id,
                type=c["type"],
                config=c.get("config", {})
            ) for c in payload.get("capabilities", [])
        ],
        avatarModels=[
            CharacterAvatarModel(
                id=generate(),
                characterId=char_id,
                name=m["name"],
                type=m["type"],
                description=m.get("description"),
                config=m.get("config", {}),
                createdAt=now,
                updatedAt=now
            ) for m in payload.get("avatarModels", [])
        ],
        i18n=[
            CharacterI18n(
                id=generate(),
                characterId=char_id,
                language=item["language"],
                name=item["name"],
                description=item.get("description"),
                tags=item.get("tags", []),
                createdAt=now,
                updatedAt=now
            ) for item in payload.get("i18n", [])
        ],
        prompts=[
            CharacterPrompt(
                id=generate(),
                characterId=char_id,
                language=p["language"],
                type=p["type"],
                content=p["content"]
            ) for p in payload.get("prompts", [])
        ]
    )

class CharactersStore:
    def __init__(self, auth_store=None):
        self.characters: Dict[str, Character] = {}
        self.auth = auth_store

    async def fetch_list(self, all_chars: bool = False):
        logger.info(f"Fetching character list (all={all_chars})")
        # In actual implementation, this would fetch from a database or remote API.
        # For now, it returns the local cache.
        return list(self.characters.values())

    async def fetch_by_id(self, char_id: str) -> Optional[Character]:
        logger.info(f"Fetching character by id: {char_id}")
        return self.characters.get(char_id)

    async def create(self, payload: Dict[str, Any]) -> Character:
        user_id = self.auth.user_id if self.auth else "default"
        character = build_local_character(user_id, payload)
        self.characters[character.id] = character
        logger.info(f"Character {character.id} created.")
        return character

    async def update(self, char_id: str, payload: Dict[str, Any]) -> Optional[Character]:
        character = self.characters.get(char_id)
        if not character:
            return None

        char_data = character.dict(by_alias=True)
        # Update character fields from payload
        if "version" in payload:
            char_data["version"] = payload["version"]
        if "coverUrl" in payload:
            char_data["coverUrl"] = payload["coverUrl"]
        if "characterId" in payload:
            char_data["characterId"] = payload["characterId"]

        char_data["updatedAt"] = time.time()
        updated_character = Character(**char_data)
        self.characters[char_id] = updated_character
        logger.info(f"Character {char_id} updated.")
        return updated_character

    async def remove(self, char_id: str):
        if char_id in self.characters:
            del self.characters[char_id]
            logger.info(f"Character {char_id} removed.")

    async def like(self, char_id: str):
        character = self.characters.get(char_id)
        if character:
            character.likes_count += 1
            character.updated_at = time.time()
            logger.info(f"Character {char_id} liked.")

    async def bookmark(self, char_id: str):
        character = self.characters.get(char_id)
        if character:
            character.bookmarks_count += 1
            character.updated_at = time.time()
            logger.info(f"Character {char_id} bookmarked.")

    def get_character(self, char_id: str) -> Optional[Character]:
        return self.characters.get(char_id)
