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
    def __init__(self, config: Optional[LipSyncConfig] = None):
        self.config = config or LipSyncConfig()
        self.last_raw_mouth_open = 0.0
        self.last_raw_update_ms = 0.0
        self.smoothed_mouth_open = 0.0
        self.last_smoothed_ms = 0.0
        self.current_volume = 0.0
        self.current_weights = {"A": 0.0, "E": 0.0, "I": 0.0, "O": 0.0, "U": 0.0}

    def update_audio_data(self, volume: float, weights: Dict[str, float]):
        self.current_volume = volume
        # AEIOUS to AEIOU remapping
        vowels = ["A", "E", "I", "O", "U"]
        amp = min(volume * self.config.volume_scale, 1.0) ** self.config.volume_exponent

        for v in vowels:
            raw_val = weights.get(v, 0.0)
            if v == "I": # Special handling for 'S' remapped to 'I'
                raw_val = max(raw_val, weights.get("S", 0.0))
            self.current_weights[v] = max(0.0, min(self.config.cap, raw_val * amp))

    def get_mouth_open(self) -> float:
        now_ms = time.time() * 1000

        if now_ms - self.last_raw_update_ms >= self.config.update_interval_ms:
            self.last_raw_mouth_open = max(self.current_weights.values()) if self.current_weights else 0.0
            self.last_raw_update_ms = now_ms

        if self.last_smoothed_ms == 0 or self.config.lerp_window_ms <= 0:
            self.smoothed_mouth_open = self.last_raw_mouth_open
        else:
            alpha = min(1.0, (now_ms - self.last_smoothed_ms) / self.config.lerp_window_ms)
            self.smoothed_mouth_open += (self.last_raw_mouth_open - self.smoothed_mouth_open) * alpha

        self.last_smoothed_ms = now_ms
        return self.smoothed_mouth_open
