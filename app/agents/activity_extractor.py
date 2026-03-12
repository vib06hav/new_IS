from typing import List, Dict, Any
import uuid
import re

def extract_activities(normalized_rows: List[List[str]], category_hint: str = "other") -> Dict[str, Any]:
    """
    Extract activities using a Hybrid Scoring approach.
    - Uses regex for Duration and Level.
    - Uses 'Greedy Sweep-up' for descriptions.
    - Stores raw text in original_row_content as a safety net.
    """
    entries = []
    confidence = 0.90
    
    # regex for Duration: looks for digits + time units or a standalone small digit
    # e.g. "3 years", "2 months", "4"
    DURATION_PATTERN = re.compile(r'(\d+\s*(?:years?|yrs?|months?|weeks?)|^\s*\d{1,2}\s*$)', re.IGNORECASE)
    
    # Semantic anchors for Level
    LEVEL_ANCHORS = ["national", "international", "state", "zonal", "intra", "district", "personal", "grade", "school", "community"]

    def clean_text(t):
        if not t: return ""
        return re.sub(r'^(?:\d+\.|\w+\s+\d+:?)\s*', '', t.strip()).strip()

    def is_header(row):
        row_joined = " ".join(row).lower()
        header_keywords = ["activity", "participation", "years", "position", "responsibility", "roles", "curricular", "extra", "level", "achievement", "duration"]
        match_count = sum(1 for kw in header_keywords if kw in row_joined)
        return match_count >= 2

    for row in normalized_rows:
        if not row: continue
        if is_header(row): continue
        
        raw_content = " | ".join(row).strip()
        
        # Determine Activity Name (Identity)
        # Default strategy: first cell is likely name, unless it's a numeric sentinel
        name_candidate = ""
        other_cells = []
        
        if len(row) > 1 and re.match(r'^\d+\.?$', row[0].strip()):
            name_candidate = row[1]
            other_cells = row[2:]
        elif len(row) > 0:
            name_candidate = row[0]
            other_cells = row[1:]
        else:
            continue

        entry = {
            "entry_id": str(uuid.uuid4()),
            "activity_type": category_hint,
            "category": None,
            "activity_name": clean_text(name_candidate),
            "level": None,
            "duration": None,
            "description_raw": "",
            "original_row_content": raw_content,
            "upload_flag": False,
            "confidence_score": confidence
        }

        description_parts = []
        
        # Tagging remaining cells
        for cell in other_cells:
            cell_stripped = cell.strip()
            if not cell_stripped: continue
            
            # Check for Duration
            if not entry["duration"] and DURATION_PATTERN.search(cell_stripped):
                # Ensure it's not a False Positive (like a Grade level)
                if not any(anchor in cell_stripped.lower() for anchor in ["grade", "level"]):
                    entry["duration"] = cell_stripped
                    continue
            
            # Check for Level
            if not entry["level"] and any(anchor in cell_stripped.lower() for anchor in LEVEL_ANCHORS):
                entry["level"] = cell_stripped
                continue
            
            # Greedy Sweep-up: Anything else is description
            description_parts.append(cell_stripped)

        entry["description_raw"] = " ".join(description_parts).strip()
        
        # Noise Filtering
        name_val = str(entry["activity_name"] or "").lower()
        if len(name_val) > 1:
            noise_patterns = [
                r'^additional information.*', r'^references.*', r'^declaration.*', r'^designation.*',
                r'^organization.*', r'^preferred major.*', r'^where did you hear.*', r'^financial aid.*',
                r'^school$', r'^friends/family.*', r'^activity$', r'^position$', r'^in what capacity.*',
                r'^will you be applying.*', r'^references.*', r'^name.*', r'^email.*', r'^mobile.*'
            ]
            if not any(re.search(p, name_val) for p in noise_patterns):
                entries.append(entry)

    return {
        "activity_entries": entries,
        "confidence_score": confidence
    }
