import logging
from typing import Optional

logger = logging.getLogger("airi_perception")

class STTInterface:
    def __init__(self, provider: str = "web-speech-api"):
        self.provider = provider

    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        # Placeholder for actual STT implementation
        logger.info(f"Transcribing audio data using {self.provider}...")
        return "Transcribed text placeholder"

    async def start_listening(self):
        logger.info("Started listening for audio input...")

    async def stop_listening(self):
        logger.info("Stopped listening for audio input.")
