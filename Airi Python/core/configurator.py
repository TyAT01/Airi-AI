import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Configurator:
    """
    Adapter for project-airi:server-sdk equivalent in Python.
    Mimics packages/stage-ui/src/stores/configurator.ts.
    """
    def __init__(self, mods_server_channel_store=None):
        self.mods_server_channel_store = mods_server_channel_store

    def update_for(self, module_name: str, config: Dict[str, Any]):
        """
        Sends a 'ui:configure' event to the mods server channel.
        """
        logger.info(f"Updating configuration for {module_name}: {config}")
        if self.mods_server_channel_store:
            self.mods_server_channel_store.send({
                "type": "ui:configure",
                "data": {
                    "moduleName": module_name,
                    "config": config,
                },
            })
        else:
            logger.warning("No mods_server_channel_store provided, cannot send update.")
