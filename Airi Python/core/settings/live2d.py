import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class Live2dSettings:
    def __init__(self):
        self.live2d_disable_focus: bool = False
        self.live2d_idle_animation_enabled: bool = True
        self.live2d_auto_blink_enabled: bool = True
        self.live2d_force_auto_blink_enabled: bool = False
        self.live2d_shadow_enabled: bool = True
        self.live2d_max_fps: int = 0

    def reset_state(self):
        self.live2d_disable_focus = False
        self.live2d_idle_animation_enabled = True
        self.live2d_auto_blink_enabled = True
        self.live2d_force_auto_blink_enabled = False
        self.live2d_shadow_enabled = True
        self.live2d_max_fps = 0
        logger.info("Live2D settings reset")
