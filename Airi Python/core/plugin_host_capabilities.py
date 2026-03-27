import logging
from typing import List, Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PluginHostProviderSummary(BaseModel):
    name: str

def list_providers_for_plugin_host() -> List[PluginHostProviderSummary]:
    # In Python, we might list the providers currently registered in the catalog
    # or available in the project structure.
    # For now, placeholder summary
    return [PluginHostProviderSummary(name="Airi Internal Provider")]

def should_publish_plugin_host_capabilities() -> bool:
    # On Python, we decide based on environment or configuration
    return True
