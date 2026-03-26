import re
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel

logger = logging.getLogger("airi_response_categoriser")

class CategorizedSegment(BaseModel):
    category: Literal["speech", "reasoning", "unknown"]
    content: str
    start_index: int
    end_index: int
    raw: str
    tag_name: str

class CategorizedResponse(BaseModel):
    segments: List[CategorizedSegment]
    speech: str
    reasoning: str
    raw: str

def categorize_response(response: str) -> CategorizedResponse:
    """
    Categorizes a model response by extracting XML-like tags (e.g., <think>).
    Mimics logic from packages/stage-ui/src/composables/response-categoriser.ts
    """
    # Simple regex for finding complete XML tags
    tag_pattern = re.compile(r'<(.*?)>(.*?)</\1>', re.DOTALL)

    segments = []
    for match in tag_pattern.finditer(response):
        tag_name = match.group(1)
        content = match.group(2)
        segments.append(CategorizedSegment(
            category="reasoning", # All tags are treated as reasoning in the original
            content=content.strip(),
            start_index=match.start(),
            end_index=match.end(),
            raw=match.group(0),
            tag_name=tag_name
        ))

    # Sort segments by position
    segments.sort(key=lambda x: x.start_index)

    # Extract speech content (everything outside tags)
    speech_parts = []
    last_end = 0
    for segment in segments:
        if segment.start_index > last_end:
            text = response[last_end:segment.start_index].strip()
            if text:
                speech_parts.append(text)
        last_end = max(last_end, segment.end_index)

    if last_end < len(response):
        text = response[last_end:].strip()
        if text:
            speech_parts.append(text)

    reasoning = "\n\n".join([s.content for s in segments if s.category == "reasoning"])
    speech = " ".join(speech_parts).strip()

    return CategorizedResponse(
        segments=segments,
        speech=speech,
        reasoning=reasoning,
        raw=response
    )

class StreamingCategorizer:
    def __init__(self):
        self.buffer = ""
        self.categorized: Optional[CategorizedResponse] = None

    def consume(self, chunk: str):
        self.buffer += chunk
        # In a real streaming implementation, we'd do incremental parsing
        # For now, re-categorize the whole buffer
        self.categorized = categorize_response(self.buffer)

    def filter_to_speech(self, text: str, start_position: int) -> str:
        """
        Filters text to only include speech parts by excluding segments in reasoning.
        """
        if not self.categorized or not self.categorized.segments:
            return text

        filtered = ""
        end_position = start_position + len(text)
        current_pos = start_position

        overlapping_segments = [
            s for s in self.categorized.segments
            if s.end_index > start_position and s.start_index < end_position
        ]

        if not overlapping_segments:
            return text

        for segment in overlapping_segments:
            seg_start = max(segment.start_index, start_position)
            seg_end = min(segment.end_index, end_position)

            if seg_start > current_pos:
                filtered += text[current_pos - start_position : seg_start - start_position]
            current_pos = seg_end

        if current_pos < end_position:
            filtered += text[current_pos - start_position:]

        return filtered
