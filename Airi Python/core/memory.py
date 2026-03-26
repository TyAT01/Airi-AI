import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import time
from nanoid import generate

logger = logging.getLogger("airi_memory")

class MemoryEntry(BaseModel):
    id: str = generate()
    content: str
    vector: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: float = time.time()

class MemorySystem:
    def __init__(self):
        self.memories: List[MemoryEntry] = []

    async def store(self, content: str, metadata: Dict[str, Any] = None):
        logger.info(f"Storing memory: {content[:50]}...")
        entry = MemoryEntry(content=content, metadata=metadata)
        self.memories.append(entry)
        return entry

    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        logger.info(f"Searching memory for: {query}")
        # Basic keyword search as a fallback for vector search
        results = [m for m in self.memories if query.lower() in m.content.lower()]
        return results[:limit]

    async def get_relevant_context(self, query: str) -> str:
        results = await self.search(query)
        if not results:
            return ""
        return "\n".join([f"- {m.content}" for m in results])
