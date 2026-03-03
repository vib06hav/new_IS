import pytest
import os
from typing import Dict, Any

from app.agents.layout_extractor import extract_layout_blocks
from app.agents.section_detector import detect_sections
from app.agents.personal_extractor import extract_personal_info
from app.agents.academic_extractor import extract_academic_records
from app.agents.test_extractor import extract_test_records
from app.agents.essay_extractor import extract_essays
from app.agents.activity_extractor import extract_activities
from app.agents.cross_section_detector import detect_cross_sections
from app.agents.timeline_builder import build_timeline
from app.agents.integrity_analyzer import analyze_integrity
from app.agents.assembler import assemble_canonical
from app.canonical.version import CANONICAL_VERSION

def test_pipeline_agents_determinism():
    """
    Ensure all Agents 1-11 run successfully without LLM and output expected schemas.
    """
    # 1. Mock layout extractor output since we don't have a real PDF file for pdfminer
    blocks = [
        {"page": 1, "text": "Personal Information\nName: Jane Doe\nDate of Birth: 2005-05-05\nFirst Generation: Yes", "bbox": (0, 0, 10, 10)},
        {"page": 1, "text": "Academics\nGrade 10\nBoard: ICSE\nPercentage: 92%\nMaths: 95\nScience: 90", "bbox": (0, 0, 10, 10)},
        {"page": 1, "text": "Standardized Tests\nSAT\nDate: 2024-01-15\nTotal: 1550\nMath: 800\nEvidence-Based Reading: 750", "bbox": (0, 0, 10, 10)},
        {"page": 2, "text": "Essays\nPrompt: Why this college?\nI have always admired the Mathematics department...", "bbox": (0, 0, 10, 10)},
        {"page": 2, "text": "Activities\nActivity: Math Olympiad\nLevel: National\nDuration: 2022-2024\nParticipated and won gold.", "bbox": (0, 0, 10, 10)},
    ]
    
    layout_meta = {
        "blocks": blocks,
        "page_count": 2,
        "confidence_score": 0.95
    }

    # 2. Section Boundary Detector
    section_meta = detect_sections(layout_meta["blocks"])
    assert "sections" in section_meta
    
    sections = section_meta["sections"]
    
    # 3. Personal Info
    identifiers_data = extract_personal_info(blocks)
    assert identifiers_data["identifiers"]["full_name"] == "Jane Doe"
    assert identifiers_data["identifiers"]["date_of_birth"] == "2005-05-05"
    assert identifiers_data["identifiers"]["demographic_flags"]["first_generation"] is True
    
    # 4. Academic Records
    academic_data = extract_academic_records(blocks)
    assert len(academic_data["academic_entries"]) == 1
    assert academic_data["academic_entries"][0]["academic_level"] == "Grade 10"
    
    # 5. Tests
    test_data = extract_test_records(blocks)
    assert len(test_data["test_entries"]) == 1
    assert test_data["test_entries"][0]["test_name"] == "SAT"
    
    # 6. Essays
    essay_data = extract_essays(blocks)
    assert len(essay_data["essay_entries"]) == 1
    
    # 7. Activities
    activity_data = extract_activities(blocks)
    assert len(activity_data["activity_entries"]) == 1
    
    # 8. Cross Section Entity
    cross_section_data = detect_cross_sections(
        academic_data["academic_entries"],
        test_data["test_entries"],
        essay_data["essay_entries"],
        activity_data["activity_entries"]
    )
    
    # 9. Timeline Builder
    timeline_data = build_timeline(
        academic_data["academic_entries"],
        test_data["test_entries"],
        activity_data["activity_entries"]
    )
    assert len(timeline_data["timeline_entries"]) > 0
    
    # 10. Integrity Analyzer
    integrity_data = analyze_integrity(
        identifiers_data["identifiers"],
        academic_data["academic_entries"],
        essay_data["essay_entries"]
    )
    
    # 11. Canonical Assembler
    canonical_record = assemble_canonical(
        application_id="app-test-uuid",
        layout_meta=layout_meta,
        section_meta=section_meta,
        identifiers_data=identifiers_data,
        academic_data=academic_data,
        test_data=test_data,
        essay_data=essay_data,
        activity_data=activity_data,
        cross_section_data=cross_section_data,
        timeline_data=timeline_data,
        integrity_data=integrity_data
    )
    
    # Assertions on canonical output
    assert canonical_record["canonical_version"] == CANONICAL_VERSION
    assert canonical_record["identifiers"]["full_name"] == "Jane Doe"
    assert "extraction_confidence" in canonical_record
    assert len(canonical_record["academic_entries"]) == 1
    assert type(canonical_record["academic_entries"]) is list
