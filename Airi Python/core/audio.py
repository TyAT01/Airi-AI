import logging
import asyncio
import numpy as np
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel

logger = logging.getLogger("airi_audio")

class SpeakingState(BaseModel):
    mouth_open_size: float = 0.0
    now_speaking: bool = False
    opacity_min: int = 30
    opacity_max: int = 100

    @property
    def avatar_border_opacity(self) -> float:
        if not self.now_speaking:
            return float(self.opacity_min)
        return (self.opacity_min + (self.opacity_max - self.opacity_min) * self.mouth_open_size) / 100.0

def calculate_volume_linear(data_buffer: np.ndarray) -> float:
    # Amplify the volume with a power function
    amplified = (data_buffer.astype(float) ** 1.2) * 1.2
    return float(np.mean(amplified) / 100.0)

def calculate_volume_minmax(data_buffer: np.ndarray) -> float:
    amplified = data_buffer.astype(float) ** 1.5
    v_min = np.min(amplified)
    v_max = np.max(amplified)
    v_range = v_max - v_min

    if v_range == 0:
        normalized = np.zeros_like(amplified)
    else:
        normalized = (amplified - v_min) / v_range

    return float(np.mean(normalized))

def calculate_volume(data_buffer: np.ndarray, mode: Literal['linear', 'minmax'] = 'linear') -> float:
    if mode == 'linear':
        return calculate_volume_linear(data_buffer)
    elif mode == 'minmax':
        return calculate_volume_minmax(data_buffer)
    return 0.0

class AudioContext:
    def __init__(self):
        # In Python, we might use PyAudio or similar for real-time audio
        self.sample_rate = 44100
        logger.info("AudioContext initialized")

class AudioDeviceManager:
    def __init__(self):
        self.selected_input_id: Optional[str] = None
        self.available_inputs: List[Dict[str, str]] = []

    async def list_devices(self):
        # Implementation depends on the library used (e.g. sounddevice)
        logger.info("Listing audio devices")
        return self.available_inputs

    async def start_stream(self):
        logger.info(f"Starting audio stream from {self.selected_input_id}")

    async def stop_stream(self):
        logger.info("Stopping audio stream")
