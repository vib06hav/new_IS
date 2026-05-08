import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.interview_generator import generate_interview
from app.policy.guard import validate_question_groups


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _resolve_trace_input(path_arg: str | None) -> Path:
    if path_arg:
        candidate = Path(path_arg)
        return candidate if candidate.is_absolute() else (PROJECT_ROOT / candidate)

    trace_root = PROJECT_ROOT / "dev" / "generated" / "test-outputs" / "stage_1_8_traces"
    candidates = sorted(trace_root.glob("*/30_call_3_input.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(
            "No trace input found. Run dev/scripts/run_stage_1_8_trace.py first or pass --input."
        )
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rerun only Call 3 from a saved Stage 1.8 trace input."
    )
    parser.add_argument(
        "--input",
        help="Path to a saved 30_call_3_input.json file. Defaults to the latest trace artifact.",
    )
    parser.add_argument(
        "--output-prefix",
        default="call_3_rerun",
        help="Prefix used for output files written beside the input trace.",
    )
    args = parser.parse_args()

    input_path = _resolve_trace_input(args.input)
    payload = _load_json(input_path)

    bundle = payload.get("bundle")
    entity_id_map = payload.get("entity_id_map")
    if not isinstance(bundle, dict) or not isinstance(entity_id_map, list):
        raise ValueError(
            f"Trace input {input_path} is missing a valid bundle or entity_id_map."
        )

    output_dir = input_path.parent
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = f"{args.output_prefix}_{timestamp}"

    raw_output = generate_interview(bundle, entity_id_map)
    raw_output_path = output_dir / f"{prefix}_raw_output.txt"
    raw_output_path.write_text(raw_output, encoding="utf-8")

    validation = validate_question_groups(
        raw_text=raw_output,
        entity_id_map=entity_id_map,
        bundle=bundle,
    )
    validation_path = output_dir / f"{prefix}_validation.json"
    _write_json(validation_path, validation)

    summary = {
        "input": str(input_path),
        "raw_output_path": str(raw_output_path),
        "validation_path": str(validation_path),
        "passed": bool(validation.get("passed")),
        "question_group_count": len(
            ((validation.get("sanitized_output") or {}).get("question_groups") or [])
        )
        if isinstance(validation, dict)
        else 0,
    }
    summary_path = output_dir / f"{prefix}_summary.json"
    _write_json(summary_path, summary)

    print(json.dumps(summary, indent=2))
    return 0 if summary["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
