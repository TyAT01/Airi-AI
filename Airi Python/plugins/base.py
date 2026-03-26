import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger("airi_plugins")

class AiriPlugin(ABC):
    def __init__(self, plugin_id: str, name: str):
        self.plugin_id = plugin_id
        self.name = name
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
    def __init__(self):
        self.plugins: Dict[str, AiriPlugin] = {}

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
