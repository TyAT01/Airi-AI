import logging
from typing import Dict, Any, Optional, List, Set, Callable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PARAMETERS = {
    "angleX": 0,
    "angleY": 0,
    "angleZ": 0,
    "leftEyeOpen": 1,
    "rightEyeOpen": 1,
    "leftEyeSmile": 0,
    "rightEyeSmile": 0,
    "leftEyebrowLR": 0,
    "rightEyebrowLR": 0,
    "leftEyebrowY": 0,
    "rightEyebrowY": 0,
    "leftEyebrowAngle": 0,
    "rightEyebrowAngle": 0,
    "leftEyebrowForm": 0,
    "rightEyebrowForm": 0,
    "mouthOpen": 0,
    "mouthForm": 0,
    "cheek": 0,
    "bodyAngleX": 0,
    "bodyAngleY": 0,
    "bodyAngleZ": 0,
    "breath": 0,
}

class Live2dStore:
    """
    Manages Live2D model state and parameters.
    Mirror of packages/stage-ui-live2d/src/stores/live2d.ts.
    """
    def __init__(self):
        # Settings state
        self.position = {"x": 0, "y": 0}
        self.current_motion = {"group": "Idle", "index": 0}
        self.available_motions: List[Dict[str, Any]] = []
        self.motion_map: Dict[str, str] = {}
        self.scale: float = 1.0
        self.model_parameters: Dict[str, float] = DEFAULT_MODEL_PARAMETERS.copy()

        # Hooks
        self._should_update_view_hooks: Set[Callable[[], None]] = set()

        # Legacy/Runtime state (kept for compatibility with existing Python code if any)
        self.is_loaded = False
        self.is_rendering = False
        self.model_id: Optional[str] = None
        self.motion_group: Optional[str] = None
        self.expression: Optional[str] = None
        self.mouth_open_size: float = 0.0

    @property
    def position_in_percentage_string(self) -> Dict[str, str]:
        return {
            "x": f"{self.position['x']}%",
            "y": f"{self.position['y']}%",
        }

    def on_should_update_view(self, hook: Callable[[], None]):
        self._should_update_view_hooks.add(hook)
        return lambda: self._should_update_view_hooks.remove(hook)

    def should_update_view(self):
        logger.info("Live2D should update view")
        for hook in self._should_update_view_hooks:
            try:
                hook()
            except Exception as e:
                logger.error(f"Error in Live2D update hook: {e}")

    def reset_state(self):
        self.position = {"x": 0, "y": 0}
        self.current_motion = {"group": "Idle", "index": 0}
        self.available_motions = []
        self.motion_map = {}
        self.scale = 1.0
        self.model_parameters = DEFAULT_MODEL_PARAMETERS.copy()

        # Legacy/Runtime state reset
        self.is_loaded = False
        self.is_rendering = False
        self.model_id = None
        self.motion_group = None
        self.expression = None
        self.mouth_open_size = 0.0

        self.should_update_view()
        logger.info("Live2D store reset")

    # Actions from previous version
    async def load_model(self, model_id: str):
        logger.info(f"Loading Live2D model: {model_id}")
        self.model_id = model_id
        self.is_loaded = True
        self.should_update_view()

    async def play_motion(self, group: str, index: int = 0):
        logger.info(f"Playing Live2D motion group: {group}, index: {index}")
        self.motion_group = group
        self.current_motion = {"group": group, "index": index}
        self.should_update_view()

    async def set_expression(self, expression: str):
        logger.info(f"Setting Live2D expression: {expression}")
        self.expression = expression
        self.should_update_view()

    async def update_mouth(self, size: float):
        self.mouth_open_size = size
        # We don't necessarily trigger should_update_view for every mouth update to avoid spam
