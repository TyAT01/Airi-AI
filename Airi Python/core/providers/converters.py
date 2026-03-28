import logging
from typing import Dict, Any, List, Optional, Union, Callable
from pydantic import BaseModel, Field
from pydantic_core import PydanticUndefined

logger = logging.getLogger(__name__)

class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: Optional[str] = ""
    capabilities: Optional[List[str]] = []
    context_length: Optional[int] = Field(0, alias="contextLength")
    deprecated: Optional[bool] = False

    model_config = {
        "populate_by_name": True
    }

class VoiceInfo(BaseModel):
    id: str
    name: str
    provider: str
    compatible_models: Optional[List[str]] = Field(None, alias="compatibleModels")
    description: Optional[str] = None
    gender: Optional[str] = None
    deprecated: Optional[bool] = False
    preview_url: Optional[str] = Field(None, alias="previewURL")
    languages: List[Dict[str, str]] = []

    model_config = {
        "populate_by_name": True
    }

def get_category_from_tasks(tasks: List[str]) -> str:
    tasks_lower = [t.lower() for t in tasks]
    if any(task in tasks_lower for task in ['speech-to-text', 'automatic-speech-recognition', 'asr', 'stt']):
        return 'transcription'
    if any(task in tasks_lower for task in ['text-to-speech', 'speech', 'tts']):
        return 'speech'
    if any(task in tasks_lower for task in ['embed', 'embedding']):
        return 'embed'
    return 'chat'

def map_models_to_metadata_models(provider_id: str, models: List[Union[Dict[str, Any], Any]]) -> List[Dict[str, Any]]:
    result = []
    for model in models:
        if isinstance(model, dict):
            m_id = model.get('id')
            m_name = model.get('name') or model.get('display_name') or m_id
            m_desc = model.get('description', '')
            m_ctx = model.get('context_length', 0)
        else:
            m_id = getattr(model, "id", None)
            m_name = getattr(model, "name", getattr(model, "display_name", m_id))
            m_desc = getattr(model, "description", "")
            m_ctx = getattr(model, "context_length", 0)

        result.append({
            "id": m_id,
            "name": m_name,
            "provider": provider_id,
            "description": m_desc,
            "contextLength": m_ctx,
            "deprecated": False
        })
    return result

def extract_schema_defaults(config_model: Optional[type[BaseModel]]) -> Dict[str, Any]:
    if not config_model:
        return {}

    defaults = {}
    for field_name, field_info in config_model.model_fields.items():
        if field_info.default is not PydanticUndefined and field_info.default != ...:
            defaults[field_info.alias or field_name] = field_info.default
        elif field_info.default_factory is not None:
            defaults[field_info.alias or field_name] = field_info.default_factory()

    return defaults

class ProviderMetadata(BaseModel):
    id: str
    order: int = 0
    category: str
    tasks: List[str]
    name: str
    description: Optional[str] = ""
    icon: Optional[str] = None
    icon_color: Optional[str] = Field(None, alias="iconColor")
    icon_image: Optional[str] = Field(None, alias="iconImage")
    default_options: Dict[str, Any] = Field(default_factory=dict, alias="defaultOptions")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }

def convert_provider_definition_to_metadata(
    definition: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> ProviderMetadata:
    tasks = definition.get("tasks", [])
    category = get_category_from_tasks(tasks)

    config_model = definition.get("config_model")
    schema_defaults = extract_schema_defaults(config_model)

    return ProviderMetadata(
        id=definition.get("id", ""),
        order=definition.get("order", 0),
        category=category,
        tasks=tasks,
        name=definition.get("name", ""),
        description=definition.get("description", ""),
        icon=definition.get("icon"),
        iconColor=definition.get("icon_color"),
        iconImage=definition.get("icon_image"),
        defaultOptions=schema_defaults
    )

def convert_provider_definitions_to_metadata(
    definitions: List[Dict[str, Any]],
    current_metadata: Dict[str, Any]
) -> Dict[str, ProviderMetadata]:
    translated = {}
    for definition in definitions:
        provider_id = definition.get("id")
        if provider_id:
            translated[provider_id] = convert_provider_definition_to_metadata(definition)
    return translated

def convert_model_to_info(model: Any, provider_id: str) -> ModelInfo:
    if isinstance(model, dict):
        return ModelInfo(
            id=model.get("id"),
            name=model.get("name") or model.get("id"),
            provider=provider_id,
            description=model.get("description", ""),
            contextLength=model.get("context_length", 0),
            deprecated=model.get("deprecated", False)
        )
    return ModelInfo(
        id=model.id,
        name=getattr(model, "name", model.id),
        provider=provider_id,
        description=getattr(model, "description", ""),
        contextLength=getattr(model, "context_length", 0),
        deprecated=getattr(model, "deprecated", False)
    )

def convert_voice_to_info(voice: Any, provider_id: str) -> VoiceInfo:
    if isinstance(voice, dict):
        return VoiceInfo(
            id=voice.get("id"),
            name=voice.get("name") or voice.get("id"),
            provider=provider_id,
            previewURL=voice.get("preview_audio_url"),
            languages=voice.get("languages", []),
            gender=voice.get("gender", "unknown")
        )
    return VoiceInfo(
        id=voice.id,
        name=getattr(voice, "name", voice.id),
        provider=provider_id,
        previewURL=getattr(voice, "preview_audio_url", None),
        languages=getattr(voice, "languages", []),
        gender=getattr(voice, "gender", "unknown")
    )
