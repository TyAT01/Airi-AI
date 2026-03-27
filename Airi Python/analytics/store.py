import time
import logging
from typing import Dict, Any, Optional
from analytics.posthog import (
    is_posthog_available_in_build,
    sync_posthog_capture,
    register_posthog_build_info
)

logger = logging.getLogger(__name__)

class SharedAnalyticsStore:
    def __init__(self, settings_analytics=None, build_info: Optional[Dict[str, Any]] = None):
        self.settings_analytics = settings_analytics
        self.build_info = build_info or {
            "version": "0.1.0",
            "commit": "dev",
            "branch": "main",
            "builtOn": time.time()
        }
        self.is_initialized = False
        self.app_start_time: Optional[float] = None
        self.first_message_tracked = False

    def on_analytics_enabled_changed(self, enabled: bool):
        if not self.is_initialized:
            return

        should_capture = sync_posthog_capture(enabled)
        if should_capture:
            # When analytics is enabled mid-session, invalidate app_start_time and
            # mark first message as already tracked to avoid backfilling a stale
            # event with a misleading duration or timing.
            if not self.first_message_tracked:
                self.app_start_time = None
                self.mark_first_message_tracked()

            register_posthog_build_info(self.build_info)

    def initialize(self):
        if self.is_initialized:
            return

        self.app_start_time = time.time()

        if is_posthog_available_in_build():
            # Assume enabled if settings_analytics is not available
            enabled = self.settings_analytics.analytics_enabled if self.settings_analytics else True
            should_capture = sync_posthog_capture(enabled)
            if should_capture:
                register_posthog_build_info(self.build_info)

        self.is_initialized = True
        logger.info("Analytics store initialized")

    def mark_first_message_tracked(self):
        self.first_message_tracked = True
        logger.info("First message tracked marked in analytics")

    @property
    def analytics_enabled(self) -> bool:
        return self.settings_analytics.analytics_enabled if self.settings_analytics else False
