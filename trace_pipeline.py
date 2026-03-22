import os
import sys
import uuid
import json
import logging
from typing import Dict, Any

# Ensure app path Is In sys.path
IN_CONTAINER = os.path.exists('/.dockerenv')
if IN_CONTAINER:
    app_path = '/app'
else:
    app_path = os.getcwd()

if app_path not in sys.path:
    sys.path.append(app_path)

# Import Agents and Utils
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
from app.utils.layout_normalizer import normalize_layout
from app.utils.sanitizer import sanitize_for_json
from datetime import datetime
from app.canonical.version import CANONICAL_VERSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TracePipeline")

def trace():
    try:
        pdf_name = "Dummy App (1)_v8_filled.pdf"
        if IN_CONTAINER:
            pdf_path = f"/app/tests/pdfs/{pdf_name}"
        else:
            pdf_path = os.path.join(app_path, "tests", "pdfs", pdf_name)

        print(f"\n--- TRACING PIPELINE FOR: {pdf_name} ---")
        sys.stdout.flush()

        app_id = str(uuid.uuid4())
        print(f"Generated Application ID: {app_id}")
        sys.stdout.flush()

        # STEP 1: Layout Extraction
        print("\n[STEP 1] Running Layout Extraction (Agent 1)...")
        layout_data = extract_layout_blocks(pdf_path)
        blocks = layout_data["blocks"]
        sys.stdout.flush()

        # STEP 2: Section Detection
        print("\n[STEP 2] Running Section Detection (Agent 2)...")
        section_data = detect_sections(blocks)
        sys.stdout.flush()

        academic_blocks = []
        test_blocks = []
        essay_blocks = []
        for section in section_data.get("sections", []):
            label = section.get("label", "").lower()
            b = section.get("blocks", [])
            if any(kw in label for kw in ["class", "academic", "education", "degree", "school"]):
                academic_blocks.extend(b)
            if any(kw in label for kw in ["test", "jee", "sat", "act", "examination"]):
                test_blocks.extend(b)
            if "essay" in label:
                essay_blocks.extend(b)

        test_rows = normalize_layout(test_blocks) if test_blocks else normalize_layout(blocks)
        essay_blocks_to_pass = essay_blocks if essay_blocks else blocks

        # Agent 3-11: Canonical Extraction
        print("\n[STEP 3-11] Running Canonical Extraction Agents...")
        personal_data = extract_personal_info(blocks)
        academic_data = extract_academic_records(blocks)
        test_data = extract_test_records(test_rows)
        essay_data = extract_essays(essay_blocks_to_pass)
        activity_data = extract_activities(blocks, pdf_path)
        
        cross_data = detect_cross_sections(
            academic_data.get("academic_entries", []),
            test_data.get("test_entries", []),
            essay_data.get("essay_entries", []),
            activity_data.get("activity_entries", [])
        )
        timeline_data = build_timeline(
            academic_data.get("academic_entries", []),
            test_data.get("test_entries", []),
            activity_data.get("activity_entries", [])
        )
        integrity_data = analyze_integrity(
            personal_data.get("identifiers", {}),
            academic_data.get("academic_entries", []),
            essay_data.get("essay_entries", []),
            activity_data.get("activity_entries", [])
        )
        
        canonical_data = assemble_canonical(
            application_id=app_id,
            layout_meta=layout_data,
            section_meta=section_data,
            identifiers_data=personal_data,
            academic_data=academic_data,
            test_data=test_data,
            essay_data=essay_data,
            activity_data=activity_data,
            cross_section_data=cross_data,
            timeline_data=timeline_data,
            integrity_data=integrity_data
        )
        
        print("\n--- COMPLETE CANONICAL PARSING OUTPUT ---")
        print(json.dumps(sanitize_for_json(canonical_data), indent=2))
        sys.stdout.flush()

        # SECTION 2: ROS PROJECTION (Pages 1-3)
        print("\n[STEP 12] Running ROS Projection...")
        sys.stdout.flush()
        page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical_data)
        
        print("\n--- ROS PAGE 1 ---")
        print(json.dumps(sanitize_for_json(page_1), indent=2))
        print("\n--- ROS PAGE 2 ---")
        print(json.dumps(sanitize_for_json(page_2), indent=2))
        print("\n--- ROS PAGE 3 ---")
        print(json.dumps(sanitize_for_json(page_3), indent=2))
        sys.stdout.flush()

        # SECTION 3: DETERMINISTIC SIGNALS (Agent 12)
        print("\n[STEP 13] Running Deterministic Signal Detection (Agent 12)...")
        sys.stdout.flush()
        deterministic_signals = detect_signals(canonical_data, entity_id_map)
        print("\n--- DETERMINISTIC SIGNALS ---")
        print(json.dumps(sanitize_for_json(deterministic_signals), indent=2))
        sys.stdout.flush()

        # SECTION 4: CONTROLLED CANONICAL OUTPUT (Agent 13: Projection Builder)
        print("\n[STEP 14] Building LLM Call 1 Projection (Agent 13)...")
        sys.stdout.flush()
        call_1_projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
        print("\n--- CONTROLLED CANONICAL OUTPUT (Call 1 Projection) ---")
        print(json.dumps(sanitize_for_json(call_1_projection), indent=2))
        sys.stdout.flush()

        # SECTION 5: LLM CALL 1 (Agent 14: Signal Interpreter)
        print("\n[STEP 15] Running Signal Interpreter (Agent 14 - LLM Call 1)...")
        sys.stdout.flush()
        raw_call_1_output = interpret_signals(call_1_projection)
        print("\n--- RESULTS FROM FIRST LLM CALL (RAW) ---")
        print(raw_call_1_output)
        sys.stdout.flush()

        # Policy Guard 1
        val_res_1 = validate_signals(raw_call_1_output, entity_id_map, deterministic_signals)
        print("\n--- CALL 1 VALIDATION RESULT ---")
        print(json.dumps(sanitize_for_json(val_res_1), indent=2))
        sys.stdout.flush()
        
        if not val_res_1["passed"]:
            print("\n!!! CALL 1 POLICY VIOLATION DETECTED - ABORTING TRACE !!!")
            return

        # SECTION 6: LLM CALL 2 (Agent 16: Interview Generator)
        print("\n[STEP 16] Running Interview Generator (Agent 16 - LLM Call 2)...")
        sys.stdout.flush()
        signals_to_bundle = val_res_1["sanitized_output"]["interpreted_signals"]
        signal_evidence_bundle = construct_bundle(signals_to_bundle, canonical_data, entity_id_map)
        raw_call_2_output = generate_interview(signal_evidence_bundle, entity_id_map)
        print("\n--- RESULTS FROM SECOND LLM CALL (RAW) ---")
        print(raw_call_2_output)
        sys.stdout.flush()

        # Policy Guard 2
        val_res_2 = validate_themes(raw_call_2_output, entity_id_map)
        print("\n--- CALL 2 VALIDATION RESULT ---")
        print(json.dumps(sanitize_for_json(val_res_2), indent=2))
        sys.stdout.flush()
        
        if not val_res_2["passed"]:
            print("\n!!! CALL 2 POLICY VIOLATION DETECTED - ABORTING TRACE !!!")
            return

        # SECTION 7: MERGED FINAL OUTPUT (ROS Assembler)
        print("\n[STEP 17] Assembling Final ROS Document...")
        sys.stdout.flush()
        report_meta = {
            "application_number": app_id,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "canonical_version": CANONICAL_VERSION,
            "report_version": "ROS_v1"
        }
        ros_document = assemble_ros_v1(
            page_1=page_1,
            page_2=page_2,
            page_3=page_3,
            llm_output=val_res_2["sanitized_output"],
            report_metadata=report_meta
        )
        print("\n--- MERGED FINAL OUTPUT (ROS v1) ---")
        print(json.dumps(sanitize_for_json(ros_document), indent=2))
        sys.stdout.flush()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[CRITICAL ERROR] Trace failed: {str(e)}")

if __name__ == "__main__":
    trace()
