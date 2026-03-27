import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AiriPlugin(ABC):
    def __init__(self, plugin_id: str, name: str, context: Optional[Dict[str, Any]] = None):
        self.plugin_id = plugin_id
        self.name = name
        self.context = context or {}
        self.enabled = False

    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def shutdown(self):
        pass

    async def on_event(self, event: Dict[str, Any]):
        # Default event handler
        pass

class PluginManager:
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self.plugins: Dict[str, AiriPlugin] = {}
        self.context = context or {}

    def register_plugin(self, plugin: AiriPlugin):
        logger.info(f"Registering plugin: {plugin.name} ({plugin.plugin_id})")
        self.plugins[plugin.plugin_id] = plugin

    async def initialize_all(self):
        for plugin in self.plugins.values():
            await plugin.initialize()
            plugin.enabled = True

    async def broadcast_event(self, event: Dict[str, Any]):
        for plugin in self.plugins.values():
            if plugin.enabled:
                await plugin.on_event(event)
