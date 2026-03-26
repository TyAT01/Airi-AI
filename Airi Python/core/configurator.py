import logging
from typing import Dict, Any

logger = logging.getLogger("airi_configurator")

class Configurator:
    def __init__(self, server_channel=None):
        self.server_channel = server_channel

    def update_for(self, module_name: str, config: Dict[str, Any]):
        logger.info(f"Updating configuration for {module_name}: {config}")
        if self.server_channel:
            self.server_channel.send({
                "type": "ui:configure",
                "data": {
                    "moduleName": module_name,
                    "config": config,
                },
            })
