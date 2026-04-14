import json
import logging
import os
import sys
import time
import uuid
import collections
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.canonical_record import CanonicalRecord
from app.agents.signal_interpreter import interpret_signals
from app.agents.projection_builder import build_projection
from app.agents.signal_detector import detect_signals
from app.projection.ros_projector import project_ros
from app.policy.guard import validate_signals, sanitise_llm_output

# Set up logging
logging.basicConfig(level=logging.ERROR) # Lower logging to focus on script output
logger = logging.getLogger(__name__)

def run_stress_test(app_id_str: str, iterations: int = 15):
    db = SessionLocal()
    results = []
    violation_counts = collections.Counter()
    
    try:
        app_uuid = uuid.UUID(app_id_str)
        canonical = db.query(CanonicalRecord).filter(CanonicalRecord.application_id == app_uuid).first()
        if not canonical:
            print(f"No canonical record found for {app_id_str}")
            return

        print(f"--- Starting Stress Test: {iterations} iterations for {app_id_str} ---")
        
        # Pre-execution: Build projection once (it's deterministic)
        page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical.canonical_data)
        deterministic_signals = detect_signals(canonical.canonical_data, entity_id_map)
        projection = build_projection(canonical.canonical_data, entity_id_map, deterministic_signals)
        essay_fragments = projection.get("essay_fragments", [])

        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...", end="", flush=True)
            
            try:
                # 1. Call LLM
                raw_output = interpret_signals(projection)

                # 1.5. Auto-repair (mirrors orchestrator)
                try:
                    raw_json = json.loads(raw_output)
                    valid_fragment_ids = {f.get("fragment_id") for f in essay_fragments if f.get("fragment_id")}
                    valid_entity_ids = {e.get("entity_id") for e in entity_id_map if e.get("entity_id")}
                    raw_json = sanitise_llm_output(raw_json, valid_fragment_ids, valid_entity_ids)
                    raw_output = json.dumps(raw_json)
                except Exception:
                    pass  # If JSON parse fails, let validate_signals handle it

                # 2. Validate
                val_res = validate_signals(
                    raw_output,
                    entity_id_map,
                    deterministic_signals,
                    essay_fragments=essay_fragments
                )
                
                passed = val_res['passed']
                violations = val_res.get('violations_log', [])
                
                results.append({
                    "iteration": i + 1,
                    "passed": passed,
                    "violations": violations
                })
                
                if not passed:
                    for v in violations:
                        violation_counts[v.get('type', 'unknown')] += 1
                
                print(f" {'PASSED' if passed else 'FAILED'}")
                
            except Exception as e:
                print(f" ERROR: {str(e)}")
                results.append({
                    "iteration": i + 1,
                    "error": str(e)
                })

            # Staggered execution
            if i < iterations - 1:
                time.sleep(3)

        # 4. Final Summary
        print("\n--- STRESS TEST SUMMARY ---")
        total_passed = sum(1 for r in results if r.get("passed") is True)
        print(f"Total Iterations: {iterations}")
        print(f"Total Passed: {total_passed}")
        print(f"Total Failed: {iterations - total_passed}")
        
        print("\nViolation Frequencies:")
        for v_type, count in violation_counts.most_common():
            print(f"  - {v_type}: {count}")

        # Save results to scratch
        with open("scratch/stress_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\nDetailed results saved to scratch/stress_test_results.json")

    finally:
        db.close()

if __name__ == "__main__":
    target_id = "0ec647d9-1b79-43b9-9c12-4bd1c92fc075"
    run_stress_test(target_id, 15)
