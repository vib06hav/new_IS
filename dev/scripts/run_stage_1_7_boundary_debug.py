import argparse
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.bundle_constructor import construct_bundle
from app.agents.interview_generator import generate_interview
from app.agents.interview_generator import build_interview_messages
from app.agents.projection_builder import build_projection
from app.agents.signal_detector import detect_signals
from app.agents.signal_interpreter import interpret_signals
from app.agents.signal_interpreter import build_signal_interpreter_messages
from app.database import SessionLocal
from app.llm.token_counter import estimate_messages_tokens, estimate_text_tokens
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.policy.guard import validate_signals, validate_themes
from app.projection.ros_projector import project_ros


OUTPUT_ROOT = Path("dev/generated/test-outputs/stage_1_7_boundary_runs")


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


def _latest_canonical_record(db) -> CanonicalRecord | None:
    return db.query(CanonicalRecord).order_by(CanonicalRecord.created_at.desc()).first()


def _canonical_record_for_application(db, application_id: str) -> CanonicalRecord | None:
    return (
        db.query(CanonicalRecord)
        .filter(CanonicalRecord.application_id == UUID(application_id))
        .first()
    )


def _application_row(db, application_id: UUID | None) -> Application | None:
    if not application_id:
        return None
    return db.query(Application).filter(Application.id == application_id).first()


def _build_output_dir(application_id: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return OUTPUT_ROOT / f"{stamp}_{application_id}"


def run(application_id: str | None) -> int:
    db = SessionLocal()
    try:
        canonical_record = (
            _canonical_record_for_application(db, application_id)
            if application_id
            else _latest_canonical_record(db)
        )
        if not canonical_record:
            print("No canonical record found.", file=sys.stderr)
            return 1

        resolved_application_id = str(canonical_record.application_id)
        run_dir = _build_output_dir(resolved_application_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        app_row = _application_row(db, canonical_record.application_id)
        canonical_data = canonical_record.canonical_data

        _write_json(
            run_dir / "00_run_metadata.json",
            {
                "started_at": datetime.now(timezone.utc),
                "script": "run_stage_1_7_boundary_debug.py",
                "application_id": resolved_application_id,
                "canonical_record_id": canonical_record.id,
                "application_status": None if not app_row else app_row.pipeline_status,
            },
        )
        _write_json(run_dir / "01_canonical_data.json", canonical_data)

        page_1, page_2, page_3, annotated_canonical, entity_id_map = project_ros(canonical_data)
        _write_json(run_dir / "02_page_1.json", page_1)
        _write_json(run_dir / "03_page_2.json", page_2)
        _write_json(run_dir / "04_page_3.json", page_3)
        _write_json(run_dir / "05_annotated_canonical.json", annotated_canonical)
        _write_json(run_dir / "06_entity_id_map.json", entity_id_map)

        deterministic_signals = detect_signals(canonical_data, entity_id_map)
        _write_json(run_dir / "07_deterministic_signals.json", deterministic_signals)

        call_1_projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
        _write_json(run_dir / "08_call_1_projection.json", call_1_projection)
        call_1_messages = build_signal_interpreter_messages(call_1_projection)
        _write_json(
            run_dir / "08b_call_1_token_metrics.json",
            {
                "call_label": "call_1",
                "prompt_token_estimate": estimate_messages_tokens(call_1_messages),
                "projection_token_estimate": estimate_text_tokens(json.dumps(call_1_projection, ensure_ascii=False)),
            },
        )

        raw_call_1_output = interpret_signals(call_1_projection)
        _write_text(run_dir / "09_raw_call_1_output.txt", raw_call_1_output)

        call_1_validation = validate_signals(raw_call_1_output, entity_id_map, deterministic_signals)
        _write_json(run_dir / "10_call_1_validation.json", call_1_validation)
        _write_json(run_dir / "10a_call_1_normalized_output.json", call_1_validation.get("normalized_output"))

        if not call_1_validation.get("passed"):
            summary = {
                "application_id": resolved_application_id,
                "call_1_passed": False,
                "call_2_attempted": False,
                "run_dir": str(run_dir),
            }
            _write_json(run_dir / "99_summary.json", summary)
            print(f"Run directory: {run_dir}")
            print("Call 1 validation failed.")
            return 2

        interpreted_signals = call_1_validation["sanitized_output"]["interpreted_signals"]
        _write_json(run_dir / "11_interpreted_signals.json", interpreted_signals)

        signal_evidence_bundle = construct_bundle(interpreted_signals, canonical_data, entity_id_map)
        _write_json(run_dir / "12_signal_evidence_bundle.json", signal_evidence_bundle)
        call_2_messages = build_interview_messages(signal_evidence_bundle, entity_id_map)
        _write_json(
            run_dir / "12b_call_2_token_metrics.json",
            {
                "call_label": "call_2",
                "prompt_token_estimate": estimate_messages_tokens(call_2_messages),
                "bundle_token_estimate": estimate_text_tokens(json.dumps(signal_evidence_bundle, ensure_ascii=False)),
            },
        )

        raw_call_2_output = generate_interview(signal_evidence_bundle, entity_id_map)
        _write_text(run_dir / "13_raw_call_2_output.txt", raw_call_2_output)
        _write_json(
            run_dir / "13b_call_output_token_metrics.json",
            {
                "call_1_output_token_estimate": estimate_text_tokens(raw_call_1_output),
                "call_2_output_token_estimate": estimate_text_tokens(raw_call_2_output),
            },
        )

        call_2_validation = validate_themes(raw_call_2_output, entity_id_map, signal_evidence_bundle)
        _write_json(run_dir / "14_call_2_validation.json", call_2_validation)
        _write_json(run_dir / "14a_call_2_normalized_output.json", call_2_validation.get("normalized_output"))

        summary = {
            "application_id": resolved_application_id,
            "call_1_passed": True,
            "call_2_passed": call_2_validation.get("passed"),
            "run_dir": str(run_dir),
        }
        _write_json(run_dir / "99_summary.json", summary)
        _write_text(
            run_dir / "99_summary.txt",
            "\n".join(
                [
                    f"Run directory: {run_dir}",
                    f"Application ID: {resolved_application_id}",
                    "Call 1 validation: passed",
                    f"Call 2 validation: {call_2_validation.get('passed')}",
                ]
            )
            + "\n",
        )

        print(f"Run directory: {run_dir}")
        print(f"Application ID: {resolved_application_id}")
        print("Call 1 validation: passed")
        print(f"Call 2 validation: {call_2_validation.get('passed')}")
        return 0 if call_2_validation.get("passed") else 3
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay the Stage 1.7 LLM boundary from a persisted canonical record."
    )
    parser.add_argument(
        "--application-id",
        help="Optional application UUID. Defaults to the latest canonical record.",
    )
    args = parser.parse_args()
    return run(args.application_id)


if __name__ == "__main__":
    raise SystemExit(main())
