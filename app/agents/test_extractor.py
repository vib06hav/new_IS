import uuid
import re
import logging
from typing import List, Dict, Any, Tuple
from app.utils.form_vocab import is_stop_word, TEST_SECTION_MAP, TEST_METADATA_KEYS

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

def extract_test_records(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardized Test Extractor (Vocabulary-Driven).
    Uses Y-clustering to reconstruct rows and Label-Registry for field mapping.
    """
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
        
    if has_jee: entries.append(create_entry("JEE Mains"))
    if has_sat: entries.append(create_entry("SAT"))
    
    if not entries:
        return {"test_entries": [], "confidence_score": 0.0}

    # --- 1. Y-Clustering into Rows ---
    page_blocks = sorted(blocks, key=lambda b: (b["page"], -b["bbox"][3]))
    rows = []
    cur_row = []
    cur_y = None
    cur_page = None

    for b in page_blocks:
        p = b["page"]
        cy = (b["bbox"][1] + b["bbox"][3]) / 2
        
        if cur_y is None or (p == cur_page and abs(cy - cur_y) < 25):
            cur_row.append(b)
            cur_y = cy
            cur_page = p
        else:
            rows.append(sorted(cur_row, key=lambda x: x["bbox"][0]))
            cur_row = [b]
            cur_y = cy
            cur_page = p
    if cur_row:
        rows.append(sorted(cur_row, key=lambda x: x["bbox"][0]))

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

    # --- 2. Process each Row ---
    for row in rows:
        row_text = " ".join([normalize_text(b["text"]) for b in row])
        
        target_test = "JEE Mains"
        if any(kw in row_text for kw in ["reading", "sat", "evidence-based"]):
            target_test = "SAT"
        
        # Keep track of indices that were already used as labels or values
        # to avoid double-dipping in Joined cells
        
        for idx, b in enumerate(row):
            b_text_norm = normalize_text(b["text"])
            label_p, val_p = _split_cell(b_text_norm)
            
            canonical = _match_label(label_p)
            final_val = val_p
            
            # If no joined value, look right
            if canonical and not final_val:
                if idx + 1 < len(row):
                    next_block = row[idx+1]
                    numeric = _extract_numeric(next_block["text"])
                    if numeric and not is_stop_word(next_block["text"]):
                        final_val = numeric

            if final_val and canonical:
                # Heuristic: If label is __date__ but value looks like a score (>=50 or has decimal),
                # and we don't have a total_score yet, treat it as __total__ if it is JEE.
                if canonical == "__date__" and target_test == "JEE Mains":
                    try:
                        num_val = float(final_val)
                        if num_val > 50:
                            canonical = "__total__"
                    except: pass
                assign_val(target_test, canonical, final_val)

    # Final cleanup: remove empty entries
    final = [e for e in entries if e["total_score"] or e["sectional_scores"]]
    
    return {
        "test_entries": final,
        "confidence_score": confidence
    }
