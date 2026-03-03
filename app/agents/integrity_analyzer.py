from typing import List, Dict, Any
import uuid

def analyze_integrity(
    identifiers: Dict[str, Any],
    academic_entries: List[Dict],
    essay_entries: List[Dict]
) -> Dict[str, Any]:
    """
    Completeness & Integrity Analyzer.
    Detect structural anomalies: missing sections, placeholder essays.
    No quality inference.
    """
    confidence = 0.95
    anomalies = []
    
    # Check basic identifying details
    if not identifiers.get("full_name"):
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "missing_required_field",
            "severity_level": "high",
            "source_reference": "identifiers",
            "description": "Applicant full name is missing."
        })
        
    # Check academic completeness heuristically
    if not academic_entries:
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "missing_section",
            "severity_level": "critical",
            "source_reference": "academic_entries",
            "description": "No academic records were detected in the application."
        })
        
    # Check essay placeholders/duplications
    for essay in essay_entries:
        if essay.get("placeholder_flag", False):
            anomalies.append({
                "anomaly_id": str(uuid.uuid4()),
                "anomaly_type": "placeholder_response",
                "severity_level": "medium",
                "source_reference": essay["entry_id"],
                "description": f"Essay '{essay.get('essay_identifier', 'unknown')}' appears to be a placeholder."
            })
            
        if essay.get("duplication_ratio", 0.0) > 0.8:
            anomalies.append({
                "anomaly_id": str(uuid.uuid4()),
                "anomaly_type": "duplicate_essay",
                "severity_level": "high",
                "source_reference": essay["entry_id"],
                "description": f"Essay '{essay.get('essay_identifier', 'unknown')}' is largely duplicated."
            })
            
    return {
        "anomalies": anomalies,
        "confidence_score": confidence
    }
