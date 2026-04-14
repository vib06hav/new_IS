import json
import logging
import os
import sys
import uuid
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.canonical_record import CanonicalRecord
from app.agents.signal_interpreter import interpret_signals
from app.agents.projection_builder import build_projection
from app.agents.signal_detector import detect_signals
from app.projection.ros_projector import project_ros
from app.policy.guard import validate_signals

# Set up logging to see details
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_diagnostic(app_id_str: str):
    db = SessionLocal()
    try:
        app_uuid = uuid.UUID(app_id_str)
        canonical = db.query(CanonicalRecord).filter(CanonicalRecord.application_id == app_uuid).first()
        if not canonical:
            print(f"No canonical record found for {app_id_str}")
            return

        print(f"--- Running Diagnostic for {app_id_str} ---")
        
        # 1. Rebuild Projection
        print("1. project_ros...")
        page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical.canonical_data)
        
        print("2. detect_signals...")
        deterministic_signals = detect_signals(canonical.canonical_data, entity_id_map)
        
        print("3. build_projection...")
        projection = build_projection(canonical.canonical_data, entity_id_map, deterministic_signals)
        essay_fragments = projection.get("essay_fragments", [])

        # 2. Call LLM
        print("4. interpret_signals (Call 1)...")
        raw_output = interpret_signals(projection)
        
        print("\n--- LLM RAW OUTPUT ---")
        print(raw_output)
        print("--- END RAW OUTPUT ---\n")

        # 3. Validate
        print("5. validate_signals...")
        val_res = validate_signals(
            raw_output,
            entity_id_map,
            deterministic_signals,
            essay_fragments=essay_fragments
        )

        print("\n--- VALIDATION RESULT ---")
        print(f"Passed: {val_res['passed']}")
        if not val_res['passed']:
            print("\nVIOLATIONS:")
            print(json.dumps(val_res.get('violations_log', []), indent=2))
        
        print("\n--- NORMALIZED OUTPUT (SNEAK PEEK) ---")
        if val_res.get('normalized_output'):
            print(json.dumps(val_res['normalized_output'], indent=2)[:500] + "...")

    finally:
        db.close()

if __name__ == "__main__":
    # Use the last failed application ID from the logs if possible, 
    # or just use the one from the most recent test run.
    # From last log: 0ec647d9-1b79-43b9-9c12-4bd1c92fc075
    target_id = "0ec647d9-1b79-43b9-9c12-4bd1c92fc075"
    run_diagnostic(target_id)
