import logging
import asyncio
import numpy as np
from typing import Literal, Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SpeakingState(BaseModel):
    """
    State for character speaking status and avatar visual feedback.
    Mimics useSpeakingStore in packages/stage-ui/src/stores/audio.ts.
    """
    mouth_open_size: float = 0.0
    now_speaking: bool = False
    opacity_min: int = 30
    opacity_max: int = 100

    @property
    def avatar_border_opacity(self) -> float:
        if not self.now_speaking:
            return float(self.opacity_min)

        # TS: ((nowSpeakingAvatarBorderOpacityMin
        #      + (nowSpeakingAvatarBorderOpacityMax - nowSpeakingAvatarBorderOpacityMin) * mouthOpenSize.value) / 100)
        return (self.opacity_min + (self.opacity_max - self.opacity_min) * self.mouth_open_size) / 100.0

def calculate_volume_linear(data_buffer: np.ndarray) -> float:
    """
    Calculates volume using linear normalization.
    Mimics calculateVolumeWithLinearNormalize in TS.
    """
    # TS uses frequency data, here we assume data_buffer is equivalent
    # TS logic: (volumeSum / dataBuffer.length / 100)
    # where volumeSum is sum of (v ** 1.2) * 1.2

    amplified = (data_buffer.astype(float) ** 1.2) * 1.2
    volume_sum = np.sum(amplified)

    return float(volume_sum / len(data_buffer) / 100.0)

def calculate_volume_minmax(data_buffer: np.ndarray) -> float:
    """
    Calculates volume using Min-Max normalization.
    Mimics calculateVolumeWithMinMaxNormalize in TS.
    """
    # TS logic: amplifiedVolumeVector = dataBuffer.map(v => v ** 1.5)
    amplified = data_buffer.astype(float) ** 1.5

    v_min = np.min(amplified)
    v_max = np.max(amplified)
    v_range = v_max - v_min

    if v_range == 0:
        # TS: normalizedVolumeVector = amplifiedVolumeVector.map(() => 0)
        normalized = np.zeros_like(amplified)
    else:
        # TS: (v - min) / range
        normalized = (amplified - v_min) / v_range

    # TS: volumeSum / dataBuffer.length
    return float(np.mean(normalized))

def calculate_volume(data_buffer: np.ndarray, mode: Literal['linear', 'minmax'] = 'linear') -> float:
    """
    Main volume calculation entry point.
    """
    if mode == 'linear':
        return calculate_volume_linear(data_buffer)
    elif mode == 'minmax':
        return calculate_volume_minmax(data_buffer)
    return 0.0

class AudioContext:
    """
    Wrapper for audio context, mimicking Web Audio API's AudioContext.
    """
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        logger.info(f"AudioContext initialized with sample rate: {sample_rate}")

class AudioDeviceManager:
    """
    Manages audio devices and streams.
    Mimics useAudioDevice in packages/stage-ui/src/stores/audio.ts.
    """
    def __init__(self):
        self.selected_input_id: Optional[str] = None
        self.available_inputs: List[Dict[str, str]] = []
        self.stream: Any = None # MediaStream equivalent

    async def list_devices(self):
        # Implementation would use sounddevice or similar
        logger.info("Listing audio devices")
        return self.available_inputs

    async def ask_permission(self):
        # In desktop Python, this is often handled by the OS or the library on stream start
        logger.info("Ensuring audio permissions")
        return True

    async def start_stream(self, constraints: Optional[Dict[str, Any]] = None):
        logger.info(f"Starting audio stream from {self.selected_input_id}")

    async def stop_stream(self):
        logger.info("Stopping audio stream")
        self.stream = None
