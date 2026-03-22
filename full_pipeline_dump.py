import os
import sys
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Ensure app path Is In sys.path
app_path = '/app'
if app_path not in sys.path:
    sys.path.append(app_path)

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

from app.agents.signal_detector import detect_signals
from app.agents.projection_builder import build_projection
from app.agents.signal_interpreter import interpret_signals
from app.agents.bundle_constructor import construct_bundle
from app.agents.interview_generator import generate_interview

from app.policy.guard import validate_signals, validate_themes
from app.ros.assembler import assemble_ros_v1
from app.canonical.version import CANONICAL_VERSION
from app.utils.sanitizer import sanitize_for_json

import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logger = logging.getLogger("FullPipelineDump")

def run_full_dump(pdf_path: str):
    results = {
        "metadata": {
            "pdf_path": pdf_path,
            "timestamp": datetime.utcnow().isoformat()
        },
        "stages": {}
    }
    
    application_id = str(uuid.uuid4())
    
    # Check PDF
    if not os.path.exists(pdf_path):
        logger.error(f"PDF NOT FOUND: {pdf_path}")
        return

    # 1. Deterministic Extraction
    start_time = time.time()
    logger.info("Executing Deterministic Extraction...")
    print("Stage 1: Extracting Layout Blocks (PDFMiner)...", flush=True)
    layout_data = extract_layout_blocks(pdf_path)
    print(f"Layout Extraction Complete in {time.time() - start_time:.2f}s", flush=True)
    from app.utils.layout_normalizer import normalize_layout
    layout_data["normalized_rows"] = normalize_layout(layout_data["blocks"])
    
    section_data = detect_sections(layout_data["blocks"])
    personal_data = extract_personal_info(layout_data["blocks"])
    academic_data = extract_academic_records(layout_data["blocks"])
    test_data = extract_test_records(layout_data["normalized_rows"])
    essay_data = extract_essays(layout_data["blocks"])
    activity_data = extract_activities(layout_data["blocks"], pdf_path)
    
    cv_academic = academic_data.get("academic_entries", [])
    cv_tests = test_data.get("test_entries", [])
    cv_essays = essay_data.get("essay_entries", [])
    cv_activities = activity_data.get("activity_entries", [])
    
    cross_section_data = detect_cross_sections(cv_academic, cv_tests, cv_essays, cv_activities)
    timeline_data = build_timeline(cv_academic, cv_tests, cv_activities)
    integrity_data = analyze_integrity(personal_data.get("identifiers", {}), cv_academic, cv_essays, cv_activities)
    
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
    
    results["stages"]["1_canonical_parsing"] = sanitize_for_json(canonical_data)
    
    print("Stage 2: Signal Detection & Projection...", flush=True)
    p1, p2, p3, annotated_can, entity_id_map = project_ros(canonical_data)
    det_signals = detect_signals(canonical_data, entity_id_map)
    
    # Fallback for trace only
    if not det_signals:
        aca_ids = [e["entity_id"] for e in entity_id_map if e.get("collection") == "academic_entries"]
        det_signals = [{"signal_id": "DET-INJECT-001", "signal_type": "academic_distribution", "observation": "High consistency (Injected for Trace)", "referenced_entity_ids": aca_ids or ["ACA-001"], "source_collection": "academic_entries"}]

    call_1_proj = build_projection(canonical_data, entity_id_map, det_signals)
    results["stages"]["2_projection"] = {"entity_id_map": entity_id_map, "deterministic_signals": det_signals, "call_1_projection": call_1_proj}
    
    # 3. LLM Call 1
    start_time = time.time()
    logger.info("Executing LLM Call 1...")
    print("Stage 3: LLM Stage 1 (Signal Interpretation)...", flush=True)
    raw_call_1 = interpret_signals(call_1_proj)
    print(f"LLM Call 1 Complete in {time.time() - start_time:.2f}s", flush=True)
    results["stages"]["3_llm_call_1_raw"] = raw_call_1
    
    print("Stage 4: Call 1 Policy Guard Validation...", flush=True)
    val_res_1 = validate_signals(raw_call_1, entity_id_map, det_signals)
    results["stages"]["4_call_1_validation"] = val_res_1
    
    # STRICT ABORT: Mirroring Orchestrator Architecture Lock 3.4
    if not val_res_1["passed"]:
        logger.warning("Call 1 Validation FAILED. HALTING as per Architecture Lock 3.4.")
        _save_dump(results)
        return

    interpreted_signals = val_res_1["sanitized_output"]["interpreted_signals"]

    # 4. Bundle and LLM Call 2
    logger.info("Executing LLM Call 2...")
    print("Stage 5: Bundle Construction...", flush=True)
    bundle = construct_bundle(interpreted_signals, canonical_data, entity_id_map)
    results["stages"]["5_signal_evidence_bundle"] = bundle
    
    start_time = time.time()
    print("Stage 6: LLM Stage 2 (Interview Generation)...", flush=True)
    raw_call_2 = generate_interview(bundle, entity_id_map)
    print(f"LLM Call 2 Complete in {time.time() - start_time:.2f}s", flush=True)
    results["stages"]["6_llm_call_2_raw"] = raw_call_2
    
    print("Stage 7: Call 2 Policy Guard Validation...", flush=True)
    val_res_2 = validate_themes(raw_call_2, entity_id_map)
    results["stages"]["7_call_2_validation"] = val_res_2
    
    if not val_res_2["passed"]:
        logger.warning("Call 2 Validation FAILED. HALTING.")
        _save_dump(results)
        return

    themes_output = val_res_2["sanitized_output"]

    # 5. Final ROS
    logger.info("Assembling Final ROS...")
    print("Stage 8: Final ROS Assembly...", flush=True)
    report_meta = {"application_number": application_id, "generated_at": datetime.utcnow().isoformat(), "canonical_version": CANONICAL_VERSION, "report_version": "ROS_v1"}
    ros_document = assemble_ros_v1(page_1=p1, page_2=p2, page_3=p3, llm_output=themes_output, report_metadata=report_meta)
    
    final_output = ros_document.copy()
    final_output["signal_data"] = {"deterministic_signals": sanitize_for_json(det_signals), "interpreted_signals": sanitize_for_json(interpreted_signals)}
    results["stages"]["8_final_ros_document"] = sanitize_for_json(final_output)
    
    _save_dump(results)
    logger.info("DONE.")

def _save_dump(results):
    output_file = "/app/full_pipeline_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    import sys
    test_pdf = sys.argv[1] if len(sys.argv) > 1 else "/app/tests/pdfs/Dummy App (1)_v8_filled.pdf"
    run_full_dump(test_pdf)
