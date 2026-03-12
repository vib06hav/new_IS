from typing import List, Dict, Any
import uuid
import re

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

    # Hints for routing (JEE hints should be more specific to avoid overlap with SAT-Math)
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
                if not any(e["test_name"] == header_name for e in entries):
                    new_e = create_entry(t_type)
                    entries.append(new_e)
                    current_entry = new_e
                else:
                    for e in entries:
                        if e["test_name"] == header_name:
                            current_entry = e
                            break

        if not entries:
            continue

        # 2. Determine Row Context (SAT or JEE?)
        # If the row has clear SAT/JEE keywords, we prefer that entry for all cells in this row
        row_context_entry = current_entry
        for test_type, hints in ROUTING_HINTS.items():
            if any(h in lower_row for h in hints):
                target_name = "SAT" if test_type == "SAT" else "JEE Mains"
                for e in entries:
                    if e["test_name"] == target_name:
                        row_context_entry = e
                        break
                # Once we find a clear hint, we stop checking (prioritizing JEE hints as they are first)
                break

        # 3. Extract Scores from Row Cells
        for cell in row:
            clean_cell = cell.strip()
            if not clean_cell: continue
            
            match = re.search(r"(.*?)\s+([\d\.]+)$", clean_cell)
            if match:
                label, val = match.groups()
                label = label.strip().lower()
            else:
                label = clean_cell.lower()
                val = None

            target_entry = row_context_entry

            # Handle JEE anomalies first
            if "jee" in target_entry["test_name"].lower():
                if "test date" in label and val:
                    # Capture percentile from "Test Date 99.39"
                    target_entry["total_score"] = val
                    continue

            # Mapping
            if "total score" in label:
                if val: 
                    target_entry["total_score"] = val
                elif len(row) > 1:
                    idx = row.index(cell)
                    if idx + 1 < len(row):
                        next_val = row[idx+1].strip()
                        if re.match(r"^[\d\.]+$", next_val):
                             target_entry["total_score"] = next_val
            elif "test date" in label and not target_entry["test_date"]:
                if val: target_entry["test_date"] = val
            elif any(kw in label for kw in ["reading", "math", "physics", "chemistry", "percentile"]):
                if val:
                    target_entry["sectional_scores"].append({
                        "label": label.title(),
                        "raw_score": val
                    })
                elif len(row) > 1:
                    idx = row.index(cell)
                    if idx + 1 < len(row):
                        next_val = row[idx+1].strip()
                        if re.match(r"^[\d\.]+$", next_val):
                            target_entry["sectional_scores"].append({
                                "label": label.title(),
                                "raw_score": next_val
                            })

    # Final cleanup
    final_entries = [e for e in entries if e["total_score"] or e["sectional_scores"]]
            
    return {
        "test_entries": final_entries,
        "confidence_score": confidence
    }
