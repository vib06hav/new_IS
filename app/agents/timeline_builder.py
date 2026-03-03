from typing import List, Dict, Any
import uuid

def build_timeline(
    academic_entries: List[Dict],
    test_entries: List[Dict],
    activity_entries: List[Dict]
) -> Dict[str, Any]:
    """
    Constructs an event-based timeline.
    """
    entries = []
    confidence = 0.95
    
    for entry in academic_entries:
        if entry.get("academic_year"):
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "year": entry["academic_year"],
                "event_label": f"Academic Record: {entry.get('academic_level', '')}",
                "source_type": "academic",
                "source_reference": entry["entry_id"]
            })
            
    for entry in test_entries:
        if entry.get("test_date"):
            # Extract year roughly from date string
            year_match = [d for d in entry["test_date"].split() if len(d) == 4 and d.isdigit()]
            year = year_match[0] if year_match else entry["test_date"]
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "year": year,
                "event_label": f"Test: {entry.get('test_name', '')}",
                "source_type": "test",
                "source_reference": entry["entry_id"]
            })
            
    for entry in activity_entries:
        if entry.get("duration"):
            entries.append({
                "entry_id": str(uuid.uuid4()),
                "year": entry["duration"][:4] if len(entry["duration"]) >= 4 else "Unknown",
                "event_label": f"Activity: {entry.get('activity_name', '')}",
                "source_type": "activity",
                "source_reference": entry["entry_id"]
            })
            
    # Sort timeline heuristically by year if possible
    entries.sort(key=lambda x: str(x["year"]), reverse=True)
    
    return {
        "timeline_entries": entries,
        "confidence_score": confidence
    }
