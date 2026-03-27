import logging
from typing import Optional, Literal
from pydantic import BaseModel
from core.display_models import DisplayModel, DisplayModelsStore

logger = logging.getLogger(__name__)

StageModelRenderer = Literal['live2d', 'vrm', 'disabled']

class StageModelSettings:
    def __init__(self, display_models_store: DisplayModelsStore):
        self.display_models_store = display_models_store
        self.stage_model_selected: str = "preset-live2d-1"
        self.stage_model_selected_display_model: Optional[DisplayModel] = None
        self.stage_model_selected_url: Optional[str] = None
        self.stage_model_renderer: Optional[StageModelRenderer] = None
        self.stage_view_controls_enabled: bool = False

    async def update_stage_model(self):
        selected_id = self.stage_model_selected
        if not selected_id:
            self.stage_model_selected_url = None
            self.stage_model_selected_display_model = None
            self.stage_model_renderer = 'disabled'
            return

        model = await self.display_models_store.get_display_model(selected_id)
        if not model:
            self.stage_model_selected_url = None
            self.stage_model_selected_display_model = None
            self.stage_model_renderer = 'disabled'
            return

        self.stage_model_selected_display_model = model
        # Simple mapping for format to renderer
        if model.format.value == 'live2d-zip':
            self.stage_model_renderer = 'live2d'
        elif model.format.value == 'vrm':
            self.stage_model_renderer = 'vrm'
        else:
            self.stage_model_renderer = 'disabled'

        if model.type == 'file':
            self.stage_model_selected_url = model.file_path
        else:
            self.stage_model_selected_url = model.url

    async def initialize_stage_model(self):
        await self.update_stage_model()

    async def reset_state(self):
        self.stage_model_selected = "preset-live2d-1"
        self.stage_model_selected_display_model = None
        self.stage_model_selected_url = None
        self.stage_model_renderer = None
        self.stage_view_controls_enabled = False
        await self.update_stage_model()
        logger.info("Stage model settings reset")
