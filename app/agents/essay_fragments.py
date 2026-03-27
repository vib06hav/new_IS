import re
from typing import Any


MAX_SENTENCES_PER_FRAGMENT = 2


def build_essay_fragments(canonical: dict[str, Any], entity_id_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fragments: list[dict[str, Any]] = []
    essay_entity_ids = {
        mapping.get("descriptor"): mapping.get("entity_id")
        for mapping in entity_id_map
        if mapping.get("collection") == "essay_entries" and mapping.get("descriptor") and mapping.get("entity_id")
    }

    for essay in canonical.get("essay_entries", []):
        if essay.get("placeholder_flag") or not essay.get("raw_text"):
            continue

        entity_id = essay_entity_ids.get(essay.get("essay_identifier"))
        if not entity_id:
            continue

        text = str(essay.get("raw_text") or "")
        spans = _paragraph_spans(text)
        if not spans:
            spans = _sentence_group_spans(text)

        for index, (start_char, end_char) in enumerate(spans, start=1):
            fragment_text = text[start_char:end_char]
            if not fragment_text.strip():
                continue
            fragments.append(
                {
                    "fragment_id": f"{entity_id}:F{index:02d}",
                    "entity_id": entity_id,
                    "text": fragment_text,
                    "start_char": start_char,
                    "end_char": end_char,
                }
            )

    return fragments


def _paragraph_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    matches = list(re.finditer(r"\n\s*\n+", text))
    if not matches:
        return spans

    start = 0
    for match in matches:
        end = match.start()
        if text[start:end].strip():
            trimmed_start, trimmed_end = _trim_span(text, start, end)
            spans.append((trimmed_start, trimmed_end))
        start = match.end()

    if text[start:].strip():
        trimmed_start, trimmed_end = _trim_span(text, start, len(text))
        spans.append((trimmed_start, trimmed_end))

    return spans


def _sentence_group_spans(text: str) -> list[tuple[int, int]]:
    sentence_spans = [
        (match.start(), match.end())
        for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text, flags=re.S)
        if match.group(0).strip()
    ]
    if not sentence_spans:
        stripped = text.strip()
        if not stripped:
            return []
        start = text.find(stripped)
        return [(start, start + len(stripped))]

    grouped_spans: list[tuple[int, int]] = []
    group_start = sentence_spans[0][0]
    group_end = sentence_spans[0][1]
    sentence_count = 1

    for start, end in sentence_spans[1:]:
        if sentence_count >= MAX_SENTENCES_PER_FRAGMENT:
            trimmed_start, trimmed_end = _trim_span(text, group_start, group_end)
            grouped_spans.append((trimmed_start, trimmed_end))
            group_start, group_end = start, end
            sentence_count = 1
            continue

        group_end = end
        sentence_count += 1

    trimmed_start, trimmed_end = _trim_span(text, group_start, group_end)
    grouped_spans.append((trimmed_start, trimmed_end))
    return grouped_spans


def _trim_span(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end
