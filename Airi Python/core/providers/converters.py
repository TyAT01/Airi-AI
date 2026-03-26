import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("airi_converters")

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    contextLength: Optional[int] = 0
    deprecated: Optional[bool] = False

class VoiceInfo(BaseModel):
    id: str
    name: str
    provider: str
    compatibleModels: Optional[List[str]] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    deprecated: Optional[bool] = False
    previewURL: Optional[str] = None
    languages: List[Dict[str, str]] = []

def convert_provider_definitions_to_metadata(definitions: List[Dict[str, Any]], t: Any, metadata: Dict[str, Any]) -> Dict[str, Any]:
    # Placeholder for converting provider definitions to metadata
    # In TS it uses i18n translation keys
    logger.info("Converting provider definitions to metadata")
    return metadata

def convert_model_to_info(model: Any, provider_id: str) -> ModelInfo:
    return ModelInfo(
        id=model.id,
        name=getattr(model, "name", model.id),
        provider=provider_id,
        description=getattr(model, "description", ""),
        contextLength=getattr(model, "context_length", 0),
        deprecated=getattr(model, "deprecated", False)
    )

def convert_voice_to_info(voice: Any, provider_id: str) -> VoiceInfo:
    return VoiceInfo(
        id=voice.id,
        name=getattr(voice, "name", voice.id),
        provider=provider_id,
        previewURL=getattr(voice, "preview_audio_url", None),
        languages=getattr(voice, "languages", []),
        gender=getattr(voice, "gender", "unknown")
    )
