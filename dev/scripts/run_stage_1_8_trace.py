import argparse
import json
import sys
import traceback
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents import orchestrator as orchestrator_module
from app.agents.interview_generator import build_interview_messages
from app.agents.interview_synthesizer import build_interviewer_synthesis_messages
from app.agents.signal_interpreter import build_signal_interpreter_messages


DEFAULT_PDF = "demo-pdfs/Dummy App (1)_v8_filled.pdf"
OUTPUT_ROOT = Path("dev/generated/test-outputs/stage_1_8_traces")


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


def _build_output_dir(pdf_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = pdf_path.stem.replace(" ", "_").replace("(", "").replace(")", "")
    return OUTPUT_ROOT / f"{stamp}_{safe_name}"


def _record_call(run_dir: Path, stage_num: int, stage_slug: str, payload: Any) -> None:
    _write_json(run_dir / f"{stage_num:02d}_{stage_slug}.json", payload)


def run(pdf_path: Path) -> int:
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    run_dir = _build_output_dir(pdf_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    application_id = str(uuid.uuid4())

    _write_json(
        run_dir / "00_run_metadata.json",
        {
            "started_at": datetime.now(timezone.utc),
            "pdf_path": str(pdf_path),
            "application_id": application_id,
            "script": "run_stage_1_8_trace.py",
            "note": "Direct local Stage 1.8 run with per-call input/output tracing.",
        },
    )

    original_call_1 = orchestrator_module.interpret_signals
    original_call_2 = orchestrator_module.synthesize_interview_focus_areas
    original_call_3 = orchestrator_module.generate_interview

    def traced_call_1(projection: dict) -> str:
        messages = build_signal_interpreter_messages(projection)
        _record_call(
            run_dir,
            10,
            "call_1_input",
            {
                "projection": projection,
                "messages": messages,
            },
        )
        raw_output = original_call_1(projection)
        _write_text(run_dir / "11_call_1_raw_output.txt", raw_output)
        return raw_output

    def traced_call_2(bundle: dict) -> str:
        messages = build_interviewer_synthesis_messages(bundle)
        _record_call(
            run_dir,
            20,
            "call_2_input",
            {
                "bundle": bundle,
                "messages": messages,
            },
        )
        raw_output = original_call_2(bundle)
        _write_text(run_dir / "21_call_2_raw_output.txt", raw_output)
        return raw_output

    def traced_call_3(bundle: dict, entity_id_map: list) -> str:
        messages = build_interview_messages(bundle, entity_id_map)
        _record_call(
            run_dir,
            30,
            "call_3_input",
            {
                "bundle": bundle,
                "entity_id_map": entity_id_map,
                "messages": messages,
            },
        )
        raw_output = original_call_3(bundle, entity_id_map)
        _write_text(run_dir / "31_call_3_raw_output.txt", raw_output)
        return raw_output

    orchestrator_module.interpret_signals = traced_call_1
    orchestrator_module.synthesize_interview_focus_areas = traced_call_2
    orchestrator_module.generate_interview = traced_call_3

    try:
        result = orchestrator_module.run_pipeline(application_id, str(pdf_path), db=None, stop_after_canonical=False)
        _write_json(run_dir / "40_pipeline_result.json", result)

        canonical_data = result.get("canonical_data")
        ros_v1 = result.get("ros_v1")
        validation_result = result.get("validation_result")

        if canonical_data is not None:
            _write_json(run_dir / "41_canonical_data.json", canonical_data)
        if ros_v1 is not None:
            _write_json(run_dir / "42_final_report.json", ros_v1)
        if validation_result is not None:
            _write_json(run_dir / "43_validation_result.json", validation_result)

        summary = {
            "application_id": application_id,
            "run_dir": str(run_dir),
            "passed": bool((validation_result or {}).get("passed")),
            "has_canonical_data": canonical_data is not None,
            "has_final_report": ros_v1 is not None,
            "focus_area_count": len((((ros_v1 or {}).get("page_4_focus_areas") or {}).get("focus_areas") or []))
            if isinstance(ros_v1, dict)
            else 0,
            "question_group_count": len((((ros_v1 or {}).get("page_5_question_groups") or {}).get("question_groups") or []))
            if isinstance(ros_v1, dict)
            else 0,
        }
        _write_json(run_dir / "99_summary.json", summary)

        print(f"Trace complete. Artifacts saved to: {run_dir}")
        print(json.dumps(summary, indent=2))
        return 0 if summary["has_final_report"] and summary["passed"] else 2
    except Exception as exc:
        _write_json(
            run_dir / "98_exception.json",
            {
                "error_type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        print(f"Run failed. See: {run_dir / '98_exception.json'}", file=sys.stderr)
        return 3
    finally:
        orchestrator_module.interpret_signals = original_call_1
        orchestrator_module.synthesize_interview_focus_areas = original_call_2
        orchestrator_module.generate_interview = original_call_3


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one demo PDF through the local Stage 1.8 pipeline with full call tracing.")
    parser.add_argument(
        "--pdf",
        default=DEFAULT_PDF,
        help="Path to the PDF to process. Defaults to a sample file in demo-pdfs.",
    )
    args = parser.parse_args()
    return run(Path(args.pdf))


if __name__ == "__main__":
    raise SystemExit(main())
