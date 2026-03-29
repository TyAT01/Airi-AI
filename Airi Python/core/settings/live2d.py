import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Live2dSettings(BaseModel):
    """
    Manages Live2D display settings.
    Mimics packages/stage-ui/src/stores/settings/live2d.ts.
    """
    live2d_disable_focus: bool = Field(False, alias="live2dDisableFocus")
    live2d_idle_animation_enabled: bool = Field(True, alias="live2dIdleAnimationEnabled")
    live2d_auto_blink_enabled: bool = Field(True, alias="live2dAutoBlinkEnabled")
    live2d_force_auto_blink_enabled: bool = Field(False, alias="live2dForceAutoBlinkEnabled")
    live2d_shadow_enabled: bool = Field(True, alias="live2dShadowEnabled")
    live2d_max_fps: int = Field(0, alias="live2dMaxFps")

    model_config = {
        "populate_by_name": True
    }

    def reset_state(self):
        self.live2d_disable_focus = False
        self.live2d_idle_animation_enabled = True
        self.live2d_auto_blink_enabled = True
        self.live2d_force_auto_blink_enabled = False
        self.live2d_shadow_enabled = True
        self.live2d_max_fps = 0
        logger.info("Live2D settings reset")
