from typing import Dict, Any
import re

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
from app.projection.ros_projector import project_ros
from app.agents.synthesis_agent import run_synthesis_agent
from app.policy.guard import validate_synthesis_output
from app.ros.assembler import assemble_ros_v1
from app.canonical.version import CANONICAL_VERSION
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

def run_pipeline(application_id: str, pdf_path: str) -> Dict[str, Any]:
    """
    Executes the deterministic agent pipeline in fixed order.
    Returns the assembled canonical representation.
    Aborts on critical failures (e.g., file not found).
    """

    # Agent 1: Layout Extraction
    logger.debug("Agent invocation (agent_id: 1, agent_name: Layout Extraction Python Agent)")
    layout_data = extract_layout_blocks(pdf_path)
    logger.debug(f"Agent completion (agent_id: 1, confidence_score: {layout_data.get('confidence_score', 'N/A')})")
    if not layout_data.get("blocks") and layout_data.get("page_count", 0) == 0:
        raise ValueError(f"Critical Failure: Could not extract layout from {pdf_path}. {layout_data.get('error', '')}")

    # Layout Normalization Pipeline Step
    from app.utils.layout_normalizer import normalize_layout
    layout_data["normalized_rows"] = normalize_layout(layout_data["blocks"])

    # Agent 2: Section Boundary Detection
    logger.debug("Agent invocation (agent_id: 2, agent_name: Section Boundary Detector Python Agent)")
    section_data = detect_sections(layout_data["blocks"])
    logger.debug(f"Agent completion (agent_id: 2, confidence_score: {section_data.get('confidence_score', 'N/A')})")

    academic_blocks = []
    test_blocks = []
    essay_blocks = []
    
    extra_blocks = []
    co_blocks = []
    leadership_blocks = []

    for section in section_data.get("sections", []):
        label = section.get("label", "").lower()
        blocks = section.get("blocks", [])
        logger.debug(f"Processing section: '{label}' with {len(blocks)} blocks")
        
        if "extra" in label and "curricul" in label:
            logger.debug(f"Row matched Extra category: {label}")
            extra_blocks.extend(blocks)
        elif "co" in label and "curricul" in label:
            logger.debug(f"Row matched Co-Curricular category: {label}")
            co_blocks.extend(blocks)
        elif "leadership" in label:
            logger.debug(f"Row matched Leadership category: {label}")
            leadership_blocks.extend(blocks)
        elif any(kw in label for kw in ["class", "academic", "education", "degree", "school"]):
            logger.debug(f"Row matched Academic category: {label}")
            academic_blocks.extend(blocks)
        elif any(kw in label for kw in ["test", "jee", "sat", "act", "examination"]):
            logger.debug(f"Row matched Test category: {label}")
            test_blocks.extend(blocks)
        elif "essay" in label:
            logger.debug(f"Row matched Essay category: {label}")
            essay_blocks.extend(blocks)
        else:
            logger.debug(f"No match for section: {label}")

    academic_rows = normalize_layout(academic_blocks) if academic_blocks else layout_data["normalized_rows"]
    test_rows = normalize_layout(test_blocks) if test_blocks else layout_data["normalized_rows"]
    essay_blocks_to_pass = essay_blocks if essay_blocks else layout_data["blocks"]

    # Agent 3: Personal Information
    logger.debug("Agent invocation (agent_id: 3, agent_name: Personal Information Extractor Python Agent)")
    personal_data = extract_personal_info(layout_data["blocks"])
    logger.debug(f"Agent completion (agent_id: 3, confidence_score: {personal_data.get('confidence_score', 'N/A')})")

    # Agent 4: Academic Records
    logger.debug("Agent invocation (agent_id: 4, agent_name: Academic Records Extractor Python Agent)")
    academic_data = extract_academic_records(layout_data["blocks"])
    logger.debug(f"Agent completion (agent_id: 4, confidence_score: {academic_data.get('confidence_score', 'N/A')})")

    # Agent 5: Standardized Tests
    logger.debug("Agent invocation (agent_id: 5, agent_name: Standardized Tests Extractor Python Agent)")
    test_data = extract_test_records(test_rows)
    logger.debug(f"Agent completion (agent_id: 5, confidence_score: {test_data.get('confidence_score', 'N/A')})")

    # Agent 6: Essays
    logger.debug("Agent invocation (agent_id: 6, agent_name: Essays Extractor Python Agent)")
    essay_data = extract_essays(essay_blocks_to_pass)
    logger.debug(f"Agent completion (agent_id: 6, confidence_score: {essay_data.get('confidence_score', 'N/A')})")

    # Agent 7: Activities (Categorized)
    logger.debug("Agent invocation (agent_id: 7, agent_name: Activities Extractor Python Agent)")
    
    logger.debug(f"Categorizing activity blocks: extra={len(extra_blocks)}, co={len(co_blocks)}, lead={len(leadership_blocks)}")
    
    extra_rows = normalize_layout(extra_blocks) if extra_blocks else []
    co_rows = normalize_layout(co_blocks) if co_blocks else []
    lead_rows = normalize_layout(leadership_blocks) if leadership_blocks else []
    
    logger.debug(f"Normalized activity rows: extra={len(extra_rows)}, co={len(co_rows)}, lead={len(lead_rows)}")
    
    extra_res = extract_activities(extra_rows, category_hint="extracurricular")
    co_res = extract_activities(co_rows, category_hint="co_curricular")
    lead_res = extract_activities(lead_rows, category_hint="leadership")
    
    # Consolidate
    activity_data = {
        "extracurricular_activities": extra_res.get("activity_entries", []),
        "co_curricular_activities": co_res.get("activity_entries", []),
        "leadership_activities": lead_res.get("activity_entries", []),
        "activity_entries": [] # Legacy field
    }
    # For backward compatibility with agents 8 and 9, we merge them into activity_entries
    activity_data["activity_entries"] = (
        activity_data["extracurricular_activities"] + 
        activity_data["co_curricular_activities"] + 
        activity_data["leadership_activities"]
    )
    activity_data["confidence_score"] = min(
        extra_res.get("confidence_score", 1.0),
        co_res.get("confidence_score", 1.0),
        lead_res.get("confidence_score", 1.0)
    )

    # Agent 8: Cross-Section Entity Detection
    logger.debug("Agent invocation (agent_id: 8, agent_name: Cross-Section Entity Detector Python Agent)")
    cross_section_data = detect_cross_sections(
        academic_data.get("academic_entries", []),
        test_data.get("test_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", [])
    )
    logger.debug(f"Agent completion (agent_id: 8, confidence_score: {cross_section_data.get('confidence_score', 'N/A')})")

    # Agent 9: Timeline Builder
    logger.debug("Agent invocation (agent_id: 9, agent_name: Timeline Builder Python Agent)")
    timeline_data = build_timeline(
        academic_data.get("academic_entries", []),
        test_data.get("test_entries", []),
        activity_data.get("activity_entries", [])
    )
    logger.debug(f"Agent completion (agent_id: 9, confidence_score: {timeline_data.get('confidence_score', 'N/A')})")

    # Agent 10: Integrtiy Analyzer
    logger.debug("Agent invocation (agent_id: 10, agent_name: Integrity Analyzer Python Agent)")
    integrity_data = analyze_integrity(
        personal_data.get("identifiers", {}),
        academic_data.get("academic_entries", []),
        essay_data.get("essay_entries", [])
    )
    logger.debug(f"Agent completion (agent_id: 10, confidence_score: {integrity_data.get('confidence_score', 'N/A')})")

    # Agent 11: Canonical Structure Assembler
    logger.debug("Agent invocation (agent_id: 11, agent_name: Canonical Structure Assembler Python Agent)")
    canonical_data = assemble_canonical(
        application_id=application_id,
        layout_meta=layout_data,
        section_meta=section_data,
        identifiers_data=personal_data,
        academic_data=academic_data,
        test_data=test_data,
        essay_data=essay_data,
        activity_data=activity_data,
        cross_section_data=cross_section_data,
        timeline_data=timeline_data,
        integrity_data=integrity_data
    )
    
    agg_conf = canonical_data.get("extraction_confidence", {}).get("aggregate_confidence", "N/A")
    logger.debug(f"Agent completion (agent_id: 11, confidence_score: {agg_conf})")

    # Agent 0 / ROS Integration: Stage 1.5 Flow
    logger.info(f"Stage 1.5 - Commencing ROS Projection (application_id: {application_id})")
    
    # Deterministic Projection (Pages 1-3)
    page_1, page_2, page_3, annotated_canonical, entity_map = project_ros(canonical_data)
    
    try:
        # Synthesis Integration (Agent 12)
        synthesis_output_raw = run_synthesis_agent(annotated_canonical)
        
        # Validation Filter (Agent 13)
        validation_result = validate_synthesis_output(synthesis_output_raw, entity_map, sanitize=True)
        
        # Determine success state
        passed = validation_result.get("passed", False)
        
        if not passed:
            logger.error(f"Agent 13 validation failed for {application_id}. Application marked failed. No second LLM call permitted.")
            ros_document = None
        else:
            # ROS Assembly
            validated_pages = validation_result.get("sanitized_output", synthesis_output_raw)
            
            report_meta = {
                "application_number": application_id,
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "canonical_version": CANONICAL_VERSION,
                "report_version": "ROS_v1"
            }
            
            ros_document = assemble_ros_v1(
                page_1=page_1,
                page_2=page_2,
                page_3=page_3,
                llm_output=validated_pages,
                report_metadata=report_meta
            )
            logger.info(f"ROS v1 Assembly complete (application_id: {application_id})")
    except Exception as e:
        logger.error(f"LLM Synthesis failed with exception: {str(e)}")
        ros_document = None
        validation_result = {"passed": False, "error": str(e)}

    return {
        "canonical_data": canonical_data,
        "ros_v1": ros_document,
        "validation_result": validation_result,
        "confidence": agg_conf
    }
