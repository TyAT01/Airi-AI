import re
from typing import List, Dict, Any, Optional

class ResponseCategorizer:
    def __init__(self):
        self.buffer = ""

    def categorize(self, text: str) -> Dict[str, Any]:
        # Simple regex-based tag extraction (think, thought, reasoning)
        # Porting logic from response-categoriser.ts
        segments = []
        pattern = r"<(think|thought|reasoning)>(.*?)</\1>"

        matches = list(re.finditer(pattern, text, re.DOTALL))

        speech_parts = []
        last_end = 0

        reasoning_content = []

        for match in matches:
            tag_name = match.group(1)
            content = match.group(2)

            # Text before tag
            if match.start() > last_end:
                speech_part = text[last_end:match.start()].strip()
                if speech_part:
                    speech_parts.append(speech_part)

            segments.append({
                "category": "reasoning",
                "content": content.strip(),
                "tagName": tag_name,
                "raw": match.group(0)
            })
            reasoning_content.append(content.strip())
            last_end = match.end()

        # Text after last tag
        if last_end < len(text):
            speech_part = text[last_end:].strip()
            if speech_part:
                speech_parts.append(speech_part)

        return {
            "segments": segments,
            "speech": " ".join(speech_parts).strip(),
            "reasoning": "\n\n".join(reasoning_content),
            "raw": text
        }

    def filter_to_speech(self, text: str) -> str:
        # Quick filter to remove all XML-like tags for TTS
        return re.sub(r"<[^>]*>.*?</[^>]*>", "", text, flags=re.DOTALL).strip()
