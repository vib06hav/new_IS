from typing import List, Dict, Any

def extract_personal_info(section_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extracts labeled personal fields strictly based on labels.
    """
    identifiers = {
        "full_name": None,
        "date_of_birth": None,
        "declared_preferences": {},
        "demographic_flags": {}
    }
    
    confidence = 0.85
    
    for block in section_blocks:
        text = block.get("text", "")
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            lower_line = line.lower()
            
            # Label-based extraction (deterministic)
            if "name:" in lower_line or "full name:" in lower_line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    identifiers["full_name"] = parts[1].strip()
            elif "dob:" in lower_line or "date of birth:" in lower_line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    identifiers["date_of_birth"] = parts[1].strip()
            elif "major:" in lower_line or "intended major:" in lower_line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    identifiers["declared_preferences"]["major"] = parts[1].strip()
            elif "first generation:" in lower_line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    val = parts[1].strip().lower()
                    identifiers["demographic_flags"]["first_generation"] = (val == "yes" or val == "true")
                    
    return {
        "identifiers": identifiers,
        "confidence_score": confidence
    }
