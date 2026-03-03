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
    timeline_data: Dict[str, Any],
    integrity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Canonical Structure Assembler.
    Merges all extracted collections into the final versioned canonical representation.
    """
    
    # 1. Profile Meta
    profile_meta = {
        "source_document_page_count": layout_meta.get("page_count", 0),
        "extraction_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "layout_block_count": len(layout_meta.get("blocks", [])),
        "detected_section_labels": [s.get("label", "unknown") for s in section_meta.get("sections", [])]
    }
    
    # 2. Identifiers
    identifiers = identifiers_data.get("identifiers", {})
    identifiers["application_id"] = application_id
    
    # 3. Extraction Confidence
    agent_scores = [
        {"agent_id": 1, "agent_name": "Layout Block Extractor", "confidence_score": layout_meta.get("confidence_score", 0.0)},
        {"agent_id": 2, "agent_name": "Section Boundary Detector", "confidence_score": section_meta.get("confidence_score", 0.0)},
        {"agent_id": 3, "agent_name": "Personal Information Extractor", "confidence_score": identifiers_data.get("confidence_score", 0.0)},
        {"agent_id": 4, "agent_name": "Academic Records Extractor", "confidence_score": academic_data.get("confidence_score", 0.0)},
        {"agent_id": 5, "agent_name": "Standardized Test Extractor", "confidence_score": test_data.get("confidence_score", 0.0)},
        {"agent_id": 6, "agent_name": "Essay Extractor", "confidence_score": essay_data.get("confidence_score", 0.0)},
        {"agent_id": 7, "agent_name": "Activity Extractor", "confidence_score": activity_data.get("confidence_score", 0.0)},
        {"agent_id": 8, "agent_name": "Cross-Section Entity Detector", "confidence_score": cross_section_data.get("confidence_score", 0.0)},
        {"agent_id": 9, "agent_name": "Timeline Builder", "confidence_score": timeline_data.get("confidence_score", 0.0)},
        {"agent_id": 10, "agent_name": "Completeness & Integrity Analyzer", "confidence_score": integrity_data.get("confidence_score", 0.0)},
    ]
    
    aggregate_confidence = sum([score["confidence_score"] for score in agent_scores]) / len(agent_scores) if agent_scores else 0.0
    
    extraction_confidence = {
        "agent_scores": agent_scores,
        "aggregate_confidence": aggregate_confidence
    }
    
    # Build complete raw dictionary mapping to CanonicalData schema
    canonical_dict = {
        "canonical_version": CANONICAL_VERSION,
        "identifiers": identifiers,
        "profile_meta": profile_meta,
        "academic_entries": academic_data.get("academic_entries", []),
        "test_entries": test_data.get("test_entries", []),
        "essay_entries": essay_data.get("essay_entries", []),
        "activity_entries": activity_data.get("activity_entries", []),
        "timeline_entries": timeline_data.get("timeline_entries", []),
        "cross_references": {"entity_map": cross_section_data.get("entity_map", [])},
        "integrity_report": {"anomalies": integrity_data.get("anomalies", [])},
        "extraction_confidence": extraction_confidence
    }
    
    # We can run it through the Pydantic model to ensure everything conforms strictly
    canonical_obj = CanonicalData(**canonical_dict)
    
    return canonical_obj.model_dump()
