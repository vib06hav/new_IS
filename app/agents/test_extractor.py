from typing import List, Dict, Any
import uuid
import re
import logging

logger = logging.getLogger(__name__)

def extract_test_records(normalized_rows: List[List[str]]) -> Dict[str, Any]:
    """
    Extract standardized tests as a collection using normalized rows.
    Handles specific SAT and JEE Main layouts with row-level context.
    """
    entries = []
    confidence = 0.90
    
    # Common test labels to trigger capture
    TEST_HEADERS = [
        ("SAT", ["scholastic assessment test", "sat details"]),
        ("JEE", ["joint entrance examination", "jee main details", "jee mains"])
    ]

    # Hints for routing
    ROUTING_HINTS = {
        "JEE": ["physics", "chemistry", "percentile", "roll number", "rank"],
        "SAT": ["reading", "writing", "math"]
    }

    def create_entry(test_type: str) -> Dict[str, Any]:
        return {
            "entry_id": str(uuid.uuid4()),
            "test_name": "SAT" if test_type == "SAT" else "JEE Mains",
            "test_date": None,
            "total_score": None,
            "sectional_scores": [],
            "percentile": None,
            "rank": None,
            "result_status": "available",
            "confidence_score": confidence
        }

    current_entry = None

    for row in normalized_rows:
        row_text = " ".join(row)
        lower_row = row_text.lower()

        # 1. Detect Test Transitions (Section Headers)
        found_signals = []
        for t_type, keywords in TEST_HEADERS:
            for kw in keywords:
                for m in re.finditer(re.escape(kw), lower_row):
                    found_signals.append((m.start(), t_type))
        
        found_signals.sort()
        if found_signals:
            for _, t_type in found_signals:
                header_name = "SAT" if t_type == "SAT" else "JEE Mains"
                # Find or Create entry
                target_e = None
                for e in entries:
                    if e["test_name"] == header_name:
                        target_e = e
                        break
                if not target_e:
                    target_e = create_entry(t_type)
                    entries.append(target_e)
                current_entry = target_e

        if not entries:
            continue

        # 2. Determine Row Context (SAT or JEE?)
        row_context_entry = current_entry
        for test_type, hints in ROUTING_HINTS.items():
            if any(h in lower_row for h in hints):
                target_name = "SAT" if test_type == "SAT" else "JEE Mains"
                for e in entries:
                    if e["test_name"] == target_name:
                        row_context_entry = e
                        break
                break

        # 3. Extract Scores from Row Cells
        for cell in row:
            clean_cell = cell.strip()
            if not clean_cell: continue
            
            # Robust label-value extraction from cell
            # Matches "Label 99.0" or "Label: 99.0" or "Label 99.0%"
            match = re.search(r"(.*?)\s*[:\-–]?\s*([\d\.]+)%?$", clean_cell)
            if match:
                label, val = match.groups()
                label = label.strip().lower()
            else:
                label = clean_cell.lower()
                val = None

            target_entry = row_context_entry

            # A. Total Score / Test Date Capture
            # If we match a total score keyword, we set total_score
            # We use more specific keywords for JEE to avoid matching "Physics Percentile"
            total_score_kws = ["total score", "test date", "aggregate nta score", "jee mains percentile"]
            if any(kw in label for kw in total_score_kws):
                ext_val = val
                if not ext_val and len(row) > 1:
                    idx = row.index(cell)
                    if idx + 1 < len(row):
                        next_val = row[idx+1].strip()
                        num_match = re.search(r"([\d\.]+)%?$", next_val)
                        if num_match:
                             ext_val = num_match.group(1)
                
                if ext_val:
                    target_entry["total_score"] = ext_val
                    # For JEE, we only want to set total_score here, not add a sectional entry
                    if "jee" in target_entry["test_name"].lower():
                         continue

            # B. Sectional Score Mapping
            # Priority: Specific subjects first
            section_map = [
                ("math", "Maths Percentile"),
                ("physics", "Physics Percentile"),
                ("chemistry", "Chemistry Percentile"),
                ("reading", "Reading/Writing"),
                ("writing", "Reading/Writing"),
                ("rank", "Sectional Rank"),     # Specific rank keywords
                ("percentile", "Sectional Percentile") # Fallback percentile
            ]

            matched_section = None
            for kw, formal_label in section_map:
                if kw in label:
                    matched_section = formal_label
                    break
            
            if matched_section:
                final_val = val
                if not final_val and len(row) > 1:
                    idx = row.index(cell)
                    if idx + 1 < len(row):
                        next_val = row[idx+1].strip()
                        num_match = re.search(r"([\d\.]+)%?$", next_val)
                        if num_match:
                            final_val = num_match.group(1)
                
                if final_val:
                    # Deduplicate in case of duplicate blocks/fuzzy matching
                    if not any(s["label"] == matched_section for s in target_entry["sectional_scores"]):
                        target_entry["sectional_scores"].append({
                            "label": matched_section,
                            "raw_score": final_val
                        })

    # Final cleanup
    # Ensure JEE always has subjects if possible
    for e in entries:
        if e["test_name"] == "JEE Mains" and len(e["sectional_scores"]) < 3:
            # If we have a total_score but few sectional scores, maybe one of them was the total?
            # We don't have enough info to re-assign, but at least we captured what we could.
            pass

    final_entries = [e for e in entries if e["total_score"] or e["sectional_scores"]]
            
    return {
        "test_entries": final_entries,
        "confidence_score": confidence
    }
