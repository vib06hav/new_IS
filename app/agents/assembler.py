import datetime
from typing import Dict, Any, List
from app.canonical.version import CANONICAL_VERSION
from app.canonical.model import CanonicalData

def assemble_canonical(
    application_id: str,
    layout_meta: Dict[str, Any],
    section_meta: Dict[str, Any],
    identifiers_data: Dict[str, Any],
    academic_data: Dict[str, Any],
    test_data: Dict[str, Any],
    essay_data: Dict[str, Any],
    activity_data: Dict[str, Any],
    cross_section_data: Dict[str, Any],
    integrity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Canonical Structure Assembler.
    Merges all extracted collections into the final versioned canonical representation.
    """
    
    # 1. Identifiers
    identifiers = identifiers_data.get("identifiers", {})
    identifiers["application_id"] = application_id
    # Clean up Identifiers for refined model
    refined_identifiers = {
        "application_id": identifiers.get("application_id"),
        "preferred_major": (
            identifiers.get("preferred_major")
            or identifiers.get("declared_preferences", {}).get("major")
            or activity_data.get("preferred_major")
        ),
        "full_name": identifiers.get("full_name"),
        "date_of_birth": identifiers.get("date_of_birth"),
        "family_background": identifiers.get("family_background"),
        "geographic_context": identifiers.get("geographic_context"),
    }
    
    # 2. Extraction Confidence
    agent_scores = [
        {"agent_id": 1, "agent_name": "Layout Block Extractor", "confidence_score": layout_meta.get("confidence_score", 0.0)},
        {"agent_id": 2, "agent_name": "Section Boundary Detector", "confidence_score": section_meta.get("confidence_score", 0.0)},
        {"agent_id": 3, "agent_name": "Personal Information Extractor", "confidence_score": identifiers_data.get("confidence_score", 0.0)},
        {"agent_id": 4, "agent_name": "Academic Records Extractor", "confidence_score": academic_data.get("confidence_score", 0.0)},
        {"agent_id": 5, "agent_name": "Standardized Test Extractor", "confidence_score": test_data.get("confidence_score", 0.0)},
        {"agent_id": 6, "agent_name": "Essay Extractor", "confidence_score": essay_data.get("confidence_score", 0.0)},
        {"agent_id": 7, "agent_name": "Activity Extractor", "confidence_score": activity_data.get("confidence_score", 0.0)},
        {"agent_id": 8, "agent_name": "Cross-Section Entity Detector", "confidence_score": cross_section_data.get("confidence_score", 0.0)},
        {"agent_id": 10, "agent_name": "Completeness & Integrity Analyzer", "confidence_score": integrity_data.get("confidence_score", 0.0)},
    ]
    
    weights = {
        1: 0.16,
        2: 0.16,
        3: 0.10,
        4: 0.16,
        5: 0.10,
        6: 0.10,
        7: 0.14,
        8: 0.04,
        10: 0.04,
    }
    weighted_total = sum(score["confidence_score"] * weights.get(score["agent_id"], 0.0) for score in agent_scores)
    anomaly_penalty = min(0.15, 0.02 * len(integrity_data.get("anomalies", [])))

    layout_issue_penalty = min(0.10, 0.03 * len(layout_meta.get("issues", [])))
    untyped_section_penalty = 0.0
    sections = section_meta.get("sections", [])
    if sections:
        untyped_count = sum(1 for section in sections if not section.get("section_type"))
        untyped_section_penalty = min(0.08, 0.01 * untyped_count)

    sparse_page_penalty = 0.0
    page_stats = layout_meta.get("page_stats", [])
    if page_stats:
        sparse_pages = sum(1 for stat in page_stats if stat.get("block_count", 0) <= 2)
        sparse_page_penalty = min(0.08, 0.02 * sparse_pages)

    aggregate_confidence = max(
        0.0,
        min(1.0, weighted_total - anomaly_penalty - layout_issue_penalty - untyped_section_penalty - sparse_page_penalty),
    )
    
    extraction_confidence = {
        "agent_scores": agent_scores,
        "aggregate_confidence": aggregate_confidence
    }
    
    # Build complete raw dictionary mapping to CanonicalData schema
    canonical_dict = {
        "canonical_version": CANONICAL_VERSION,
        "identifiers": refined_identifiers,
        "academic_entries": academic_data.get("academic_entries", []),
        "test_entries": test_data.get("test_entries", []),
        "essay_entries": essay_data.get("essay_entries", []),
        "activity_entries": activity_data.get("activity_entries", []),
        "integrity_report": {"anomalies": integrity_data.get("anomalies", [])},
        "extraction_confidence": extraction_confidence
    }
    
    # We can run it through the Pydantic model to ensure everything conforms strictly
    canonical_obj = CanonicalData(**canonical_dict)
    
    return canonical_obj.model_dump()
