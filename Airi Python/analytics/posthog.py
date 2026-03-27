import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Simplified PostHog for Python port
class PostHogMock:
    def __init__(self):
        self.initialized = False
        self.opted_out = True
        self.build_info: Dict[str, Any] = {}

    def init(self, project_key: str, config: Dict[str, Any]):
        logger.info(f"PostHog initialized with key: {project_key[:5]}...")
        self.initialized = True
        self.opted_out = config.get("opt_out_capturing_by_default", True)

    def opt_in_capturing(self):
        self.opted_out = False
        logger.info("PostHog opted in")

    def opt_out_capturing(self):
        self.opted_out = True
        logger.info("PostHog opted out")

    def has_opted_out_capturing(self) -> bool:
        return self.opted_out

    def register(self, properties: Dict[str, Any]):
        self.build_info.update(properties)
        logger.info(f"PostHog registered build info: {properties}")

    def capture(self, event: str, properties: Optional[Dict[str, Any]] = None):
        if not self.initialized or self.opted_out:
            return
        logger.info(f"PostHog captured event '{event}' with props: {properties}")

posthog = PostHogMock()

def is_posthog_available_in_build() -> bool:
    # Always available in Python implementation for parity
    return True

def ensure_posthog_initialized(enabled: bool) -> bool:
    if posthog.initialized:
        return True

    posthog.init("PYTHON_MOCK_KEY", {"opt_out_capturing_by_default": not enabled})
    return True

def sync_posthog_capture(enabled: bool) -> bool:
    if enabled:
        ensure_posthog_initialized(True)
        if posthog.has_opted_out_capturing():
            posthog.opt_in_capturing()
        return True

    if posthog.initialized and not posthog.has_opted_out_capturing():
        posthog.opt_out_capturing()
    return False

def register_posthog_build_info(build_info: Dict[str, Any]):
    if not posthog.initialized:
        return

    posthog.register({
        "app_version": build_info.get("version", "dev"),
        "app_commit": build_info.get("commit"),
        "app_branch": build_info.get("branch"),
        "app_build_time": build_info.get("builtOn"),
    })
