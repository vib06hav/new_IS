import argparse
import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Note: We import models to inspect the DB locally if needed, 
# but we primarily use the API for the "complete run".
from app.database import SessionLocal
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.models.final_report import FinalReport
from app.models.user import User
from app.auth.security import get_password_hash


API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PDF = "demo-pdfs/Dummy App (1)_v8_filled.pdf"
OUTPUT_ROOT = Path("dev/generated/test-outputs/stage_1_7_runs")

# Credentials for our test admin
TEST_ADMIN_EMAIL = "test_admin_pipeline@example.com"
TEST_ADMIN_PASSWORD = "PipelineDebugPass123!"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_jsonable(payload), handle, indent=2, ensure_ascii=False)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        body = response.text

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
    }


def _application_row_payload(app_row: Application | None) -> dict[str, Any] | None:
    if not app_row:
        return None

    return {
        "id": str(app_row.id),
        "uploaded_by": str(app_row.uploaded_by),
        "storage_key": app_row.storage_key,
        "status": app_row.status,
        "created_at": app_row.created_at,
    }


def _record_payload(record: Any, field_name: str) -> dict[str, Any] | None:
    if not record:
        return None

    return {
        "id": str(record.id),
        "application_id": str(record.application_id),
        "created_at": record.created_at,
        field_name: getattr(record, field_name),
        "canonical_version": getattr(record, "canonical_version", None),
        "report_version": getattr(record, "report_version", None),
    }


def _build_output_dir(pdf_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")
    return OUTPUT_ROOT / f"{stamp}_{safe_name}"


def _ensure_test_admin():
    """Directly ensures a test admin exists in the database for our script to use."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == TEST_ADMIN_EMAIL).first()
        if not admin:
            print(f"Seeding test admin {TEST_ADMIN_EMAIL} into DB...")
            admin = User(
                name="Pipeline Test Admin",
                email=TEST_ADMIN_EMAIL,
                password_hash=get_password_hash(TEST_ADMIN_PASSWORD),
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("  Admin user created.")
        else:
            print(f"Test admin {TEST_ADMIN_EMAIL} already exists.")
    finally:
        db.close()


def _login_as_admin(client: httpx.Client, run_dir: Path) -> str:
    """Attempts to login as the test admin and returns the Bearer token."""
    _ensure_test_admin()
    
    print(f"Logging in as {TEST_ADMIN_EMAIL}...")
    login_response = client.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    
    _write_json(run_dir / "02_login_response.json", _response_payload(login_response))
    login_response.raise_for_status()

    # Extract the JWT from the 'agis_session' cookie to use as a Bearer token
    # This avoids CSRF protection issues which trigger when using cookies without CSRF headers.
    token = client.cookies.get("agis_session")
    if not token:
        # Check set-cookie headers if not in client.cookies
        for cookie in login_response.cookies:
            if cookie.name == "agis_session":
                token = cookie.value
                break
    
    if not token:
        raise ValueError("Could not find agis_session cookie in login response")
        
    return token


def _dump_db_artifacts(run_dir: Path, application_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        app_uuid = UUID(application_id)
        app_row = db.query(Application).filter(Application.id == app_uuid).first()
        canonical_row = db.query(CanonicalRecord).filter(CanonicalRecord.application_id == app_uuid).first()
        report_row = db.query(FinalReport).filter(FinalReport.application_id == app_uuid).first()

        db_payload = {
            "application": _application_row_payload(app_row),
            "canonical_record": _record_payload(canonical_row, "canonical_data"),
            "final_report": _record_payload(report_row, "content"),
        }

        _write_json(run_dir / "db_artifacts_latest.json", db_payload)

        if canonical_row:
            _write_json(run_dir / "canonical_data.json", canonical_row.canonical_data)
        if report_row:
            _write_json(run_dir / "final_report_content.json", report_row.content)

        return db_payload
    finally:
        db.close()


def _poll_status(client: httpx.Client, application_id: str, target_status: str, headers: dict, run_dir: Path, step_name: str, timeout: int = 240) -> str:
    print(f"Polling application {application_id} for status {target_status} ({step_name})...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        resp = client.get(f"{API_BASE_URL}/applications/{application_id}", headers=headers)
        if resp.status_code == 200:
            current_status = resp.json().get("status")
            print(f"  Current status: {current_status}")
            if current_status == target_status:
                return current_status
            if current_status == "FAILED":
                print(f"!!! Application failed during {step_name}")
                return "FAILED"
        else:
            print(f"  Error polling status: {resp.status_code}")
        
        time.sleep(5)
    
    print(f"!!! Timeout waiting for status {target_status}")
    return "TIMEOUT"


def run(pdf_path: Path) -> int:
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    run_dir = _build_output_dir(pdf_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Starting run. Artifacts will be saved to: {run_dir}")

    _write_json(
        run_dir / "00_run_metadata.json",
        {
            "started_at": datetime.now(timezone.utc),
            "api_base_url": API_BASE_URL,
            "pdf_path": str(pdf_path),
            "script": "run_stage_1_7_pipeline_debug.py",
            "note": "Refactored for Stage 1.7 two-step pipeline. Using Bearer token to bypass CSRF.",
        },
    )

    with httpx.Client(timeout=600.0, follow_redirects=True) as client:
        token = _login_as_admin(client, run_dir)
        headers = {"Authorization": f"Bearer {token}"}
        print("Authenticated with Bearer token.")

        # Step 1: Upload PDF
        print(f"Step 1: Uploading {pdf_path.name}...")
        # We use a unique filename to avoid 409 Conflict with existing display_ids in the DB
        unique_filename = f"Test_Run_{pdf_path.stem}_{int(time.time())}.pdf".replace(" ", "_")
        print(f"Step 1: Uploading {pdf_path.name} as {unique_filename}...")
        with pdf_path.open("rb") as handle:
            upload_response = client.post(
                f"{API_BASE_URL}/applications/upload",
                headers=headers,
                files={"file": (unique_filename, handle, "application/pdf")},
            )

        _write_json(run_dir / "03_upload_response.json", _response_payload(upload_response))
        upload_response.raise_for_status()
        application_id = upload_response.json()["id"]
        print(f"  Created application ID: {application_id}")

        # Step 2: Wait for PROCESSED
        status = _poll_status(client, application_id, "PROCESSED", headers, run_dir, "Deterministic Extraction")
        if status != "PROCESSED":
            _dump_db_artifacts(run_dir, application_id)
            return 3

        # Step 3: Trigger Synthesis
        print("Step 3: Triggering Final Report Generation (Synthesis)...")
        # The admin route for triggering report generation is POST /applications/{id}/generate-report
        synth_response = client.post(
            f"{API_BASE_URL}/applications/{application_id}/generate-report",
            headers=headers,
        )
        _write_json(run_dir / "04_synthesis_trigger_response.json", _response_payload(synth_response))
        if synth_response.status_code >= 400:
            print(f"!!! Synthesis trigger failed: {synth_response.status_code}")
            _dump_db_artifacts(run_dir, application_id)
            return 4
        
        # Step 4: Wait for READY
        status = _poll_status(client, application_id, "READY", headers, run_dir, "LLM Synthesis")
        
        # Step 5: Final Artifact Dump
        db_payload = _dump_db_artifacts(run_dir, application_id)
        
        has_content = False
        if db_payload["final_report"]:
            themes = db_payload["final_report"].get("content", {}).get("page_4_focus_areas", {}).get("themes", [])
            has_content = len(themes) > 0

        summary = {
            "application_id": application_id,
            "final_status": status,
            "has_canonical": db_payload["canonical_record"] is not None,
            "has_report": db_payload["final_report"] is not None,
            "has_content": has_content,
            "run_dir": str(run_dir),
        }
        _write_json(run_dir / "summary.json", summary)

        summary_lines = [
            f"Run directory: {run_dir}",
            f"Application ID: {application_id}",
            f"Final Status: {status}",
            f"Canonical Data Persistent: {summary['has_canonical']}",
            f"Final Report Persistent: {summary['has_report']}",
            f"Final Report Has Content: {summary['has_content']}",
        ]
        print("\n" + "="*40)
        print("\n".join(summary_lines))
        print("="*40 + "\n")

        if status == "READY" and summary["has_report"] and summary["has_content"]:
            return 0
        return 5


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one PDF through the Stage 1.7 two-step pipeline and verify outputs."
    )
    parser.add_argument(
        "--pdf",
        default=DEFAULT_PDF,
        help="Path to the PDF to upload. Defaults to a sample file in demo-pdfs.",
    )
    args = parser.parse_args()

    return run(Path(args.pdf))


if __name__ == "__main__":
    raise SystemExit(main())
