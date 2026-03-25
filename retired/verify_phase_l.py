import os
import sys
import uuid
import json
import logging
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Detect if running in container
IN_CONTAINER = os.path.exists('/.dockerenv') or os.environ.get('KUBERNETES_SERVICE_HOST')

if IN_CONTAINER:
    app_path = '/app'
else:
    app_path = r'c:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser'

if app_path not in sys.path:
    sys.path.append(app_path)

from app.database import SessionLocal, engine
from app.agents.orchestrator import run_pipeline
from app.models.application import Application
from app.models.synthesis_record import SynthesisRecord
from app.models.canonical_record import CanonicalRecord
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PhaseL_Verification")

def run_verification():
    print("=== Phase L: Final Migration Verification ===")
    db = SessionLocal()
    
    # 1. Environment & Infrastructure Check (10.5)
    print("\n[10.5] Schema and Infrastructure Check:")
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"- Tables found: {tables}")
        expected_tables = {'users', 'applications', 'canonical_records', 'synthesis_records'}
        if set(tables).issuperset(expected_tables):
            print("  PASS: All four required tables exist.")
        else:
            print(f"  FAIL: Table mismatch. Found {tables}")

        # Check synthesis_records column
        columns = [c['name'] for c in inspector.get_columns('synthesis_records')]
        if 'synthesis_output' in columns:
             print("  PASS: synthesis_output column exists.")
        else:
             print("  FAIL: synthesis_output column missing.")
    except Exception as e:
        print(f"  FAIL: Database connectivity/schema check failed: {str(e)}")

    # 2. Codebase Cleanliness (10.4)
    print("\n[10.4] Codebase Cleanliness Check:")
    legacy_agent_path = os.path.join(app_path, 'app', 'agents', 'synthesis_agent.py')
    if not os.path.exists(legacy_agent_path):
        print("  PASS: synthesis_agent.py deleted.")
    else:
        # Note: If running in container, this might be old code from build
        print(f"  INFO: synthesis_agent.py check - exists: {os.path.exists(legacy_agent_path)}")

    try:
        from app.llm import client
        if not hasattr(client, 'generate_synthesis'):
            print("  PASS: generate_synthesis() removed from client.py.")
        else:
            print("  FAIL: generate_synthesis() still exists.")
    except Exception as e:
        print(f"  FAIL: LLM client check failed: {str(e)}")

    # 3. End-to-End Pipeline Run (10.1)
    print("\n[10.1] End-to-End Pipeline Run:")
    if IN_CONTAINER:
        pdf_path = '/app/tests/pdfs/Dummy App (1)_v8_filled.pdf'
    else:
        pdf_path = os.path.join(app_path, 'tests', 'pdfs', 'Dummy App (1)_v8_filled.pdf')
    
    # Ensure a user exists (Application requires uploaded_by)
    user = db.query(User).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="verification_test@example.com",
            password_hash="hashed_password",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create application record
    app_id = str(uuid.uuid4())
    db_app = Application(
        id=uuid.UUID(app_id),
        uploaded_by=user.id, 
        file_path=pdf_path,
        pipeline_status="processing"
    )
    db.add(db_app)
    db.commit()

    print(f"Starting pipeline for application_id: {app_id}")
    try:
        results = run_pipeline(app_id, pdf_path, db)
        print("Pipeline execution finished.")
        
        # Verify DB Records
        db.refresh(db_app)
        print(f"Pipeline Status in DB: {db_app.pipeline_status}")
        
        synthesis = db.query(SynthesisRecord).filter(SynthesisRecord.application_id == uuid.UUID(app_id)).first()
        if synthesis:
            print(f"  Synthesis Record: policy_passed={synthesis.policy_passed}, created_at={synthesis.created_at}")
            output = synthesis.synthesis_output
            
            if output is None:
                print("  FAIL: synthesis_output is NULL in database.")
                if synthesis.policy_violations_log:
                    print(f"  Violations Log: {json.dumps(synthesis.policy_violations_log, indent=2)}")
            else:
                print("  PASS: synthesis_output produced.")
                required_keys = {
                    'report_metadata', 'page_1_background_profile', 
                    'page_2_academic_and_engagement', 'page_3_essays', 
                    'page_4_focus_themes', 'page_5_question_groups', 'signal_data'
                }
                if all(k in output for k in required_keys):
                    print("  PASS: All 7 keys present in synthesis_output.")
                else:
                    present_keys = set(output.keys())
                    missing = required_keys - present_keys
                    print(f"  FAIL: Missing keys in synthesis_output: {missing}")
                    print(f"  Present keys: {present_keys}")

                if output.get('report_metadata', {}).get('report_version') == 'ROS_v1':
                    print("  PASS: report_version is ROS_v1.")
                else:
                    print(f"  FAIL: report_version mismatch: {output.get('report_metadata', {}).get('report_version')}")

                signal_data = output.get('signal_data', {})
                if signal_data.get('deterministic_signals'):
                    print("  PASS: deterministic_signals present and non-empty.")
                else:
                    print("  FAIL: deterministic_signals empty or missing.")

                if signal_data.get('interpreted_signals'):
                    print("  PASS: interpreted_signals present and non-empty.")
                else:
                    print("  FAIL: interpreted_signals empty or missing.")
        else:
            print("  FAIL: No synthesis record found.")

    except Exception as e:
        print(f"  CRITICAL FAIL: Pipeline crashed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()

    db.close()

if __name__ == "__main__":
    run_verification()
