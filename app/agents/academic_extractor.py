from typing import List, Dict, Any
import uuid

def extract_academic_records(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract academic records as a collection.
    No hardcoded keys for Class 9/10/12. Emits list of academic entries.
    """
    entries = []
    confidence = 0.85
    
    current_entry = None
    
    for block in section_blocks:
        text = block.get("text", "")
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Heuristic for new academic entry (e.g., "Grade 10", "Class 12", "Year 2024")
            if "grade" in line.lower() or "class" in line.lower() or "year " in line.lower():
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "entry_id": str(uuid.uuid4()),
                    "academic_level": line,
                    "board_name": None,
                    "academic_year": None,
                    "marking_scheme_raw": None,
                    "grading_mode": "unknown",
                    "score_raw": None,
                    "predicted_score_raw": None,
                    "subject_entries": [],
                    "component_tags": [],
                    "confidence_score": confidence
                }
            elif current_entry:
                lower_line = line.lower()
                if "board:" in lower_line:
                    current_entry["board_name"] = line.split(":", 1)[1].strip()
                elif "percentage:" in lower_line or "cgpa:" in lower_line:
                    parts = line.split(":", 1)
                    current_entry["score_raw"] = parts[1].strip()
                    current_entry["marking_scheme_raw"] = parts[0].strip()
                    current_entry["grading_mode"] = "percentage" if "percentage" in lower_line else "cgpa"
                elif ":" in line:
                    # Assume subject: score
                    parts = line.split(":", 1)
                    current_entry["subject_entries"].append({
                        "subject_name": parts[0].strip(),
                        "score_raw": parts[1].strip(),
                        "predicted_score_raw": None,
                        "component_tag": None
                    })
                    
    if current_entry:
        entries.append(current_entry)
        
    return {
        "academic_entries": entries,
        "confidence_score": confidence
    }
