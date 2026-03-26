from typing import Dict, Any, Optional
from schemas.protocol import ModuleIdentity

def get_event_source_key(envelope: Dict[str, Any]) -> str:
    """
    Resolves a unique key for an event source.
    Mimics src/utils/event-source.ts logic.
    """
    metadata = envelope.get("metadata", {})
    source = metadata.get("source")

    if not source:
        # Check deprecated source field
        source_id = envelope.get("source")
        if isinstance(source_id, str):
            return source_id
        return "unknown"

    if isinstance(source, dict):
        # ModuleIdentity shape
        plugin_id = source.get("plugin", {}).get("id", "unknown")
        instance_id = source.get("id", "unknown")
        return f"{plugin_id}:{instance_id}"

    return str(source)
