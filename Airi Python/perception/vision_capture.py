import logging
from typing import Optional, Any
try:
    import pyautogui
    from PIL import Image
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

logger = logging.getLogger(__name__)

class ScreenCapture:
    def __init__(self):
        self.enabled = HAS_LIBS
        if not HAS_LIBS:
            logger.warning("pyautogui or PIL not found. Screen capture disabled.")

    def capture(self) -> Optional[Any]:
        if not self.enabled:
            return None

        try:
            screenshot = pyautogui.screenshot()
            logger.debug("Screen captured.")
            return screenshot
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return None

    def save_capture(self, path: str):
        screenshot = self.capture()
        if screenshot:
            screenshot.save(path)
            logger.info(f"Screenshot saved to {path}")
