import logging
from typing import Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ControlsIslandSettings(BaseModel):
    """
    Manages control island UI settings.
    Mimics packages/stage-ui/src/stores/settings/controls-island.ts.
    """
    allow_visible_on_all_workspaces: bool = Field(True, alias="allowVisibleOnAllWorkspaces")
    always_on_top: bool = Field(True, alias="alwaysOnTop")
    controls_island_icon_size: Literal['auto', 'large', 'small'] = Field('auto', alias="controlsIslandIconSize")

    model_config = {
        "populate_by_name": True
    }

    def reset_state(self):
        self.allow_visible_on_all_workspaces = True
        self.always_on_top = True
        self.controls_island_icon_size = 'auto'
        logger.info("Controls island settings reset")
