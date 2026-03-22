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

# Stage 1.7 Agents
from app.agents.signal_detector import detect_signals
from app.agents.projection_builder import build_projection
from app.agents.signal_interpreter import interpret_signals
from app.agents.bundle_constructor import construct_bundle
from app.agents.interview_generator import generate_interview
from app.llm.client import LLMClientError

# Policy and ROS
from app.policy.guard import validate_signals, validate_themes
from app.ros.assembler import assemble_ros_v1

# Models and Utilities
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.models.synthesis_record import SynthesisRecord
from app.canonical.version import CANONICAL_VERSION
from app.utils.sanitizer import sanitize_for_json
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
logger = logging.getLogger(__name__)

def run_pipeline(application_id: str, pdf_path: str, db: Session) -> Dict[str, Any]:
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
    
    # Pass all blocks so it can detect its own section boundaries as per the plan
    activity_data = extract_activities(layout_data["blocks"], pdf_path)

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
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", [])
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

    # Persist canonical as soon as deterministic assembly completes so failed LLM
    # runs can still be replayed through the Stage 1.7 boundary.
    try:
        app_uuid = uuid.UUID(application_id)
        existing_canonical = (
            db.query(CanonicalRecord)
            .filter(CanonicalRecord.application_id == app_uuid)
            .first()
        )
        if not existing_canonical:
            db_canonical = CanonicalRecord(
                application_id=app_uuid,
                canonical_version=CANONICAL_VERSION,
                canonical_data=sanitize_for_json(canonical_data)
            )
            db.add(db_canonical)
            db.commit()
            logger.info(f"Canonical persisted for {application_id} before LLM boundary")
    except Exception as e:
        db.rollback()
        logger.error(f"Canonical persistence failed for {application_id}: {str(e)}")
        raise

    # Agent 0 / ROS Integration: Stage 1.7 Flow
    logger.info(f"Stage 1.7 - Commencing Pipeline Orchestration (application_id: {application_id})")
    
    # 2. Deterministic Projection (Pages 1-3 + entity_id_map)
    page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical_data)
    
    # 3. Agent 12: Signal Detector
    logger.debug("Agent 12: Signal Detector")
    deterministic_signals = detect_signals(canonical_data, entity_id_map)
    
    # 4. Agent 13: Projection Builder
    logger.debug("Agent 13: Projection Builder")
    call_1_projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
    
    # 5. Agent 14: Signal Interpreter (LLM Call 1)
    logger.debug("Agent 14: Signal Interpreter (LLM Call 1)")
    try:
        raw_call_1_output = interpret_signals(call_1_projection)
    except LLMClientError as e:
        logger.error(f"LLM Call 1 Transport/Load Failure: {str(e)}")
        abort_res = {
            "passed": False, 
            "violations_log": [{
                "violation_id": str(uuid.uuid4()), 
                "field": "llm_call_1", 
                "type": "transport_error", 
                "context": str(e)
            }]
        }
        _handle_abort(application_id, abort_res, db)
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": abort_res, "confidence": agg_conf}
    
    # 6. Policy Guard (Call 1 Validation)
    logger.debug("Policy Guard: Signal Validation")
    val_res_1 = validate_signals(raw_call_1_output, entity_id_map, deterministic_signals)
    
    # 7. Abort Path 1
    if not val_res_1["passed"]:
        logger.error(f"Architecture Lock 3.4: Call 1 Validation Failed for {application_id}. HALTING PIPELINE.")
        _handle_abort(application_id, val_res_1, db)
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": val_res_1, "confidence": agg_conf}

    # 8. Agent 15: Bundle Constructor
    logger.debug(f"Agent 15: Bundle Constructor (keys in val_res_1: {list(val_res_1.keys())})")
    signals_to_bundle = val_res_1["sanitized_output"]["interpreted_signals"]
    signal_evidence_bundle = construct_bundle(signals_to_bundle, canonical_data, entity_id_map)
    
    # 9. Agent 16: Interview Generator (LLM Call 2)
    logger.debug("Agent 16: Interview Generator (LLM Call 2)")
    try:
        raw_call_2_output = generate_interview(signal_evidence_bundle, entity_id_map)
    except LLMClientError as e:
        logger.error(f"LLM Call 2 Transport/Load Failure: {str(e)}")
        abort_res = {
            "passed": False, 
            "violations_log": [{
                "violation_id": str(uuid.uuid4()), 
                "field": "llm_call_2", 
                "type": "transport_error", 
                "context": str(e)
            }]
        }
        _handle_abort(application_id, abort_res, db)
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": abort_res, "confidence": agg_conf}
    
    # 10. Policy Guard (Call 2 Validation)
    logger.debug("Policy Guard: Theme Validation")
    val_res_2 = validate_themes(raw_call_2_output, entity_id_map, signal_evidence_bundle)
    
    # 11. Abort Path 2
    if not val_res_2["passed"]:
        logger.error(f"Call 2 Validation Failed for {application_id}")
        _handle_abort(application_id, val_res_2, db)
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": val_res_2, "confidence": agg_conf}

    # 12. ROS Assembler
    logger.debug("ROS Assembler")
    validated_output = val_res_2["sanitized_output"]
    
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
        llm_output=validated_output,
        report_metadata=report_meta
    )

    # 13. Final synthesis_output construction
    synthesis_output = ros_document.copy()
    synthesis_output["signal_data"] = {
        "deterministic_signals": deterministic_signals,
        "interpreted_signals": val_res_1["sanitized_output"]["interpreted_signals"]
    }

    # 14-16. Persistence and Finalization
    try:
        # Synthesis Persistence
        db_synthesis = SynthesisRecord(
            application_id=uuid.UUID(application_id),
            synthesis_output=sanitize_for_json(synthesis_output),
            policy_passed=True,
            policy_violations_log=None
        )
        db.add(db_synthesis)
        
        # Update App state
        db_app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
        if db_app:
            db_app.pipeline_status = "complete"
            try:
                db_app.pipeline_confidence = float(agg_conf)
            except (TypeError, ValueError):
                db_app.pipeline_confidence = None
            
        db.commit()
        logger.info(f"Pipeline complete and persisted for {application_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Persistence failed for {application_id}: {str(e)}")
        raise

    return {
        "canonical_data": canonical_data,
        "ros_v1": synthesis_output,
        "validation_result": val_res_2,
        "confidence": agg_conf
    }

def _handle_abort(application_id: str, val_result: dict, db: Session):
    """Internal helper to handle policy validation aborts."""
    try:
        app_uuid = uuid.UUID(application_id)
        db_app = db.query(Application).filter(Application.id == app_uuid).first()
        if db_app:
            db_app.pipeline_status = "failed"
        
        db_synthesis = SynthesisRecord(
            application_id=app_uuid,
            synthesis_output={
                "report_metadata": {
                    "application_id": application_id,
                    "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "canonical_version": CANONICAL_VERSION,
                    "report_version": "ROS_v1",
                    "status": "failed"
                }
            },
            policy_passed=False,
            policy_violations_log=sanitize_for_json(val_result.get("violations_log", []))
        )
        db.add(db_synthesis)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Abort handling failed for {application_id}: {str(e)}")
