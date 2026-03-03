from typing import List, Dict, Any
import uuid

def extract_test_records(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract standardized tests as a collection.
    """
    entries = []
    confidence = 0.85
    
    current_entry = None
    
    for block in section_blocks:
        text = block.get("text", "")
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            lower_line = line.lower()
            
            # Heuristic for new test
            if "test:" in lower_line or "exam:" in lower_line or line.upper() in ["SAT", "ACT", "IELTS", "TOEFL", "JEE"]:
                if current_entry:
                    entries.append(current_entry)
                
                test_name = line.split(":", 1)[1].strip() if ":" in line else line
                
                current_entry = {
                    "entry_id": str(uuid.uuid4()),
                    "test_name": test_name,
                    "test_date": None,
                    "total_score": None,
                    "sectional_scores": [],
                    "percentile": None,
                    "rank": None,
                    "result_status": "available",
                    "confidence_score": confidence
                }
            elif current_entry:
                if "date:" in lower_line:
                    current_entry["test_date"] = line.split(":", 1)[1].strip()
                elif "total:" in lower_line or "score:" in lower_line:
                    current_entry["total_score"] = line.split(":", 1)[1].strip()
                elif "status:" in lower_line:
                    current_entry["result_status"] = line.split(":", 1)[1].strip().lower()
                elif ":" in line:
                    parts = line.split(":", 1)
                    current_entry["sectional_scores"].append({
                        "label": parts[0].strip(),
                        "raw_score": parts[1].strip()
                    })
                    
    if current_entry:
        entries.append(current_entry)
        
    return {
        "test_entries": entries,
        "confidence_score": confidence
    }
