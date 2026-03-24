from typing import List, Dict, Any, Optional

from app.utils.block_deduper import dedupe_near_overlapping_blocks
from app.utils.text_normalization import normalize_label


def extract_personal_info(
    section_blocks: List[Dict[str, Any]],
    parent_sections: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Extracts labeled personal fields strictly based on layout bounding boxes.
    Parent details are section-aware and should be passed in via section metadata
    rather than rediscovered from stripped header blocks.
    """
    identifiers = {
        "full_name": None,
        "date_of_birth": None,
        "preferred_major": None,
        "family_background": {
            "father": {"name": None, "education": None, "field_of_employment": None, "organization": None, "designation": None},
            "mother": {"name": None, "education": None, "field_of_employment": None, "organization": None, "designation": None}
        },
        "declared_preferences": {},
        "demographic_flags": {}
    }

    confidence = 0.85
    section_blocks = dedupe_near_overlapping_blocks(section_blocks)
    parent_sections = parent_sections or []

    def find_value_for_label(label_block: Dict[str, Any], blocks: List[Dict[str, Any]]) -> str:
        """Find the nearest block to the right on the same row."""
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

    # First pass: generic personal details
    for block in section_blocks:
        text = block.get("text", "").strip()
        lower_text = normalize_label(text)

        if ":" in text and len(text.split(":")) > 1:
            val = text.split(":", 1)[1].strip() or find_value_for_label(block, section_blocks)
        else:
            val = find_value_for_label(block, section_blocks)

        if not val:
            continue

        if lower_text in {"name", "full name"}:
            if not identifiers["full_name"] and "father" not in val.lower() and "mother" not in val.lower():
                identifiers["full_name"] = val
        elif lower_text in {"date of birth", "dob"}:
            if not identifiers["date_of_birth"]:
                identifiers["date_of_birth"] = val
        elif lower_text in {"major", "intended major", "preferred major"}:
            identifiers["declared_preferences"]["major"] = val
            identifiers["preferred_major"] = val
        elif lower_text == "first generation":
            identifiers["demographic_flags"]["first_generation"] = val.lower() in {"yes", "true"}

    # Second pass: section-aware parent details
    parent_labels = {
        "name", "highest degree attained", "education",
        "field of employment", "occupation", "organization", "designation",
        "mobile number", "email address", "date of birth",
        "nationality", "educational institute (last attended)",
    }

    for parent_section in parent_sections:
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

            val = find_value_for_label(block, parent_blocks)
            if not val:
                continue

            if clean_label == "name":
                identifiers["family_background"][context]["name"] = val
            elif clean_label in {"highest degree attained", "education"}:
                identifiers["family_background"][context]["education"] = val
            elif clean_label in {"field of employment", "occupation"}:
                identifiers["family_background"][context]["field_of_employment"] = val
            elif clean_label == "organization":
                identifiers["family_background"][context]["organization"] = val
            elif clean_label == "designation":
                identifiers["family_background"][context]["designation"] = val

    return {
        "identifiers": identifiers,
        "confidence_score": confidence
    }
