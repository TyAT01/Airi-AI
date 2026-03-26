import logging
from typing import Literal
from pydantic import BaseModel

logger = logging.getLogger("airi_settings_controls_island")

class ControlsIslandSettings:
    def __init__(self):
        self.allow_visible_on_all_workspaces: bool = True
        self.always_on_top: bool = True
        self.controls_island_icon_size: Literal['auto', 'large', 'small'] = 'auto'

    def reset_state(self):
        self.allow_visible_on_all_workspaces = True
        self.always_on_top = True
        self.controls_island_icon_size = 'auto'
        logger.info("Controls island settings reset")
