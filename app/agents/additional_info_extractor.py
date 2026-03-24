from typing import List, Dict, Any, Optional

from app.utils.text_normalization import normalize_label


def extract_additional_info(
    section_blocks: List[Dict[str, Any]],
    all_blocks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    preferred_major: Optional[str] = None
    confidence = 0.9

    if not section_blocks:
        return {"preferred_major": None, "confidence_score": 0.0}

    search_blocks = all_blocks if all_blocks is not None else section_blocks

    for block in section_blocks:
        label = normalize_label(block.get("text", ""))
        if label != "preferred major":
            continue

        label_y0, label_y1 = block["bbox"][1], block["bbox"][3]
        label_x1 = block["bbox"][2]
        page = block["page"]

        candidates = []
        for candidate in search_blocks:
            if candidate["page"] != page or candidate == block:
                continue

            c_y0, c_y1 = candidate["bbox"][1], candidate["bbox"][3]
            vertical_overlap = min(label_y1, c_y1) - max(label_y0, c_y0)
            if (vertical_overlap > 0 or abs(label_y0 - c_y0) < 5) and candidate["bbox"][0] > label_x1:
                candidates.append(candidate)

        candidates.sort(key=lambda item: item["bbox"][0])
        for candidate in candidates:
            text = candidate.get("text", "").strip()
            if text:
                preferred_major = text
                break

        if preferred_major:
            break

    return {
        "preferred_major": preferred_major,
        "confidence_score": confidence if preferred_major else 0.0,
    }
