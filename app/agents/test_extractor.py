import uuid
import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from app.utils.form_vocab import is_stop_word, TEST_SECTION_MAP, TEST_METADATA_KEYS
from app.utils.row_grouper import group_blocks_into_rows

logger = logging.getLogger(__name__)

def _safe_float(s: str) -> float:
    if not s: return None
    try:
        # Remove commas, % etc
        clean = re.sub(r"[^\d\.]", "", s)
        return float(clean)
    except:
        return None

def _extract_numeric(text: str) -> str:
    """Extracts a score-like number from text (e.g. '97.69')."""
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%?$", text.strip())
    if match:
        return match.group(1)
    return None


def _looks_like_date(text: str) -> bool:
    clean = text.strip()
    return bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", clean) or re.search(r"\b\d{2}/\d{2}/\d{4}\b", clean))

def _split_cell(text: str) -> Tuple[str, str]:
    """Splits a cell into potential label and value."""
    clean = text.strip()
    # 1. Joined case: 'Physics Percentile 96.67'
    # Use lookahead to ensure at least one digit is present (avoids capturing just ".")
    match = re.search(r"^(.*?)\s*[:\-–]?\s*((?=.*\d)[\d\.]+)%?$", clean)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return clean, None

def _match_label(text: str) -> str:
    """Matches a string to a canonical field label from the registry."""
    clean = text.lower().strip()
    if not clean: return None
    
    # Try exact match first
    if clean in TEST_SECTION_MAP:
        return TEST_SECTION_MAP[clean]
    
    # Try partial match (greedy)
    for kw, formal in TEST_SECTION_MAP.items():
        if kw == clean or (len(kw) > 3 and kw in clean):
            return formal
    return None

def _extract_test_records_with_rows(
    blocks: List[Dict[str, Any]],
    row_blocks: List[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    if not blocks:
        return {"test_entries": [], "confidence_score": 0.0}

    confidence = 0.90
    entries = []

    def normalize_text(t):
        return " ".join(t.lower().split())

    full_text_norm = " ".join([normalize_text(b["text"]) for b in blocks])

    jee_kws = ["jee", "joint entrance", "nta score", "physics percentile"]
    sat_kws = ["sat", "scholastic assessment", "reading and writing", "reading score"]

    has_jee = any(kw in full_text_norm for kw in jee_kws)
    has_sat = any(kw in full_text_norm for kw in sat_kws)

    def create_entry(name: str) -> Dict:
        return {
            "entry_id": str(uuid.uuid4()),
            "test_name": name,
            "test_date": None,
            "total_score": None,
            "sectional_scores": [],
            "percentile": None,
            "rank": None,
            "result_status": "available",
            "confidence_score": confidence,
        }

    if has_jee:
        entries.append(create_entry("JEE Mains"))
    if has_sat:
        entries.append(create_entry("SAT"))

    if not entries:
        return {"test_entries": [], "confidence_score": 0.0}

    def assign_val(test_name: str, key: str, val: str):
        for e in entries:
            if e["test_name"] == test_name:
                if key == "__total__":
                    e["total_score"] = val
                elif key == "__date__":
                    e["test_date"] = val
                elif key == "__roll__":
                    pass
                else:
                    if not any(s["label"] == key for s in e["sectional_scores"]):
                        e["sectional_scores"].append({"label": key, "raw_score": val})

    for row in row_blocks:
        row_text = " ".join([normalize_text(b["text"]) for b in row])

        target_test = "JEE Mains"
        if any(kw in row_text for kw in ["reading", "sat", "evidence-based"]):
            target_test = "SAT"

        for idx, b in enumerate(row):
            b_text_norm = normalize_text(b["text"])
            label_p, val_p = _split_cell(b_text_norm)

            canonical = _match_label(label_p)
            final_val = val_p

            if canonical and not final_val:
                if idx + 1 < len(row):
                    next_block = row[idx + 1]
                    if canonical == "__date__":
                        if _looks_like_date(next_block["text"]):
                            final_val = next_block["text"].strip()
                    else:
                        numeric = _extract_numeric(next_block["text"])
                        if numeric and not is_stop_word(next_block["text"]):
                            final_val = numeric

            if final_val and canonical:
                assign_val(target_test, canonical, final_val)

    final = [e for e in entries if e["total_score"] or e["sectional_scores"]]
    return {
        "test_entries": final,
        "confidence_score": confidence
    }


def extract_test_records(
    blocks: List[Dict[str, Any]],
    rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Standardized Test Extractor (Vocabulary-Driven).
    Uses Y-clustering to reconstruct rows and Label-Registry for field mapping.
    """
    provided_rows = [row.get("blocks", []) for row in rows if row.get("blocks")] if rows is not None else None
    if provided_rows is not None:
        result = _extract_test_records_with_rows(blocks, provided_rows)
        if result.get("test_entries"):
            return result

    fallback_rows = group_blocks_into_rows(blocks, y_threshold=25)
    return _extract_test_records_with_rows(blocks, fallback_rows)
