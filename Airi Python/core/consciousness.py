import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger("airi_consciousness")

class ConsciousnessConfig(BaseModel):
    active_provider: str = Field("", alias="activeProvider")
    active_model: str = Field("", alias="activeModel")
    ollama_thinking_enabled: bool = Field(False, alias="ollamaThinkingEnabled")

class ConsciousnessStore:
    def __init__(self):
        self.config = ConsciousnessConfig()
        self.is_configured = False

    def set_active_provider(self, provider: str, model: str):
        self.config.active_provider = provider
        self.config.active_model = model
        self.is_configured = bool(provider and model)
        logger.info(f"Consciousness configured with {provider}/{model}")

    def reset_state(self):
        self.config = ConsciousnessConfig()
        self.is_configured = False
