import json
import logging
import os
import sys
import time
import uuid
import collections
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.canonical_record import CanonicalRecord
from app.agents.signal_interpreter import interpret_signals
from app.agents.projection_builder import build_projection
from app.agents.signal_detector import detect_signals
from app.projection.ros_projector import project_ros
from app.policy.guard import validate_signals, sanitise_llm_output
from app.llm.client import LLMClientError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s] %(message)s')
logger = logging.getLogger("stability_test")

def run_stability_test():
    db = SessionLocal()
    app_id_str = "0ec647d9-1b79-43b9-9c12-4bd1c92fc075" # Target applicant
    
    test_matrix = [
        {"provider": "google", "model": "google/gemini-2.5-flash-lite", "iterations": 1, "label": "Baseline"},
        {"provider": "openai", "model": "openai/gpt-4o-mini", "iterations": 2, "label": "Control"},
        {"provider": "deepseek", "model": "deepseek/deepseek-r1", "iterations": 3, "label": "Target"},
    ]

    report = []
    report.append("# Comparative Model Reliability Test Report\n")
    report.append(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}")
    report.append(f"**Target Applicant:** `{app_id_str}`\n")
    report.append("| Provider | Model | Iteration | Status | Latency | Violation/Repair |")
    report.append("|---|---|---|---|---|---|")

    try:
        app_uuid = uuid.UUID(app_id_str)
        canonical = db.query(CanonicalRecord).filter(CanonicalRecord.application_id == app_uuid).first()
        if not canonical:
            logger.error(f"No canonical record found for {app_id_str}")
            return

        # Pre-execution: Build projection once
        page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical.canonical_data)
        deterministic_signals = detect_signals(canonical.canonical_data, entity_id_map)
        projection = build_projection(canonical.canonical_data, entity_id_map, deterministic_signals)
        essay_fragments = projection.get("essay_fragments", [])
        
        valid_fragment_ids = {f.get("fragment_id") for f in essay_fragments if f.get("fragment_id")}
        valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}

        for execution in test_matrix:
            provider = execution["provider"]
            model_name = execution["model"]
            iterations = execution["iterations"]
            
            logger.info(f"--- Testing {model_name} ({iterations} iterations) ---")
            
            for i in range(iterations):
                iter_num = i + 1
                logger.info(f"Iteration {iter_num}/{iterations} starting...")
                start_time = time.time()
                
                status = "PASSED"
                error_detail = ""
                latency = 0
                
                try:
                    # Patch the settings to use the target model
                    with patch("app.config.settings.AICREDITS_GENERATION_MODEL_PRIMARY", model_name), \
                         patch("app.config.settings.AICREDITS_GENERATION_MODEL_FALLBACK", model_name), \
                         patch("app.config.settings.LLM_MODEL_NAME", model_name):
                        
                        # 1. Call LLM
                        raw_output = interpret_signals(projection)
                        latency = round(time.time() - start_time, 2)
                        
                        # 2. Sanitise
                        try:
                            raw_json = json.loads(raw_output)
                            sanitised_json = sanitise_llm_output(raw_json, valid_fragment_ids, valid_entity_ids)
                            processed_output = json.dumps(sanitised_json, indent=2)
                        except Exception as e:
                            logger.warning(f"JSON Parse/Sanitise failed: {e}")
                            processed_output = raw_output
                            status = "JSON_ERROR"

                        # 3. Save Output
                        folder = Path(f"provider_testing/{provider}")
                        folder.mkdir(parents=True, exist_ok=True)
                        output_file = folder / f"iteration_{iter_num}.json"
                        with open(output_file, "w") as f:
                            f.write(processed_output)
                        
                        # 4. Validate (to check if it actually passed the guard)
                        val_res = validate_signals(
                            processed_output,
                            entity_id_map,
                            deterministic_signals,
                            essay_fragments=essay_fragments
                        )
                        
                        if not val_res['passed']:
                            status = "GUARD_FAILED"
                            error_detail = val_res.get('violations_log', [{}])[0].get('type', 'logic')

                except LLMClientError as e:
                    latency = round(time.time() - start_time, 2)
                    status = "LLM_ERROR"
                    error_detail = str(e)
                    logger.error(f"Iteration {iter_num} failed: {error_detail}")
                except Exception as e:
                    latency = round(time.time() - start_time, 2)
                    status = "CRASH"
                    error_detail = str(e)
                    logger.error(f"Iteration {iter_num} crashed: {error_detail}")

                report.append(f"| {provider} | `{model_name}` | {iter_num} | {status} | {latency}s | {error_detail} |")
                
                if i < iterations - 1:
                    time.sleep(5) # Delay between iterations to avoid rate limits

        # Write Final Report
        with open("provider_testing/stability_report.md", "w") as f:
            f.write("\n".join(report))
        logger.info("Test complete. Report saved to provider_testing/stability_report.md")

    finally:
        db.close()

if __name__ == "__main__":
    run_stability_test()
