from typing import Any, Dict, List

from app.utils.block_deduper import dedupe_near_overlapping_blocks
from app.utils.text_normalization import normalize_label


def _empty_family_background() -> Dict[str, Dict[str, Any]]:
    return {
        "father": {
            "name": None,
            "education": None,
            "field_of_employment": None,
            "organization": None,
            "designation": None,
        },
        "mother": {
            "name": None,
            "education": None,
            "field_of_employment": None,
            "organization": None,
            "designation": None,
        },
    }


def _find_value_for_label(label_block: Dict[str, Any], blocks: List[Dict[str, Any]]) -> str:
    label_y0, label_y1 = label_block["bbox"][1], label_block["bbox"][3]
    label_x1 = label_block["bbox"][2]
    page = label_block["page"]

    candidates = []
    for block in blocks:
        if block["page"] != page or block == label_block:
            continue

        block_y0, block_y1 = block["bbox"][1], block["bbox"][3]
        block_x0 = block["bbox"][0]
        vertical_overlap = min(label_y1, block_y1) - max(label_y0, block_y0)
        if (vertical_overlap > 0 or abs(label_y0 - block_y0) < 5) and block_x0 > label_x1:
            candidates.append(block)

    candidates.sort(key=lambda block: block["bbox"][0])
    label_lower = normalize_label(label_block["text"])
    for candidate in candidates:
        candidate_text_lower = normalize_label(candidate["text"])
        if candidate_text_lower != label_lower and candidate_text_lower not in {"organization", "designation"}:
            return candidate["text"].strip()

    return None


def extract_family_background(parent_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    family_background = _empty_family_background()
    confidence = 0.85
    parent_labels = {
        "name", "highest degree attained", "education",
        "field of employment", "occupation", "organization", "designation",
        "mobile number", "email address", "date of birth",
        "nationality", "educational institute (last attended)",
    }

    for parent_section in parent_sections or []:
        section_label = normalize_label(parent_section.get("label", ""))
        if section_label == "father details":
            context = "father"
        elif section_label == "mother details":
            context = "mother"
        else:
            continue

        parent_blocks = dedupe_near_overlapping_blocks(parent_section.get("blocks", []))
        for block in parent_blocks:
            text = block.get("text", "").strip()
            clean_label = normalize_label(text).strip(" -:")
            if clean_label not in parent_labels:
                continue

            val = _find_value_for_label(block, parent_blocks)
            if not val:
                continue

            if clean_label == "name":
                family_background[context]["name"] = val
            elif clean_label in {"highest degree attained", "education"}:
                family_background[context]["education"] = val
            elif clean_label in {"field of employment", "occupation"}:
                family_background[context]["field_of_employment"] = val
            elif clean_label == "organization":
                family_background[context]["organization"] = val
            elif clean_label == "designation":
                family_background[context]["designation"] = val

    return {
        "family_background": family_background,
        "confidence_score": confidence,
    }
