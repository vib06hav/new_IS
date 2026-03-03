from typing import List, Dict, Any
import uuid

def extract_activities(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract activities as a collection. No ranking inferred.
    """
    entries = []
    confidence = 0.90
    
    current_entry = None
    
    for block in section_blocks:
        text = block.get("text", "")
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Simple heuristic: bullet points or "Activity:" implies new activity
            if line.startswith("-") or line.startswith("*") or "activity:" in line.lower():
                if current_entry:
                    entries.append(current_entry)
                
                clean_name = line.strip("-* ").split(":", 1)[-1].strip()
                
                current_entry = {
                    "entry_id": str(uuid.uuid4()),
                    "category": None,
                    "activity_name": clean_name or "Unknown Activity",
                    "level": None,
                    "duration": None,
                    "description_raw": "",
                    "upload_flag": False,
                    "confidence_score": confidence
                }
            elif current_entry:
                lower_line = line.lower()
                if "level:" in lower_line:
                    current_entry["level"] = line.split(":", 1)[1].strip()
                elif "duration:" in lower_line:
                    current_entry["duration"] = line.split(":", 1)[1].strip()
                elif "category:" in lower_line:
                    current_entry["category"] = line.split(":", 1)[1].strip()
                else:
                    current_entry["description_raw"] += line + " "

    if current_entry:
        entries.append(current_entry)
        
    for entry in entries:
        entry["description_raw"] = entry["description_raw"].strip()

    return {
        "activity_entries": entries,
        "confidence_score": confidence
    }
