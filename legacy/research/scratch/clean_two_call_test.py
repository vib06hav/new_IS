import json
import logging
import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
import uuid
from app.agents.signal_interpreter import interpret_signals
from app.agents.interview_generator import generate_interview
from app.agents.bundle_constructor import construct_bundle
from app.projection.ros_projector import project_ros
from app.agents.signal_detector import detect_signals
from app.agents.projection_builder import build_projection
from app.policy.guard import validate_signals, sanitise_llm_output, validate_question_groups
from app.agents.orchestrator import run_pipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s] %(message)s')
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("chardet").setLevel(logging.WARNING)
logger = logging.getLogger("clean_test")

def get_dummy_app_canonical():
    """Ingests Dummy App 2 directly from the PDF file to ensure clean context in-memory."""
    pdf_path = "tests/pdfs/Dummy App (2)_v8_filled.pdf"
    if not os.path.exists(pdf_path):
        logger.error(f"Could not find PDF at {pdf_path}")
        return None
        
    logger.info(f"Ingesting PDF: {pdf_path}...")
    app_id = str(uuid.uuid4())
    try:
        # Run deterministic pipeline up to canonical assembly without persisting to DB
        result = run_pipeline(app_id, pdf_path, db=None, stop_after_canonical=True)
        return result.get("canonical_data")
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        return None

def run_clean_test():
    # 1. Force the model to be Flash Lite
    from app.config import settings
    settings.AICREDITS_GENERATION_MODEL_PRIMARY = "google/gemini-2.5-flash-lite"
    settings.AICREDITS_GENERATION_MODEL_FALLBACK = "google/gemini-2.5-flash-lite"
    settings.LLM_MODEL_NAME = "google/gemini-2.5-flash-lite"
    
    # 2. Ingest the PDF directly
    canonical_data = get_dummy_app_canonical()
    if not canonical_data:
        return

    # 3. Build the LLM Context (Static Projection)
    logger.info("Building Static Projection (Context)...")
    _, _, _, _, entity_id_map = project_ros(canonical_data)
    deterministic_signals = detect_signals(canonical_data, entity_id_map)
    projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
    essay_fragments = projection.get("essay_fragments", [])
    
    valid_fragment_ids = {f.get("fragment_id") for f in essay_fragments if f.get("fragment_id")}
    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}

    logger.info("\n=== STARTING TWO-CALL PIPELINE ===")
    
    # ---------------------------------------------------------
    # CALL 1: SIGNAL INTERPRETER (Generates Signals & Themes)
    # ---------------------------------------------------------
    t0 = time.time()
    logger.info("-> Executing Call 1: interpret_signals")
    try:
        raw_call_1 = interpret_signals(projection)
    except Exception as e:
        logger.error(f"Call 1 API Error: {str(e)}")
        return
    call_1_latency = time.time() - t0
    
    # Auto-Repair & Validate
    raw_json_1 = json.loads(raw_call_1)
    sanitised_1 = sanitise_llm_output(raw_json_1, valid_fragment_ids, valid_entity_ids)
    
    val_res_1 = validate_signals(
        json.dumps(sanitised_1),
        entity_id_map,
        deterministic_signals,
        essay_fragments=essay_fragments
    )
    
    if not val_res_1['passed']:
        logger.error(f"Call 1 Guard Failed! Violations: {val_res_1.get('violations_log')}")
        return
        
    validated_signals_data = val_res_1["sanitized_output"]
    logger.info(f"[SUCCESS] Call 1 finished in {call_1_latency:.2f}s")
    logger.info(f"[RESULT] Found {len(validated_signals_data.get('signals', []))} Signals and {len(validated_signals_data.get('themes', []))} Themes.\n")
    
    # ---------------------------------------------------------
    # BRIDGE: BUNDLE CONSTRUCTOR (Funnels data into Call 2)
    # ---------------------------------------------------------
    logger.info("-> Constructing Evidence Bundle for Call 2...")
    bundle = construct_bundle(validated_signals_data, canonical_data, entity_id_map)
    
    # ---------------------------------------------------------
    # CALL 2: INTERVIEW GENERATOR (Generates Question Groups)
    # ---------------------------------------------------------
    t1 = time.time()
    logger.info("-> Executing Call 2: generate_interview")
    try:
        raw_call_2 = generate_interview(bundle, entity_id_map)
    except Exception as e:
        logger.error(f"Call 2 API Error: {str(e)}")
        return
    call_2_latency = time.time() - t1
    
    # Validate Output
    val_res_2 = validate_question_groups(raw_call_2, entity_id_map, bundle)
    if not val_res_2['passed']:
        logger.error(f"Call 2 Guard Failed! Violations: {val_res_2.get('violations_log')}")
        return
        
    validated_questions_data = val_res_2["sanitized_output"]
    logger.info(f"[SUCCESS] Call 2 finished in {call_2_latency:.2f}s")
    logger.info(f"[RESULT] Generated {len(validated_questions_data.get('question_groups', []))} Question Groups.\n")
    
    # ---------------------------------------------------------
    # SAVE COMBINED OUTPUT
    # ---------------------------------------------------------
    output = {
        "metrics": {
            "model": "google/gemini-2.5-flash-lite",
            "call_1_latency_seconds": round(call_1_latency, 2),
            "call_2_latency_seconds": round(call_2_latency, 2)
        },
        "stage_1_signals_themes": validated_signals_data,
        "stage_2_questions": validated_questions_data
    }
    
    os.makedirs("scratch", exist_ok=True)
    out_path = "scratch/clean_two_call_output.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
        
    logger.info(f"Pipeline complete. Fully sanitized output saved to: {out_path}")

if __name__ == "__main__":
    run_clean_test()
