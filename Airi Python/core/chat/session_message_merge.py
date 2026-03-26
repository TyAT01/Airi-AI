from typing import List, Union, Dict, Any, Optional

def extract_message_content(message: Dict[str, Any]) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part.get("text", "")))
        return "".join(parts)

    return ""

def get_message_fingerprint(message: Dict[str, Any]) -> str:
    return "\u001F".join([
        str(message.get("id", "")),
        str(message.get("role", "")),
        str(message.get("createdAt", "")),
        extract_message_content(message)
    ])

def merge_loaded_session_messages(stored_messages: List[Dict[str, Any]], current_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not current_messages:
        return stored_messages

    current_non_system_messages = [
        msg for i, msg in enumerate(current_messages)
        if i != 0 or msg.get("role") != "system"
    ]

    if not current_non_system_messages:
        return stored_messages

    seen = {get_message_fingerprint(msg) for msg in stored_messages}
    extra_messages = []
    for msg in current_non_system_messages:
        fingerprint = get_message_fingerprint(msg)
        if fingerprint not in seen:
            extra_messages.append(msg)
            seen.add(fingerprint)

    if not extra_messages:
        return stored_messages

    system_message = None
    if stored_messages and stored_messages[0].get("role") == "system":
        system_message = stored_messages[0]
    elif current_messages and current_messages[0].get("role") == "system":
        system_message = current_messages[0]

    if not stored_messages and system_message:
        return [system_message] + extra_messages

    return stored_messages + extra_messages
