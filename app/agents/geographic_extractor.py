from typing import Any, Dict, List, Optional

from app.utils.block_deduper import dedupe_near_overlapping_blocks
from app.utils.row_grouper import group_blocks_into_rows
from app.utils.text_normalization import normalize_label


FIELD_ALIASES = {
    "city": {"town city", "city"},
    "state": {"state"},
    "country": {"country name", "country"},
}

ADDRESS_SECTION_PRIORITY = {
    "permanent address": 0,
    "communication address": 1,
    "address details": 2,
}


def _all_field_labels() -> set[str]:
    labels = set()
    for aliases in FIELD_ALIASES.values():
        labels.update(aliases)
    labels.update({"district", "pin code", "pin", "address"})
    return labels


def _extract_value_from_row(row: List[Dict[str, Any]], label_aliases: set[str]) -> Optional[str]:
    all_field_labels = _all_field_labels()

    for block in row[1:]:
        value = str(block.get("text", "")).strip()
        if not value:
            continue
        normalized = normalize_label(value)
        if not normalized:
            continue
        if normalized in all_field_labels:
            continue
        if normalized.split(" ", 1)[0] in {"district", "city", "state", "country", "pin", "address"}:
            continue
        if value.endswith(":"):
            continue
        return value

    return None


def _extract_candidate(section: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    blocks = dedupe_near_overlapping_blocks(section.get("blocks", []))
    if not blocks:
        return None

    rows = group_blocks_into_rows(blocks, y_threshold=12.0)
    candidate = {"city": None, "state": None, "country": None}

    for row in rows:
        if not row:
            continue
        first_label = normalize_label(row[0].get("text", ""))
        if not first_label:
            continue

        target_field = None
        for field, aliases in FIELD_ALIASES.items():
            if first_label in aliases:
                target_field = field
                break

        if not target_field or candidate[target_field] is not None:
            continue

        value = _extract_value_from_row(row, FIELD_ALIASES[target_field])
        if value:
            candidate[target_field] = value

    completeness = sum(1 for value in candidate.values() if value)
    if completeness == 0:
        return None

    normalized_label = normalize_label(section.get("label", ""))
    return {
        **candidate,
        "source_section": normalized_label or None,
        "confidence_score": 0.9 if completeness == 3 else 0.75 if completeness == 2 else 0.6,
        "_priority": ADDRESS_SECTION_PRIORITY.get(normalized_label, 99),
        "_completeness": completeness,
    }


def extract_geographic_context(address_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministically extract city/state/country from address sections only.
    Prefers permanent address over communication address and ignores unrelated
    repeated OCR fragments by parsing row-level label/value pairs.
    """
    candidates = []
    for section in address_sections or []:
        candidate = _extract_candidate(section)
        if candidate:
            candidates.append(candidate)

    if not candidates:
        return {"geographic_context": None, "confidence_score": 0.0}

    candidates.sort(key=lambda item: (item["_priority"], -item["_completeness"]))
    best = candidates[0]
    geographic_context = {
        "city": best.get("city"),
        "state": best.get("state"),
        "country": best.get("country"),
    }
    geographic_context = {k: v for k, v in geographic_context.items() if v is not None}

    return {
        "geographic_context": geographic_context or None,
        "confidence_score": best.get("confidence_score", 0.0),
        "source_section": best.get("source_section"),
    }
