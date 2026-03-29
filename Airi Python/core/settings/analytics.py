import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AnalyticsSettings(BaseModel):
    """
    Manages analytics settings.
    Mimics packages/stage-ui/src/stores/settings/analytics.ts.
    """
    analytics_enabled: bool = Field(True, alias="analyticsEnabled")

    model_config = {
        "populate_by_name": True
    }

    def reset_state(self):
        self.analytics_enabled = True
        logger.info("Analytics settings reset")
