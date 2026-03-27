import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class VisionAgentConfig(BaseModel):
    id: str
    name: str
    description: str

VISION_AGENTS: List[VisionAgentConfig] = []
