import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_vision_agents")

class VisionAgentConfig(BaseModel):
    id: str
    name: str
    description: str

VISION_AGENTS: List[VisionAgentConfig] = []
