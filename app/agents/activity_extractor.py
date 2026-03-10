from typing import List, Dict, Any
import uuid
import re

def extract_activities(normalized_rows: List[List[str]]) -> Dict[str, Any]:
    """
    Extract activities as a collection using normalized rows. No ranking inferred.
    """
    entries = []
    confidence = 0.90
    
    current_entry = None
    in_table = False
    
    for row in normalized_rows:
        if not row: continue
        text = " ".join(row).strip()
        lower_line = text.lower()
        
        # Header detection for activities table
        if "activity" in lower_line and ("category" in lower_line or "participation" in lower_line):
            in_table = True
            continue
            
        # Parse table row: ["Debate Club", "Co-Curricular", "2 Years", "State"]
        if in_table and len(row) >= 2:
            clean_name = row[0].strip("-* ")
            name_lower = clean_name.lower()
            activity_type = "other"
            if "club" in name_lower or "sport" in name_lower or "music" in name_lower or "art" in name_lower:
                activity_type = "extracurricular"
            elif "olympiad" in name_lower or "competition" in name_lower or "research" in name_lower:
                activity_type = "co_curricular"
            elif "president" in name_lower or "captain" in name_lower or "founder" in name_lower or "lead" in name_lower:
                activity_type = "leadership"
                
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "activity_type": activity_type,
                "category": row[1].strip() if len(row) > 1 else None,
                "activity_name": clean_name or "Unknown Activity",
                "level": row[3].strip() if len(row) > 3 else None,
                "duration": row[2].strip() if len(row) > 2 else None,
                "description_raw": "",
                "upload_flag": False,
                "confidence_score": confidence
            })
            continue

        # non-table list processing
        if text.startswith("-") or text.startswith("*") or "activity:" in lower_line or re.match(r'^\d+\.', text):
            in_table = False
            if current_entry:
                entries.append(current_entry)
            
            clean_name = text.strip("-* ").split(":", 1)[-1].strip()
            if len(row) > 1 and "activity" in row[0].lower():
                clean_name = row[1].strip("-* ")
                
            name_lower = clean_name.lower()
            activity_type = "other"
            if "club" in name_lower or "sport" in name_lower or "music" in name_lower or "art" in name_lower:
                activity_type = "extracurricular"
            elif "olympiad" in name_lower or "competition" in name_lower or "research" in name_lower:
                activity_type = "co_curricular"
            elif "president" in name_lower or "captain" in name_lower or "founder" in name_lower or "lead" in name_lower:
                activity_type = "leadership"
            
            current_entry = {
                "entry_id": str(uuid.uuid4()),
                "activity_type": activity_type,
                "category": None,
                "activity_name": clean_name or "Unknown Activity",
                "level": None,
                "duration": None,
                "description_raw": "",
                "upload_flag": False,
                "confidence_score": confidence
            }
            continue
            
        if current_entry and not in_table:
            for i, cell in enumerate(row):
                lower_cell = cell.lower()
                next_val = row[i+1].strip() if i + 1 < len(row) else cell.split(":", 1)[1].strip() if ":" in cell else ""
                
                if "level" in lower_cell:
                    current_entry["level"] = next_val
                elif "duration" in lower_cell:
                    current_entry["duration"] = next_val
                elif "category" in lower_cell:
                    cat = next_val
                    current_entry["category"] = cat
                    
                    cat_lower = cat.lower()
                    if "club" in cat_lower or "sport" in cat_lower or "music" in cat_lower or "art" in cat_lower:
                        current_entry["activity_type"] = "extracurricular"
                    elif "olympiad" in cat_lower or "competition" in cat_lower or "research" in cat_lower:
                        current_entry["activity_type"] = "co_curricular"
                    elif "leadership" in cat_lower or "president" in cat_lower or "captain" in cat_lower or "founder" in cat_lower:
                        current_entry["activity_type"] = "leadership"
                else:
                    if i == 0 and not ":" in cell:
                        current_entry["description_raw"] += cell + " "

    if current_entry:
        entries.append(current_entry)
        
    for entry in entries:
        entry["description_raw"] = entry["description_raw"].strip()

    return {
        "activity_entries": entries,
        "confidence_score": confidence
    }
