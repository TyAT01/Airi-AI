import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_live2d")

class Live2dModelConfig(BaseModel):
    model_id: str = Field(..., alias="modelId")
    motion_groups: List[str] = Field([], alias="motionGroups")
    expressions: List[str] = []
    metadata: Dict[str, Any] = {}

class Live2dState(BaseModel):
    is_loaded: bool = Field(False, alias="isLoaded")
    is_rendering: bool = Field(False, alias="isRendering")
    model_id: Optional[str] = Field(None, alias="modelId")
    motion_group: Optional[str] = Field(None, alias="motionGroup")
    expression: Optional[str] = None
    mouth_open_size: float = Field(0.0, alias="mouthOpenSize")

class Live2dStore:
    def __init__(self):
        self.state = Live2dState()

    async def load_model(self, model_id: str):
        logger.info(f"Loading Live2D model: {model_id}")
        self.state.model_id = model_id
        self.state.is_loaded = True

    async def play_motion(self, group: str):
        logger.info(f"Playing Live2D motion group: {group}")
        self.state.motion_group = group

    async def set_expression(self, expression: str):
        logger.info(f"Setting Live2D expression: {expression}")
        self.state.expression = expression

    async def update_mouth(self, size: float):
        self.state.mouth_open_size = size
