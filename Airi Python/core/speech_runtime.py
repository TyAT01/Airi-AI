import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("airi_speech_runtime")

class SpeechIntent:
    def __init__(self, intent_id: str):
        self.intent_id = intent_id

    def write_literal(self, text: str):
        pass

    def write_special(self, special: str):
        pass

    def write_flush(self):
        pass

    def end(self):
        pass

class SpeechPipelineRuntime:
    def __init__(self):
        self.hosts = []

    def open_intent(self, options: Optional[Dict[str, Any]] = None) -> SpeechIntent:
        intent_id = options.get("intentId", "default") if options else "default"
        logger.info(f"Opening speech intent: {intent_id}")
        return SpeechIntent(intent_id)

    async def register_host(self, pipeline: Any):
        logger.info("Registering speech pipeline host")
        self.hosts.append(pipeline)

    def is_host(self) -> bool:
        return len(self.hosts) > 0

    async def dispose(self):
        logger.info("Disposing speech pipeline runtime")
        self.hosts = []

class SpeechRuntimeStore:
    def __init__(self):
        self.runtime = SpeechPipelineRuntime()

    def open_intent(self, options: Optional[Dict[str, Any]] = None) -> SpeechIntent:
        return self.runtime.open_intent(options)

    async def register_host(self, pipeline: Any):
        await self.runtime.register_host(pipeline)

    def is_host(self) -> bool:
        return self.runtime.is_host()

    async def dispose(self):
        await self.runtime.dispose()
