from typing import Dict, Any
import re
import json
from pathlib import Path

from app.agents.layout_extractor import extract_layout_blocks
from app.agents.section_detector import detect_sections
from app.agents.personal_extractor import extract_personal_info
from app.agents.family_extractor import extract_family_background
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
from app.agents.bundle_constructor import construct_focus_area_bundle, construct_question_bundle
from app.agents.interview_synthesizer import synthesize_interview_focus_areas
from app.agents.interview_generator import generate_interview
from app.agents.report_annotations import build_report_annotations
from app.llm.client import LLMClientError

# Policy and ROS
from app.policy.guard import (
    validate_focus_areas,
    validate_question_groups,
    validate_signals,
    sanitise_llm_output,
)
from app.ros.assembler import assemble_ros_v1

# Models and Utilities
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.canonical.version import CANONICAL_VERSION
from app.config import settings
from app.agents.section_scope_resolver import resolve_section_scopes
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


def run_deterministic_pipeline(
    application_id: str,
    pdf_path: str,
    db: Session | None = None,
) -> Dict[str, Any]:
    return run_pipeline(application_id, pdf_path, db=db, stop_after_canonical=True)


def run_pipeline(
    application_id: str,
    pdf_path: str,
    db: Session | None = None,
    stop_after_canonical: bool = False,
) -> Dict[str, Any]:
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
    scopes = resolve_section_scopes(section_data, parser_engine_version, layout_data.get("rows"))
    section_map = scopes["section_map"]
    section_slices = scopes["section_slices"]
    parent_sections = section_slices.get("parent_details", [])
    address_sections = section_slices.get("address_details", [])
    academic_rows = scopes["academic_rows"]
    test_rows = scopes["test_rows"]
    personal_blocks = section_map.get("personal_details", [])
    academic_blocks = section_map.get("academics", [])
    test_blocks = section_map.get("standardized_tests", [])
    essay_blocks = section_map.get("essays", [])
    additional_info_blocks = section_map.get("additional_information", [])
    extra_blocks = section_map.get("extracurricular", [])
    co_blocks = section_map.get("co_curricular", [])
    leadership_blocks = section_map.get("leadership", [])

    essay_blocks_to_pass = essay_blocks if essay_blocks else layout_data["blocks"]

    # Agent 3: Personal Information
    logger.debug("Agent invocation (agent_id: 3, agent_name: Personal Information Extractor Python Agent)")
    personal_scope = personal_blocks if personal_blocks else layout_data["blocks"]
    personal_data = extract_personal_info(personal_scope)
    family_data = extract_family_background(parent_sections)
    personal_data.setdefault("identifiers", {})["family_background"] = family_data["family_background"]
    personal_data["confidence_score"] = max(
        personal_data.get("confidence_score", 0.0),
        family_data.get("confidence_score", 0.0),
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

    page_1, page_2, page_3, _, entity_id_map = project_ros(canonical_data)
    deterministic_signals = detect_signals(canonical_data, entity_id_map)
    pages_1_3 = {
        "page_1_background_profile": page_1,
        "page_2_academic_and_engagement": page_2,
        "page_3_essays": page_3,
    }

    # Persist canonical as soon as deterministic assembly completes so failed LLM
    # runs can still be replayed through the Stage 1.7 boundary.
    try:
        app_uuid = uuid.UUID(application_id)
        if db is not None:
            existing_canonical = (
                db.query(CanonicalRecord)
                .filter(CanonicalRecord.application_id == app_uuid)
                .first()
            )
            if not existing_canonical:
                db_canonical = CanonicalRecord(
                    application_id=app_uuid,
                    canonical_version=CANONICAL_VERSION,
                    canonical_data=sanitize_for_json(canonical_data),
                    deterministic_signals=sanitize_for_json(deterministic_signals),
                    pages_1_3=sanitize_for_json(pages_1_3),
                )
                db.add(db_canonical)
            else:
                existing_canonical.canonical_version = CANONICAL_VERSION
                existing_canonical.canonical_data = sanitize_for_json(canonical_data)
                existing_canonical.deterministic_signals = sanitize_for_json(deterministic_signals)
                existing_canonical.pages_1_3 = sanitize_for_json(pages_1_3)

            db_app = db.query(Application).filter(Application.id == app_uuid).first()
            if db_app:
                db_app.status = "PROCESSED"

            db.commit()
            logger.info(f"Canonical persisted for {application_id} before LLM boundary")
    except Exception as e:
        if db is not None:
            db.rollback()
        logger.error(f"Canonical persistence failed for {application_id}: {str(e)}")
        raise

    if stop_after_canonical:
        return {
            "canonical_data": canonical_data,
            "pages_1_3": pages_1_3,
            "deterministic_signals": deterministic_signals,
            "ros_v1": None,
            "validation_result": {"passed": True, "violations_log": []},
            "confidence": agg_conf,
        }

    return run_synthesis_pipeline(application_id, canonical_data, db=db, aggregate_confidence=agg_conf)


def run_synthesis_pipeline(
    application_id: str,
    canonical_data: Dict[str, Any],
    db: Session | None = None,
    aggregate_confidence: Any | None = None,
    persisted_review: CanonicalRecord | None = None,
) -> Dict[str, Any]:
    agg_conf = (
        aggregate_confidence
        if aggregate_confidence is not None
        else canonical_data.get("extraction_confidence", {}).get("aggregate_confidence", "N/A")
    )

    logger.info(f"Stage 1.7 - Commencing Pipeline Orchestration (application_id: {application_id})")

    page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical_data)
    if persisted_review and persisted_review.pages_1_3:
        page_1 = persisted_review.pages_1_3.get("page_1_background_profile", page_1)
        page_2 = persisted_review.pages_1_3.get("page_2_academic_and_engagement", page_2)
        page_3 = persisted_review.pages_1_3.get("page_3_essays", page_3)

    logger.debug("Agent 12: Signal Detector")
    deterministic_signals = (
        persisted_review.deterministic_signals
        if persisted_review and persisted_review.deterministic_signals
        else detect_signals(canonical_data, entity_id_map)
    )

    logger.debug("Agent 13: Projection Builder")
    call_1_projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
    essay_fragments = call_1_projection.get("essay_fragments", [])

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
        _handle_abort(
            application_id,
            abort_res,
            db,
            artifacts={
                "stage": "call_1_transport",
                "validation_result": abort_res,
                "call_1_projection": call_1_projection,
                "essay_fragments": essay_fragments,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": abort_res, "confidence": agg_conf}

    logger.debug("Policy Guard: Signal Sanitiser (pre-validation auto-repair)")
    sanitised_call_1_json = None
    try:
        raw_call_1_json = __import__("json").loads(raw_call_1_output)
        valid_fragment_ids = {f.get("fragment_id") for f in essay_fragments if f.get("fragment_id")}
        valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
        fragment_entity_lookup = {
            fragment.get("fragment_id"): fragment.get("entity_id")
            for fragment in essay_fragments
            if fragment.get("fragment_id") and fragment.get("entity_id")
        }
        sanitised_call_1_json = sanitise_llm_output(
            raw_call_1_json,
            valid_fragment_ids,
            valid_entity_ids,
            fragment_entity_lookup=fragment_entity_lookup,
        )
        raw_call_1_output = __import__("json").dumps(sanitised_call_1_json)
    except Exception as san_err:
        logger.warning(f"[SANITISER] Skipped — could not parse LLM output for repair: {san_err}")

    logger.debug("Policy Guard: Signal Validation")
    val_res_1 = validate_signals(
        raw_call_1_output,
        entity_id_map,
        deterministic_signals,
        essay_fragments=essay_fragments,
    )

    if not val_res_1["passed"]:
        logger.error(f"Architecture Lock 3.4: Call 1 Validation Failed for {application_id}. HALTING PIPELINE.")
        _handle_abort(
            application_id,
            val_res_1,
            db,
            artifacts={
                "stage": "call_1_validation",
                "raw_call_1_output": raw_call_1_output,
                "sanitised_call_1_output": sanitised_call_1_json,
                "validation_result": val_res_1,
                "call_1_projection": call_1_projection,
                "essay_fragments": essay_fragments,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": val_res_1, "confidence": agg_conf}

    logger.debug(f"Agent 15: Focus-Area Bundle Constructor (keys in val_res_1: {list(val_res_1.keys())})")
    validated_call_1_output = val_res_1["sanitized_output"]
    focus_area_bundle = construct_focus_area_bundle(validated_call_1_output, canonical_data, entity_id_map)

    logger.debug("Agent 16: Interview Synthesizer (LLM Call 2)")
    try:
        raw_call_2_output = synthesize_interview_focus_areas(focus_area_bundle)
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
        _handle_abort(
            application_id,
            abort_res,
            db,
            artifacts={
                "stage": "call_2_transport",
                "validation_result": abort_res,
                "focus_area_bundle": focus_area_bundle,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": abort_res, "confidence": agg_conf}

    logger.debug("Policy Guard: Focus Area Validation")
    val_res_2 = validate_focus_areas(raw_call_2_output, validated_call_1_output)

    if not val_res_2["passed"]:
        logger.error(f"Call 2 Validation Failed for {application_id}")
        _handle_abort(
            application_id,
            val_res_2,
            db,
            artifacts={
                "stage": "call_2_validation",
                "raw_call_2_output": raw_call_2_output,
                "validation_result": val_res_2,
                "focus_area_bundle": focus_area_bundle,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": val_res_2, "confidence": agg_conf}

    validated_focus_areas = val_res_2["sanitized_output"]
    question_bundle = construct_question_bundle(
        validated_call_1_output,
        validated_focus_areas,
        canonical_data,
        entity_id_map,
    )

    logger.debug("Agent 17: Interview Generator (LLM Call 3)")
    try:
        raw_call_3_output = generate_interview(question_bundle, entity_id_map)
    except LLMClientError as e:
        logger.error(f"LLM Call 3 Transport/Load Failure: {str(e)}")
        abort_res = {
            "passed": False,
            "violations_log": [{
                "violation_id": str(uuid.uuid4()),
                "field": "llm_call_3",
                "type": "transport_error",
                "context": str(e)
            }]
        }
        _handle_abort(
            application_id,
            abort_res,
            db,
            artifacts={
                "stage": "call_3_transport",
                "validation_result": abort_res,
                "question_bundle": question_bundle,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": abort_res, "confidence": agg_conf}

    logger.debug("Policy Guard: Question Group Validation")
    val_res_3 = validate_question_groups(raw_call_3_output, entity_id_map, question_bundle)

    if not val_res_3["passed"]:
        logger.error(f"Call 3 Validation Failed for {application_id}")
        _handle_abort(
            application_id,
            val_res_3,
            db,
            artifacts={
                "stage": "call_3_validation",
                "raw_call_3_output": raw_call_3_output,
                "validation_result": val_res_3,
                "question_bundle": question_bundle,
            },
        )
        return {"canonical_data": canonical_data, "ros_v1": None, "validation_result": val_res_3, "confidence": agg_conf}

    logger.debug("ROS Assembler")
    validated_themes = validated_call_1_output["themes"]
    validated_signals = validated_call_1_output["signals"]
    validated_focus_area_items = validated_focus_areas["focus_areas"]
    validated_question_groups = val_res_3["sanitized_output"]["question_groups"]

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
        focus_areas=validated_focus_area_items,
        question_groups=validated_question_groups,
        report_metadata=report_meta
    )

    synthesis_output = ros_document.copy()
    annotations = build_report_annotations(
        validated_signals,
        validated_themes,
        entity_id_map,
        essay_fragments=essay_fragments,
    )
    synthesis_output["signal_data"] = {
        "deterministic_signals": deterministic_signals,
        "signals": validated_signals,
        "themes": validated_themes,
        "annotations": annotations,
    }

    try:
        if db is not None:
            db_app = db.query(Application).filter(Application.id == uuid.UUID(application_id)).first()
            if db_app:
                db_app.status = "READY"

            db.commit()
            logger.info(f"Synthesis stage completed for {application_id}")
    except Exception as e:
        if db is not None:
            db.rollback()
        logger.error(f"Persistence failed for {application_id}: {str(e)}")
        raise

    return {
        "canonical_data": canonical_data,
        "ros_v1": synthesis_output,
        "validation_result": val_res_3,
        "confidence": agg_conf
    }

def _persist_failure_artifacts(application_id: str, payload: dict[str, Any]) -> None:
    try:
        artifact_dir = Path(settings.UPLOAD_DIRECTORY) / "failure_artifacts" / str(application_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        artifact_path = artifact_dir / f"{timestamp}.json"
        artifact_payload = sanitize_for_json(payload)
        artifact_payload["application_id"] = application_id
        artifact_payload["captured_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        with artifact_path.open("w", encoding="utf-8") as handle:
            json.dump(artifact_payload, handle, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.error(f"Failure artifact persistence failed for {application_id}: {str(exc)}")


def _handle_abort(
    application_id: str,
    val_result: dict,
    db: Session | None,
    artifacts: dict[str, Any] | None = None,
):
    """Internal helper to handle policy validation aborts."""
    if artifacts:
        _persist_failure_artifacts(application_id, artifacts)
    if db is None:
        return
    try:
        app_uuid = uuid.UUID(application_id)
        db_app = db.query(Application).filter(Application.id == app_uuid).first()
        if db_app:
            db_app.status = "FAILED"
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Abort handling failed for {application_id}: {str(e)}")
