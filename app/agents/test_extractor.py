from typing import List, Dict, Any
import uuid

def extract_test_records(normalized_rows: List[List[str]]) -> Dict[str, Any]:
    """
    Extract standardized tests as a collection using normalized rows.
    """
    entries = []
    confidence = 0.85
    
    current_entry = None
    in_table = False
    
    for row in normalized_rows:
        if not row: continue
        text = " ".join(row).strip()
        lower_line = text.lower()
        
        # Header detection for tests section
        if "test" in lower_line and "score" in lower_line and "date" in lower_line:
            in_table = True
            continue
            
        # Break test extraction if reaching other sections in case of bleed
        if "essay" in lower_line or "declaration" in lower_line or "activity" in lower_line:
            break
            
        # Parse table row for sectional scores (e.g. ["Mathematics", "800"])
        if in_table and len(row) >= 2 and current_entry:
            if any(char.isdigit() for char in row[1]):
                current_entry["sectional_scores"].append({
                    "label": row[0].strip(),
                    "raw_score": row[1].strip()
                })
                continue
            
        # Heuristic for new test
        if "test:" in lower_line or "exam:" in lower_line or any(test in text.upper() for test in ["SAT", "ACT", "IELTS", "TOEFL", "JEE"]):
            in_table = False
            if current_entry:
                entries.append(current_entry)
            
            test_val = text.split(":", 1)[1].strip() if ":" in text else text.strip()
            if len(row) > 1 and "test" in row[0].lower():
                test_val = row[1]
                
            current_entry = {
                "entry_id": str(uuid.uuid4()),
                "test_name": test_val,
                "test_date": None,
                "total_score": None,
                "sectional_scores": [],
                "percentile": None,
                "rank": None,
                "result_status": "available",
                "confidence_score": confidence
            }
            continue

        if current_entry and not in_table:
            for i, cell in enumerate(row):
                lower_cell = cell.lower()
                next_val = row[i+1].strip() if i + 1 < len(row) else cell.split(":", 1)[1].strip() if ":" in cell else ""
                
                if not next_val and i == len(row) - 1:
                    continue
                    
                if "date" in lower_cell:
                    current_entry["test_date"] = next_val
                elif "total" in lower_cell or "score:" in lower_cell:
                    current_entry["total_score"] = next_val
                elif "status" in lower_cell:
                    current_entry["result_status"] = next_val.lower()
                elif ":" in cell:
                    parts = cell.split(":", 1)
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
