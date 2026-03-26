import time
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

logger = logging.getLogger("airi_lipsync")

class LipSyncConfig(BaseModel):
    cap: float = 0.7
    volume_scale: float = 0.9
    volume_exponent: float = 0.7
    update_interval_ms: int = 40
    lerp_window_ms: int = 120

class LipSyncEngine:
    """
    Advanced LipSync engine for Python.
    Remaps audio analysis (AEIOU) to visual parameters.
    """
    def __init__(self, config: Optional[LipSyncConfig] = None):
        self.config = config or LipSyncConfig()
        self.last_raw_mouth_open = 0.0
        self.last_raw_update_ms = 0.0
        self.smoothed_mouth_open = 0.0
        self.last_smoothed_ms = 0.0
        self.current_volume = 0.0
        # Weights for visemes
        self.current_weights = {"A": 0.0, "E": 0.0, "I": 0.0, "O": 0.0, "U": 0.0}

    def update_audio_data(self, volume: float, weights: Dict[str, float]):
        """
        Updates viseme weights based on audio volume and frequency analysis.
        """
        self.current_volume = volume
        vowels = ["A", "E", "I", "O", "U"]

        # Non-linear amplification based on volume
        amp = min(volume * self.config.volume_scale, 1.0) ** self.config.volume_exponent

        for v in vowels:
            raw_val = weights.get(v, 0.0)
            # Port logic: 'S' noise often remaps well to 'I' shape for speech clarity
            if v == "I":
                raw_val = max(raw_val, weights.get("S", 0.0))

            self.current_weights[v] = max(0.0, min(self.config.cap, raw_val * amp))

    def get_mouth_open(self) -> float:
        """
        Returns the smoothed mouth opening value (0.0 to 1.0).
        """
        now_ms = time.time() * 1000

        # Update raw target at specified intervals
        if now_ms - self.last_raw_update_ms >= self.config.update_interval_ms:
            self.last_raw_mouth_open = max(self.current_weights.values()) if self.current_weights else 0.0
            self.last_raw_update_ms = now_ms

        # Linear interpolation (smoothing)
        if self.last_smoothed_ms == 0 or self.config.lerp_window_ms <= 0:
            self.smoothed_mouth_open = self.last_raw_mouth_open
        else:
            dt = now_ms - self.last_smoothed_ms
            alpha = min(1.0, dt / self.config.lerp_window_ms)
            self.smoothed_mouth_open += (self.last_raw_mouth_open - self.smoothed_mouth_open) * alpha

        self.last_smoothed_ms = now_ms
        return self.smoothed_mouth_open

    def get_viseme_params(self) -> Dict[str, float]:
        """
        Returns the current viseme weights for rendering.
        """
        return self.current_weights.copy()
