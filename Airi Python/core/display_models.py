import logging
import time
from enum import Enum
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

class DisplayModelFormat(str, Enum):
    Live2dZip = 'live2d-zip'
    Live2dDirectory = 'live2d-directory'
    VRM = 'vrm'
    PMXZip = 'pmx-zip'
    PMXDirectory = 'pmx-directory'
    PMD = 'pmd'

class DisplayModelFile(BaseModel):
    id: str = Field(default_factory=lambda: f"display-model-{generate()}")
    format: DisplayModelFormat
    type: Literal['file'] = 'file'
    file_path: str = Field(..., alias="file") # In JS this is a File object, here we use path
    name: str
    preview_image: Optional[str] = Field(None, alias="previewImage")
    imported_at: float = Field(default_factory=time.time, alias="importedAt")

    class Config:
        populate_by_name = True

class DisplayModelURL(BaseModel):
    id: str = Field(default_factory=lambda: f"display-model-{generate()}")
    format: DisplayModelFormat
    type: Literal['url'] = 'url'
    url: str
    name: str
    preview_image: Optional[str] = Field(None, alias="previewImage")
    imported_at: float = Field(default_factory=time.time, alias="importedAt")

    class Config:
        populate_by_name = True

DisplayModel = Union[DisplayModelFile, DisplayModelURL]

DISPLAY_MODELS_PRESETS: List[DisplayModel] = [
    DisplayModelURL(
        id='preset-live2d-1',
        format=DisplayModelFormat.Live2dZip,
        type='url',
        url='assets/live2d/models/hiyori_pro_zh.zip',
        name='Hiyori (Pro)',
        previewImage='assets/live2d/models/hiyori/preview.png',
        importedAt=1733113886.840
    ),
    DisplayModelURL(
        id='preset-live2d-2',
        format=DisplayModelFormat.Live2dZip,
        type='url',
        url='assets/live2d/models/hiyori_free_zh.zip',
        name='Hiyori (Free)',
        previewImage='assets/live2d/models/hiyori/preview.png',
        importedAt=1733113886.840
    ),
    DisplayModelURL(
        id='preset-vrm-1',
        format=DisplayModelFormat.VRM,
        type='url',
        url='assets/vrm/models/AvatarSample-A/AvatarSample_A.vrm',
        name='AvatarSample_A',
        previewImage='assets/vrm/models/AvatarSample-A/preview.png',
        importedAt=1733113886.840
    ),
    DisplayModelURL(
        id='preset-vrm-2',
        format=DisplayModelFormat.VRM,
        type='url',
        url='assets/vrm/models/AvatarSample-B/AvatarSample_B.vrm',
        name='AvatarSample_B',
        previewImage='assets/vrm/models/AvatarSample-B/preview.png',
        importedAt=1733113886.840
    ),
]

class DisplayModelsStore:
    """
    Manages avatar models.
    Mimics packages/stage-ui/src/stores/display-models.ts.
    """
    def __init__(self):
        self.display_models: List[DisplayModel] = list(DISPLAY_MODELS_PRESETS)
        self.loading = False

    async def load_display_models(self):
        """
        Loads display models. In Python, this might load from a local directory or database.
        """
        logger.info("Loading display models")
        # For now, it resets to presets or maintains the list.
        self.display_models = sorted(self.display_models, key=lambda x: x.imported_at, reverse=True)

    async def get_display_model(self, model_id: str) -> Optional[DisplayModel]:
        for model in self.display_models:
            if model.id == model_id:
                return model
        return None

    async def add_display_model(self, format: DisplayModelFormat, file_path: str, name: str, preview_image: Optional[str] = None):
        new_model = DisplayModelFile(
            id=f"display-model-{generate()}",
            format=format,
            file=file_path,
            name=name,
            previewImage=preview_image,
            importedAt=time.time()
        )
        self.display_models.insert(0, new_model)
        logger.info(f"Added display model: {name}")
        return new_model

    async def rename_display_model(self, model_id: str, name: str):
        model = await self.get_display_model(model_id)
        if model:
            model.name = name
            logger.info(f"Renamed display model {model_id} to {name}")

    async def remove_display_model(self, model_id: str):
        self.display_models = [m for m in self.display_models if m.id != model_id]
        logger.info(f"Removed display model: {model_id}")

    async def reset_display_models(self):
        self.display_models = list(DISPLAY_MODELS_PRESETS)
        logger.info("Reset display models to presets")
