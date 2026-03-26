import json
import base64
import struct
import logging
import httpx
from typing import List, Dict, Any, Optional, AsyncIterable
from pydantic import BaseModel

logger = logging.getLogger("airi_openrouter_speech")

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/"
DEFAULT_MODEL = "openai/gpt-audio-mini"
PROVIDER_ID = "openrouter-audio-speech"

def tts_prompt_template(input_text: str) -> str:
    return f"Read this text aloud exactly as written, without any commentary or extra words:\n\n{input_text}"

OPENAI_VOICES = [
    "alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse", "marin", "cedar"
]

class OpenRouterSpeechProvider:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

    async def generate_speech(self, input_text: str, voice: str, model: str = DEFAULT_MODEL) -> bytes:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/proj-airi/airi", # Attribution
            "X-Title": "Airi"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": tts_prompt_template(input_text)}
            ],
            "modalities": ["text", "audio"],
            "audio": {"voice": voice, "format": "pcm16"},
            "stream": True
        }

        audio_chunks = []
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}chat/completions", headers=headers, json=payload, timeout=60.0) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"OpenRouter speech request failed: {response.status_code} {error_text.decode()}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            audio_data = chunk.get("choices", [{}])[0].get("delta", {}).get("audio", {}).get("data")
                            if audio_data:
                                audio_chunks.append(audio_data)
                        except json.JSONDecodeError:
                            continue

        pcm_bytes = base64.b64decode("".join(audio_chunks))
        return self._wrap_pcm_in_wav(pcm_bytes)

    def _wrap_pcm_in_wav(self, pcm_bytes: bytes, sample_rate: int = 24000) -> bytes:
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        data_size = len(pcm_bytes)

        # WAV Header
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_size, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
        header += struct.pack('<4sI', b'data', data_size)

        return header + pcm_bytes

def list_voices():
    return [{"id": v, "name": v.capitalize()} for v in OPENAI_VOICES]
