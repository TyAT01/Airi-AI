import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class VisionCapturePayload(BaseModel):
    image_data_url: str = Field(..., alias="imageDataUrl")
    workload_id: str = Field(..., alias="workloadId")
    source_id: Optional[str] = Field(None, alias="sourceId")
    captured_at: Optional[float] = Field(None, alias="capturedAt")
    publish_context: bool = Field(False, alias="publishContext")

class VisionOrchestratorStore:
    def __init__(self, vision_store=None):
        self.vision_store = vision_store
        self.last_result_text = ""
        self.last_result_at: Optional[float] = None
        self.last_error: Optional[str] = None
        self.last_workload_id = "screen:interpret"

    async def process_capture(self, payload: VisionCapturePayload):
        if not self.vision_store or not self.vision_store.configured:
            raise RuntimeError("Vision model is not configured")

        self.last_workload_id = payload.workload_id

        # Placeholder for inference logic
        text = "Vision inference result"

        self.last_result_text = text
        self.last_result_at = time.time()
        self.last_error = None

        if payload.publish_context:
            logger.info(f"Publishing vision context for {payload.workload_id}")
            # Context update logic here
            return {"contextUpdates": 1, "text": text}

        return {"contextUpdates": 0, "text": text}

    def record_error(self, error: Exception):
        self.last_error = str(error)
        logger.error(f"Vision orchestrator error: {error}")
