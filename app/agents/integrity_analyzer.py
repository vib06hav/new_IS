from typing import List, Dict, Any
import uuid

def analyze_integrity(
    identifiers: Dict[str, Any],
    academic_entries: List[Dict],
    essay_entries: List[Dict],
    activity_entries: List[Dict] = None
) -> Dict[str, Any]:
    """
    Completeness & Integrity Analyzer.
    Detect structural anomalies: missing sections, placeholder essays, malformed activities.
    """
    confidence = 0.95
    anomalies = []
    
    # 1. Identifiers
    if not identifiers.get("full_name"):
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "missing_required_field",
            "severity_level": "high",
            "source_reference": "identifiers",
            "description": "Applicant full name is missing."
        })
        
    # 2. Academic Completeness
    if not academic_entries:
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "missing_section",
            "severity_level": "critical",
            "source_reference": "academic_entries",
            "description": "No academic records were detected in the application."
        })
        
    # 3. Essay Integrity
    for essay in essay_entries:
        if essay.get("placeholder_flag", False):
            anomalies.append({
                "anomaly_id": str(uuid.uuid4()),
                "anomaly_type": "placeholder_response",
                "severity_level": "medium",
                "source_reference": essay["entry_id"],
                "description": f"Essay '{essay.get('essay_identifier', 'unknown')}' appears to be a placeholder."
            })
            
    # 4. Activity Integrity
    if activity_entries:
        for entry in activity_entries:
            # Check for binary names (likely noise)
            name = str(entry.get("activity_name") or entry.get("position_title") or "").strip().lower()
            if name in ["yes", "no"]:
                anomalies.append({
                    "anomaly_id": str(uuid.uuid4()),
                    "anomaly_type": "malformed_activity",
                    "severity_level": "medium",
                    "source_reference": entry["entry_id"],
                    "description": f"Activity name/title '{name}' is likely binary noise from a form question."
                })
            
            # Check for question marks in descriptive fields (likely noise)
            desc_fields = [entry.get("achievement"), entry.get("roles_and_responsibilities"), entry.get("description_raw")]
            for f in desc_fields:
                if f and "?" in f:
                    anomalies.append({
                        "anomaly_id": str(uuid.uuid4()),
                        "anomaly_type": "activity_text_bleed",
                        "severity_level": "low",
                        "source_reference": entry["entry_id"],
                        "description": "Descriptive field contains question marks, suggesting bleed from form labels."
                    })
                    break

    return {
        "anomalies": anomalies,
        "confidence_score": confidence
    }
