import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_onboarding")

ESSENTIAL_PROVIDER_IDS = ['openai', 'anthropic', 'google-generative-ai', 'openrouter-ai', 'ollama', 'deepseek', 'openai-compatible']
CREDENTIAL_BASED_ESSENTIAL_PROVIDER_IDS = ['openai', 'anthropic', 'google-generative-ai', 'openrouter-ai', 'deepseek']

class OnboardingStore:
    def __init__(self, providers_store=None):
        self.providers_store = providers_store
        self.has_completed_setup = False
        self.has_skipped_setup = False
        self.showing_setup = False

    @property
    def has_essential_provider_configured(self) -> bool:
        if not self.providers_store:
            return False
        return any(self.providers_store.configured_providers.get(pid, False) for pid in ESSENTIAL_PROVIDER_IDS)

    @property
    def has_essential_provider_credential_configured(self) -> bool:
        if not self.providers_store:
            return False
        for pid in CREDENTIAL_BASED_ESSENTIAL_PROVIDER_IDS:
            config = self.providers_store.providers.get(pid, {})
            if config.get("apiKey", "").strip():
                return True
        return False

    @property
    def needs_onboarding(self) -> bool:
        return not self.has_skipped_setup and not self.has_completed_setup

    def mark_setup_completed(self):
        self.has_completed_setup = True
        self.has_skipped_setup = False
        self.showing_setup = False
        logger.info("Onboarding setup marked as completed")

    def mark_setup_skipped(self):
        self.has_skipped_setup = True
        self.showing_setup = False
        logger.info("Onboarding setup marked as skipped")

    def reset_setup_state(self):
        self.has_completed_setup = False
        self.has_skipped_setup = False
        self.showing_setup = False
        logger.info("Onboarding setup state reset")

    def force_show_setup(self):
        self.showing_setup = True
        logger.info("Forcing onboarding setup to show")
