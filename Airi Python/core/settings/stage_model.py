import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field
from core.display_models import DisplayModel, DisplayModelsStore

logger = logging.getLogger(__name__)

StageModelRenderer = Literal['live2d', 'vrm', 'disabled']

class StageModelSettings(BaseModel):
    """
    Manages the character model displayed on the stage.
    Mimics packages/stage-ui/src/stores/settings/stage-model.ts.
    """
    stage_model_selected: str = Field("preset-live2d-1", alias="stageModelSelected")
    stage_model_selected_display_model: Optional[DisplayModel] = Field(None, alias="stageModelSelectedDisplayModel")
    stage_model_selected_url: Optional[str] = Field(None, alias="stageModelSelectedUrl")
    stage_model_renderer: Optional[StageModelRenderer] = Field(None, alias="stageModelRenderer")
    stage_view_controls_enabled: bool = Field(False, alias="stageViewControlsEnabled")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

    def __init__(self, display_models_store: DisplayModelsStore, **data):
        super().__init__(**data)
        self._display_models_store = display_models_store
        self._stage_model_update_sequence = 0

    async def update_stage_model(self):
        self._stage_model_update_sequence += 1
        request_id = self._stage_model_update_sequence
        selected_id = self.stage_model_selected

        if not selected_id:
            self.stage_model_selected_url = None
            self.stage_model_selected_display_model = None
            self.stage_model_renderer = 'disabled'
            return

        model = await self._display_models_store.get_display_model(selected_id)

        # In a multi-threaded or highly async env, we'd check request_id here.
        if request_id != self._stage_model_update_sequence:
            return

        if not model:
            self.stage_model_selected_url = None
            self.stage_model_selected_display_model = None
            self.stage_model_renderer = 'disabled'
            return

        self.stage_model_selected_display_model = model

        from core.display_models import DisplayModelFormat
        if model.format == DisplayModelFormat.Live2dZip:
            self.stage_model_renderer = 'live2d'
        elif model.format == DisplayModelFormat.VRM:
            self.stage_model_renderer = 'vrm'
        else:
            self.stage_model_renderer = 'disabled'

        if model.type == 'file':
            # Mirroring URL.createObjectURL behavior with file paths or local URIs
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
