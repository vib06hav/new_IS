from typing import List, Dict, Any
import uuid

from app.utils.text_normalization import has_mojibake


def analyze_integrity(
    identifiers: Dict[str, Any],
    academic_entries: List[Dict],
    essay_entries: List[Dict],
    activity_entries: List[Dict] = None,
    layout_meta: Dict[str, Any] = None,
    section_meta: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Completeness & Integrity Analyzer.
    Detect structural anomalies: missing sections, placeholder essays, malformed activities.
    """
    confidence = 0.95
    anomalies = []
    layout_meta = layout_meta or {}
    section_meta = section_meta or {}

    # 0. Layout / Section quality
    for issue in layout_meta.get("issues", []):
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": issue.get("issue_type", "layout_issue"),
            "severity_level": issue.get("severity", "medium"),
            "source_reference": issue.get("source_stage", "layout_extraction"),
            "description": issue.get("message", "Layout extraction reported an issue."),
        })

    sections = section_meta.get("sections", [])
    typed_sections = [section for section in sections if section.get("section_type")]
    if sections and not typed_sections:
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "untyped_sections",
            "severity_level": "medium",
            "source_reference": "section_detection",
            "description": "Section detector produced sections, but none mapped to canonical section types.",
        })

    page_stats = layout_meta.get("page_stats", [])
    sparse_pages = [stat["page"] for stat in page_stats if stat.get("block_count", 0) <= 2]
    if page_stats and len(sparse_pages) >= max(1, len(page_stats) // 2):
        anomalies.append({
            "anomaly_id": str(uuid.uuid4()),
            "anomaly_type": "low_text_density",
            "severity_level": "medium",
            "source_reference": "layout_extraction",
            "description": f"Multiple pages have very few text blocks: {sparse_pages}.",
        })
    
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
        if has_mojibake(essay.get("raw_text", "")):
            anomalies.append({
                "anomaly_id": str(uuid.uuid4()),
                "anomaly_type": "text_encoding_artifact",
                "severity_level": "medium",
                "source_reference": essay["entry_id"],
                "description": "Essay text contains mojibake or broken punctuation encoding."
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

            position = str(entry.get("position_title") or "").strip()
            if entry.get("activity_type") != "leadership" and position:
                position_word_count = len(position.replace("\n", " ").split())
                if position_word_count > 4:
                    anomalies.append({
                        "anomaly_id": str(uuid.uuid4()),
                        "anomaly_type": "activity_field_overload",
                        "severity_level": "medium",
                        "source_reference": entry["entry_id"],
                        "description": "Non-leadership position_title contains descriptive prose instead of a concise title."
                    })

            roles = str(entry.get("roles_and_responsibilities") or "").strip()
            if roles and roles.lower().endswith((" at", " in", " for", " with", " of", " to")):
                anomalies.append({
                    "anomaly_id": str(uuid.uuid4()),
                    "anomaly_type": "truncated_activity_text",
                    "severity_level": "medium",
                    "source_reference": entry["entry_id"],
                    "description": "Activity responsibility text appears truncated and ends in a dangling preposition."
                })

    confidence_penalty = min(0.30, 0.03 * len(anomalies))
    return {
        "anomalies": anomalies,
        "confidence_score": max(0.0, confidence - confidence_penalty)
    }
