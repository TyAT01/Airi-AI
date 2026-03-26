import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger("airi_memory")

class MemoryEntry(BaseModel):
    id: str = Field(default_factory=generate)
    content: str
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: float = Field(default_factory=time.time)

class MemorySystem:
    def __init__(self, embedding_client=None):
        self.memories: List[MemoryEntry] = []
        self.embedding_client = embedding_client

    async def store(self, content: str, metadata: Dict[str, Any] = None):
        vector = None
        if self.embedding_client:
            try:
                vector = await self.embedding_client.create_embedding(content)
            except Exception as e:
                logger.error(f"Embedding error: {e}")

        entry = MemoryEntry(content=content, vector=vector, metadata=metadata)
        self.memories.append(entry)
        logger.info(f"Stored memory: {content[:50]}...")
        return entry

    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        if not self.memories:
            return []

        if self.embedding_client:
            query_vector = await self.embedding_client.create_embedding(query)
            # Simple cosine similarity would go here if we had vectors
            # For now, fallback to keyword
            pass

        results = [m for m in self.memories if query.lower() in m.content.lower()]
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    async def get_relevant_context(self, query: str) -> str:
        results = await self.search(query)
        if not results:
            return ""
        context_parts = []
        for m in results:
            context_parts.append(f"[{time.ctime(m.created_at)}] {m.content}")
        return "\n".join(context_parts)

class EmbeddingClient:
    # Placeholder for actual embedding logic (OpenAI, etc.)
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def create_embedding(self, text: str) -> List[float]:
        # Return dummy vector
        return [0.1] * 1536
