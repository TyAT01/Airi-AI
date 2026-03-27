import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def create_datetime_context() -> Dict[str, Any]:
    import time
    from datetime import datetime

    now = datetime.now()
    content = f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

    return {
        "role": "system",
        "content": content,
        "strategy": "replace-self",
        "metadata": {
            "type": "datetime",
            "timestamp": time.time()
        }
    }
