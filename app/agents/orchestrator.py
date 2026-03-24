from typing import Dict, Any
import re

from app.agents.layout_extractor import extract_layout_blocks
from app.agents.section_detector import detect_sections
from app.agents.personal_extractor import extract_personal_info
from app.agents.geographic_extractor import extract_geographic_context
from app.agents.additional_info_extractor import extract_additional_info
from app.agents.academic_extractor import extract_academic_records
from app.agents.test_extractor import extract_test_records
from app.agents.essay_extractor import extract_essays
from app.agents.activity_extractor import extract_activities
from app.agents.cross_section_detector import detect_cross_sections
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
from app.config import settings
from app.utils.text_normalization import normalize_label
from app.utils.sanitizer import sanitize_for_json
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
logger = logging.getLogger(__name__)


def _merge_activity_results(*results: Dict[str, Any]) -> Dict[str, Any]:
    activity_entries = []
    confidences = []
    preferred_major = None

    for result in results:
        if not result:
            continue
        activity_entries.extend(result.get("activity_entries", []))
        if result.get("confidence_score") is not None:
            confidences.append(result.get("confidence_score", 0.0))
        if not preferred_major and result.get("preferred_major"):
            preferred_major = result["preferred_major"]

    return {
        "activity_entries": activity_entries,
        "preferred_major": preferred_major,
        "confidence_score": (sum(confidences) / len(confidences)) if confidences else 0.0,
    }


def _get_parser_engine_version() -> str:
    version = settings.PARSER_ENGINE_VERSION
    return version if version in {"v1", "v2"} else "v2"


def _rows_for_section(section: Dict[str, Any], layout_rows: Any) -> list:
    if not layout_rows:
        return []

    start = section.get("start_row_index")
    end = section.get("end_row_index")
    if start is None or end is None:
        return []

    return [
        row
        for row in layout_rows
        if start <= row.get("row_index", -1) <= end
    ]


def _collect_section_blocks(section_data: Dict[str, Any], parser_engine_version: str) -> Dict[str, Any]:
    buckets = {
        "personal_blocks": [],
        "parent_blocks": [],
        "academic_blocks": [],
        "test_blocks": [],
        "essay_blocks": [],
        "additional_info_blocks": [],
        "extra_blocks": [],
        "co_blocks": [],
        "leadership_blocks": [],
    }

    for section in section_data.get("sections", []):
        label = section.get("label", "").lower()
        section_type = section.get("section_type")
        blocks = section.get("blocks", [])
        logger.debug(f"Processing section: '{label}' ({section_type}) with {len(blocks)} blocks")

        if parser_engine_version == "v1":
            if "personal" in label:
                buckets["personal_blocks"].extend(blocks)
            elif any(kw in label for kw in ["parent", "father", "mother"]):
                buckets["parent_blocks"].extend(blocks)
            elif "extra" in label and "curricul" in label:
                buckets["extra_blocks"].extend(blocks)
            elif "co" in label and "curricul" in label:
                buckets["co_blocks"].extend(blocks)
            elif "leadership" in label:
                buckets["leadership_blocks"].extend(blocks)
            elif any(kw in label for kw in ["class", "academic", "education", "degree", "school"]):
                buckets["academic_blocks"].extend(blocks)
            elif any(kw in label for kw in ["test", "jee", "sat", "act", "examination", "percentile", "score"]):
                buckets["test_blocks"].extend(blocks)
            elif "essay" in label:
                buckets["essay_blocks"].extend(blocks)
            elif "additional" in label:
                buckets["additional_info_blocks"].extend(blocks)
            continue

        if section_type == "personal_details":
            buckets["personal_blocks"].extend(blocks)
        elif section_type == "parent_details":
            buckets["parent_blocks"].extend(blocks)
        elif section_type == "extracurricular":
            buckets["extra_blocks"].extend(blocks)
        elif section_type == "co_curricular":
            buckets["co_blocks"].extend(blocks)
        elif section_type == "leadership":
            buckets["leadership_blocks"].extend(blocks)
        elif section_type == "academics":
            buckets["academic_blocks"].extend(blocks)
        elif section_type == "standardized_tests":
            buckets["test_blocks"].extend(blocks)
        elif section_type == "essays":
            buckets["essay_blocks"].extend(blocks)
        elif section_type == "additional_information":
            buckets["additional_info_blocks"].extend(blocks)

    return buckets


def _collect_parent_sections(section_data: Dict[str, Any], parser_engine_version: str, layout_rows: Any) -> list:
    parent_sections = []
    for section in section_data.get("sections", []):
        label = section.get("label", "").lower()
        section_type = section.get("section_type")

        if parser_engine_version == "v1":
            is_parent_section = any(kw in label for kw in ["parent", "father", "mother"])
            is_address_section = "address" in label
        else:
            is_parent_section = section_type == "parent_details"
            is_address_section = section_type == "address_details"

        if not is_parent_section and not is_address_section:
            continue

        section_rows = _rows_for_section(section, layout_rows)
        row_blocks = []
        for row in section_rows:
            row_blocks.extend(row.get("blocks", []))

        parent_sections.append({
            "label": section.get("label"),
            "normalized_label": normalize_label(section.get("label", "")),
            "blocks": row_blocks or section.get("blocks", []),
        })

    return parent_sections


def _collect_address_sections(section_data: Dict[str, Any], parser_engine_version: str, layout_rows: Any) -> list:
    address_sections = []
    for section in section_data.get("sections", []):
        label = section.get("label", "").lower()
        section_type = section.get("section_type")

        if parser_engine_version == "v1":
            is_address_section = "address" in label
        else:
            is_address_section = section_type == "address_details"

        if not is_address_section:
            continue

        section_rows = _rows_for_section(section, layout_rows)
        row_blocks = []
        for row in section_rows:
            row_blocks.extend(row.get("blocks", []))

        address_sections.append({
            "label": section.get("label"),
            "normalized_label": normalize_label(section.get("label", "")),
            "blocks": row_blocks or section.get("blocks", []),
        })

    return address_sections


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
    section_data = detect_sections(layout_data["blocks"], rows=layout_data.get("rows"))
    logger.debug(f"Agent completion (agent_id: 2, confidence_score: {section_data.get('confidence_score', 'N/A')})")
    parser_engine_version = _get_parser_engine_version()
    logger.info(f"Parser engine version: {parser_engine_version}")
    section_buckets = _collect_section_blocks(section_data, parser_engine_version)
    parent_sections = _collect_parent_sections(section_data, parser_engine_version, layout_data.get("rows"))
    address_sections = _collect_address_sections(section_data, parser_engine_version, layout_data.get("rows"))
    academic_rows = []
    test_rows = []
    for section in section_data.get("sections", []):
        section_rows = _rows_for_section(section, layout_data.get("rows"))
        if not section_rows:
            continue
        section_type = section.get("section_type")
        label = section.get("label", "").lower()
        if parser_engine_version == "v1":
            if any(kw in label for kw in ["class", "academic", "education", "degree", "school"]):
                academic_rows.extend(section_rows)
            elif any(kw in label for kw in ["test", "jee", "sat", "act", "examination", "percentile", "score"]):
                test_rows.extend(section_rows)
        else:
            if section_type == "academics":
                academic_rows.extend(section_rows)
            elif section_type == "standardized_tests":
                test_rows.extend(section_rows)
    personal_blocks = section_buckets["personal_blocks"]
    academic_blocks = section_buckets["academic_blocks"]
    test_blocks = section_buckets["test_blocks"]
    essay_blocks = section_buckets["essay_blocks"]
    additional_info_blocks = section_buckets["additional_info_blocks"]
    extra_blocks = section_buckets["extra_blocks"]
    co_blocks = section_buckets["co_blocks"]
    leadership_blocks = section_buckets["leadership_blocks"]

    essay_blocks_to_pass = essay_blocks if essay_blocks else layout_data["blocks"]

    # Agent 3: Personal Information
    logger.debug("Agent invocation (agent_id: 3, agent_name: Personal Information Extractor Python Agent)")
    personal_scope = personal_blocks if personal_blocks else layout_data["blocks"]
    personal_data = extract_personal_info(
        personal_scope,
        parent_sections=parent_sections,
    )
    geographic_data = extract_geographic_context(address_sections)
    if geographic_data.get("geographic_context"):
        personal_data.setdefault("identifiers", {})["geographic_context"] = geographic_data["geographic_context"]
        personal_data["confidence_score"] = max(
            personal_data.get("confidence_score", 0.0),
            geographic_data.get("confidence_score", 0.0),
        )
    logger.debug(f"Agent completion (agent_id: 3, confidence_score: {personal_data.get('confidence_score', 'N/A')})")

    if additional_info_blocks:
        logger.debug("Agent invocation (agent_id: 3a, agent_name: Additional Information Extractor Python Agent)")
        additional_info_data = extract_additional_info(additional_info_blocks, all_blocks=layout_data["blocks"])
        preferred_major = additional_info_data.get("preferred_major")
        if preferred_major:
            identifiers = personal_data.setdefault("identifiers", {})
            identifiers.setdefault("declared_preferences", {})
            identifiers["preferred_major"] = identifiers.get("preferred_major") or preferred_major
            identifiers["declared_preferences"]["major"] = (
                identifiers["declared_preferences"].get("major") or preferred_major
            )
            personal_data["confidence_score"] = max(
                personal_data.get("confidence_score", 0.0),
                additional_info_data.get("confidence_score", 0.0),
            )
        logger.debug(
            f"Agent completion (agent_id: 3a, confidence_score: {additional_info_data.get('confidence_score', 'N/A')})"
        )

    # Agent 4: Academic Records
    logger.debug("Agent invocation (agent_id: 4, agent_name: Academic Records Extractor Python Agent)")
    academic_scope = academic_blocks if academic_blocks else layout_data["blocks"]
    academic_data = extract_academic_records(academic_scope, rows=academic_rows or None)
    logger.debug(f"Agent completion (agent_id: 4, confidence_score: {academic_data.get('confidence_score', 'N/A')})")

    # Agent 5: Standardized Tests
    logger.debug("Agent invocation (agent_id: 5, agent_name: Standardized Tests Extractor Python Agent)")
    # Pass raw blocks to use coordinate-based lookup with keywords
    test_scope = test_blocks if test_blocks else layout_data["blocks"]
    test_data = extract_test_records(test_scope, rows=test_rows or None)
    logger.debug(f"Agent completion (agent_id: 5, confidence_score: {test_data.get('confidence_score', 'N/A')})")

    # Agent 6: Essays
    logger.debug("Agent invocation (agent_id: 6, agent_name: Essays Extractor Python Agent)")
    essay_data = extract_essays(essay_blocks_to_pass)
    logger.debug(f"Agent completion (agent_id: 6, confidence_score: {essay_data.get('confidence_score', 'N/A')})")

    # Agent 7: Activities (Categorized)
    logger.debug("Agent invocation (agent_id: 7, agent_name: Activities Extractor Python Agent)")
    if extra_blocks or co_blocks or leadership_blocks:
        activity_data = _merge_activity_results(
            extract_activities(extra_blocks, pdf_path, forced_section="extracurricular") if extra_blocks else {},
            extract_activities(co_blocks, pdf_path, forced_section="co_curricular") if co_blocks else {},
            extract_activities(leadership_blocks, pdf_path, forced_section="leadership") if leadership_blocks else {},
        )
    else:
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

    # Agent 10: Integrtiy Analyzer
    logger.debug("Agent invocation (agent_id: 10, agent_name: Integrity Analyzer Python Agent)")
    integrity_data = analyze_integrity(
        personal_data.get("identifiers", {}),
        academic_data.get("academic_entries", []),
        essay_data.get("essay_entries", []),
        activity_data.get("activity_entries", []),
        layout_meta=layout_data,
        section_meta=section_data,
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
