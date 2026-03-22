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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.models.synthesis_record import SynthesisRecord
from app.models.user import User


API_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PDF = "tests/pdfs/Dummy App (1)_v8_filled.pdf"
OUTPUT_ROOT = Path("tests/outputs/stage_1_7_runs")


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
        "file_path": app_row.file_path,
        "pipeline_status": app_row.pipeline_status,
        "pipeline_confidence": app_row.pipeline_confidence,
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
        "policy_passed": getattr(record, "policy_passed", None),
        "policy_violations_log": getattr(record, "policy_violations_log", None),
    }


def _build_output_dir(pdf_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")
    return OUTPUT_ROOT / f"{stamp}_{safe_name}"


def _register_and_login(client: httpx.Client, run_dir: Path) -> tuple[str, str]:
    email = f"stage17_{int(time.time())}@example.com"
    password = "stage17debugpass123"

    register_response = client.post(
        f"{API_BASE_URL}/auth/register",
        json={"email": email, "password": password, "role": "interviewer"},
    )
    _write_json(run_dir / "01_register_response.json", _response_payload(register_response))
    register_response.raise_for_status()

    login_response = client.post(
        f"{API_BASE_URL}/auth/login",
        data={"username": email, "password": password},
    )
    _write_json(run_dir / "02_login_response.json", _response_payload(login_response))
    login_response.raise_for_status()

    access_token = login_response.json()["access_token"]
    return email, access_token


def _find_user(db, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def _find_latest_application_for_user(db, user_id: UUID) -> Application | None:
    return (
        db.query(Application)
        .filter(Application.uploaded_by == user_id)
        .order_by(Application.created_at.desc())
        .first()
    )


def _dump_db_artifacts(run_dir: Path, email: str, application_id: str | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        user = _find_user(db, email)
        app_row = None

        if application_id:
            app_row = db.query(Application).filter(Application.id == UUID(application_id)).first()
        elif user:
            app_row = _find_latest_application_for_user(db, user.id)

        canonical_row = None
        synthesis_row = None

        if app_row:
            canonical_row = (
                db.query(CanonicalRecord)
                .filter(CanonicalRecord.application_id == app_row.id)
                .first()
            )
            synthesis_row = (
                db.query(SynthesisRecord)
                .filter(SynthesisRecord.application_id == app_row.id)
                .first()
            )

        db_payload = {
            "user": None if not user else {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
            },
            "application": _application_row_payload(app_row),
            "canonical_record": _record_payload(canonical_row, "canonical_data"),
            "synthesis_record": _record_payload(synthesis_row, "synthesis_output"),
        }

        _write_json(run_dir / "05_db_artifacts.json", db_payload)

        if canonical_row:
            _write_json(run_dir / "06_canonical_data.json", canonical_row.canonical_data)
        if synthesis_row:
            _write_json(run_dir / "07_synthesis_output.json", synthesis_row.synthesis_output)
            _write_json(run_dir / "08_policy_violations_log.json", synthesis_row.policy_violations_log)

        return db_payload
    finally:
        db.close()


def run(pdf_path: Path) -> int:
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    run_dir = _build_output_dir(pdf_path)
    run_dir.mkdir(parents=True, exist_ok=True)

    _write_json(
        run_dir / "00_run_metadata.json",
        {
            "started_at": datetime.now(timezone.utc),
            "api_base_url": API_BASE_URL,
            "pdf_path": str(pdf_path),
            "script": "run_stage_1_7_pipeline_debug.py",
            "note": "Intended to run inside the Docker api container.",
        },
    )

    with httpx.Client(timeout=600.0) as client:
        email, access_token = _register_and_login(client, run_dir)
        headers = {"Authorization": f"Bearer {access_token}"}

        with pdf_path.open("rb") as handle:
            upload_response = client.post(
                f"{API_BASE_URL}/applications/upload",
                headers=headers,
                files={"file": (pdf_path.name, handle, "application/pdf")},
            )

        _write_json(run_dir / "03_upload_response.json", _response_payload(upload_response))

        application_id = None
        upload_body = None
        try:
            upload_body = upload_response.json()
        except ValueError:
            upload_body = None

        if isinstance(upload_body, dict):
            application_id = upload_body.get("id")

        db_payload = _dump_db_artifacts(run_dir, email, application_id)

        latest_app = db_payload.get("application") or {}
        resolved_application_id = application_id or latest_app.get("id")

        if resolved_application_id:
            app_get_response = client.get(
                f"{API_BASE_URL}/applications/{resolved_application_id}",
                headers=headers,
            )
            _write_json(run_dir / "04_application_get_response.json", _response_payload(app_get_response))

        summary = {
            "upload_status_code": upload_response.status_code,
            "application_id": resolved_application_id,
            "pipeline_status": latest_app.get("pipeline_status"),
            "policy_passed": (db_payload.get("synthesis_record") or {}).get("policy_passed"),
            "run_dir": str(run_dir),
        }
        _write_json(run_dir / "09_summary.json", summary)

        summary_lines = [
            f"Run directory: {run_dir}",
            f"Upload status: {upload_response.status_code}",
            f"Application ID: {resolved_application_id}",
            f"Pipeline status: {latest_app.get('pipeline_status')}",
            f"Policy passed: {(db_payload.get('synthesis_record') or {}).get('policy_passed')}",
        ]
        _write_text(run_dir / "10_summary.txt", "\n".join(summary_lines) + "\n")

        print("\n".join(summary_lines))

        if upload_response.status_code >= 400:
            return 2
        if latest_app.get("pipeline_status") != "complete":
            return 3
        if (db_payload.get("synthesis_record") or {}).get("policy_passed") is not True:
            return 4
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one PDF through the live Stage 1.7 API pipeline and dump DB artifacts."
    )
    parser.add_argument(
        "--pdf",
        default=DEFAULT_PDF,
        help="Path to the PDF to upload. Defaults to a sample file in tests/pdfs.",
    )
    args = parser.parse_args()

    return run(Path(args.pdf))


if __name__ == "__main__":
    raise SystemExit(main())
