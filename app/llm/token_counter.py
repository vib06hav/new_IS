import json
import re
from typing import Any


def estimate_text_tokens(text: str | None) -> int:
    """
    Lightweight token estimate without provider-specific tokenizers.
    Uses a conservative heuristic based on characters and lexical pieces.
    """
    if not text:
        return 0

    normalized = str(text)
    piece_count = len(re.findall(r"\w+|[^\w\s]", normalized, flags=re.UNICODE))
    char_estimate = max(1, len(normalized) // 4)
    return max(char_estimate, piece_count)


def estimate_messages_tokens(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages or []:
        total += 4  # lightweight chat framing overhead
        total += estimate_text_tokens(message.get("role", ""))
        total += estimate_text_tokens(message.get("content", ""))
    return total + 2


def estimate_json_tokens(payload: Any) -> int:
    return estimate_text_tokens(json.dumps(payload, ensure_ascii=False))

