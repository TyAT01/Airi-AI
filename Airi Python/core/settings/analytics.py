import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AnalyticsSettings:
    def __init__(self):
        self.analytics_enabled: bool = True

    def reset_state(self):
        self.analytics_enabled = True
        logger.info("Analytics settings reset")
