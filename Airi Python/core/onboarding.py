import logging
import os
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

ESSENTIAL_PROVIDER_IDS = ['openai', 'anthropic', 'google-generative-ai', 'openrouter-ai', 'ollama', 'deepseek', 'openai-compatible']
CREDENTIAL_BASED_ESSENTIAL_PROVIDER_IDS = ['openai', 'anthropic', 'google-generative-ai', 'openrouter-ai', 'deepseek']

class OnboardingStore:
    def __init__(self, providers_store=None, persistence_file: str = "settings/onboarding.json"):
        self.providers_store = providers_store
        self.persistence_file = persistence_file
        self.has_completed_setup = False
        self.has_skipped_setup = False
        self.showing_setup = False
        self._load_from_persistence()

    def _load_from_persistence(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, "r") as f:
                    data = json.load(f)
                    self.has_completed_setup = data.get("has_completed_setup", False)
                    self.has_skipped_setup = data.get("has_skipped_setup", False)
            except Exception as e:
                logger.error(f"Failed to load onboarding persistence: {e}")

    def _save_to_persistence(self):
        os.makedirs(os.path.dirname(self.persistence_file), exist_ok=True)
        try:
            with open(self.persistence_file, "w") as f:
                json.dump({
                    "has_completed_setup": self.has_completed_setup,
                    "has_skipped_setup": self.has_skipped_setup
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save onboarding persistence: {e}")

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
            api_key = config.get("apiKey", "")
            if isinstance(api_key, str) and api_key.strip():
                return True
        return False

    @property
    def needs_onboarding(self) -> bool:
        return not self.has_skipped_setup and not self.has_completed_setup

    def mark_setup_completed(self):
        self.has_completed_setup = True
        self.has_skipped_setup = False
        self.showing_setup = False
        self._save_to_persistence()
        logger.info("Onboarding setup marked as completed")

    def mark_setup_skipped(self):
        self.has_skipped_setup = True
        self.showing_setup = False
        self._save_to_persistence()
        logger.info("Onboarding setup marked as skipped")

    def reset_setup_state(self):
        self.has_completed_setup = False
        self.has_skipped_setup = False
        self.showing_setup = False
        self._save_to_persistence()
        logger.info("Onboarding setup state reset")

    def force_show_setup(self):
        self.showing_setup = True
        logger.info("Forcing onboarding setup to show")
