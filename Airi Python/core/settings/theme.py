import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_THEME_COLORS_HUE = 220.44

class ThemeSettings:
    def __init__(self):
        self.theme_colors_hue: float = DEFAULT_THEME_COLORS_HUE
        self.theme_colors_hue_dynamic: bool = False

    def set_theme_colors_hue(self, hue: float = DEFAULT_THEME_COLORS_HUE):
        self.theme_colors_hue = hue
        self.theme_colors_hue_dynamic = False
        logger.info(f"Theme hue set to {hue}")

    def apply_primary_color_from(self, color: Optional[str] = None):
        # In Python, we might need a library to convert color to hue
        # Placeholder logic
        self.set_theme_colors_hue(DEFAULT_THEME_COLORS_HUE)

    def is_color_selected_for_primary(self, hex_color: Optional[str] = None) -> bool:
        if self.theme_colors_hue_dynamic:
            return False
        # Simplified comparison
        return True

    def reset_state(self):
        self.theme_colors_hue = DEFAULT_THEME_COLORS_HUE
        self.theme_colors_hue_dynamic = False
        logger.info("Theme settings reset")
