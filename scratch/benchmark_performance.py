import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

# -------------------------------------------------------
# Silence noisy low-level loggers BEFORE importing app code
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(levelname)s [%(name)s] %(message)s')
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("chardet").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("benchmark_v2")

from app.agents.orchestrator import run_pipeline
from app.agents.signal_interpreter import interpret_signals
from app.agents.bundle_constructor import construct_bundle
from app.agents.interview_generator import generate_interview
from app.projection.ros_projector import project_ros
from app.agents.signal_detector import detect_signals
from app.agents.projection_builder import build_projection
from app.policy.guard import validate_signals, sanitise_llm_output, validate_question_groups
from app.config import settings


# -------------------------------------------------------
# STEP 1: Ingest PDF into memory only (NO DB writes)
# -------------------------------------------------------
def ingest_pdf_to_canonical(pdf_path: str) -> dict:
    logger.info(f"Ingesting PDF (in-memory, no DB): {pdf_path}")
    app_id = str(uuid.uuid4())
    result = run_pipeline(app_id, pdf_path, db=None, stop_after_canonical=True)
    canonical_data = result.get("canonical_data")
    if not canonical_data:
        raise RuntimeError("Ingestion returned no canonical data.")
    return canonical_data


# -------------------------------------------------------
# STEP 2: Build static projection context (built once, shared by all 14 models)
# -------------------------------------------------------
def build_static_context(canonical_data: dict) -> dict:
    logger.info("Building Static Projection (shared across all models)...")
    _, _, _, _, entity_id_map = project_ros(canonical_data)
    deterministic_signals = detect_signals(canonical_data, entity_id_map)
    projection = build_projection(canonical_data, entity_id_map, deterministic_signals)
    essay_fragments = projection.get("essay_fragments", [])
    return {
        "canonical_data": canonical_data,
        "entity_id_map": entity_id_map,
        "deterministic_signals": deterministic_signals,
        "projection": projection,
        "essay_fragments": essay_fragments,
        "valid_fragment_ids": {f.get("fragment_id") for f in essay_fragments if f.get("fragment_id")},
        "valid_entity_ids": {e.get("entity_id") for e in entity_id_map if e.get("entity_id")},
    }


# -------------------------------------------------------
# STEP 3: Run the two-call pipeline for a single model
# Returns a result dict with all metrics and output
# -------------------------------------------------------
def run_two_call_pipeline(model_id: str, ctx: dict) -> dict:
    result = {
        "model_id": model_id,
        "status": "PASSED",
        "call_1_latency": 0.0,
        "call_2_latency": 0.0,
        "signal_count": 0,
        "theme_count": 0,
        "question_group_count": 0,
        "error_msg": "",
        "call_1_output": None,
        "call_2_output": None,
    }

    # Force this model for both calls
    settings.AICREDITS_GENERATION_MODEL_PRIMARY = model_id
    settings.AICREDITS_GENERATION_MODEL_FALLBACK = model_id
    settings.LLM_MODEL_NAME = model_id

    try:
        # ---- CALL 1: Signal Interpreter ----
        t0 = time.time()
        try:
            raw_call_1 = interpret_signals(ctx["projection"])
        except Exception as e:
            result["status"] = "CALL_1_API_ERROR"
            result["error_msg"] = str(e)
            result["call_1_latency"] = round(time.time() - t0, 2)
            return result

        result["call_1_latency"] = round(time.time() - t0, 2)

        raw_json_1 = json.loads(raw_call_1)
        result["signal_count"] = len(raw_json_1.get("signals", []))
        result["theme_count"] = len(raw_json_1.get("themes", []))

        # Sanitise & Validate Call 1
        sanitised_1 = sanitise_llm_output(raw_json_1, ctx["valid_fragment_ids"], ctx["valid_entity_ids"])

        val_res_1 = validate_signals(
            json.dumps(sanitised_1),
            ctx["entity_id_map"],
            ctx["deterministic_signals"],
            essay_fragments=ctx["essay_fragments"]
        )

        if not val_res_1["passed"]:
            result["status"] = "GUARD_1_FAILED"
            result["error_msg"] = val_res_1.get("violations_log", [{}])[0].get("type", "logic_error")
            result["call_1_output"] = sanitised_1
            return result

        validated_call_1 = val_res_1["sanitized_output"]
        result["call_1_output"] = validated_call_1

        # ---- BRIDGE: Bundle Constructor ----
        bundle = construct_bundle(validated_call_1, ctx["canonical_data"], ctx["entity_id_map"])

        # ---- CALL 2: Interview Generator ----
        t1 = time.time()
        try:
            raw_call_2 = generate_interview(bundle, ctx["entity_id_map"])
        except Exception as e:
            result["status"] = "CALL_2_API_ERROR"
            result["error_msg"] = str(e)
            result["call_2_latency"] = round(time.time() - t1, 2)
            return result

        result["call_2_latency"] = round(time.time() - t1, 2)

        # Validate Call 2
        val_res_2 = validate_question_groups(raw_call_2, ctx["entity_id_map"], bundle)

        if not val_res_2["passed"]:
            result["status"] = "GUARD_2_FAILED"
            result["error_msg"] = val_res_2.get("violations_log", [{}])[0].get("type", "logic_error")

        validated_call_2 = val_res_2.get("sanitized_output", {})
        result["question_group_count"] = len(validated_call_2.get("question_groups", []))
        result["call_2_output"] = validated_call_2

    except Exception as e:
        result["status"] = "CRASH"
        result["error_msg"] = str(e)
        logger.error(f"Unexpected crash for {model_id}: {e}")

    return result


# -------------------------------------------------------
# MAIN BENCHMARK RUNNER
# -------------------------------------------------------
def run_benchmark():
    pdf_file = "tests/pdfs/Dummy App (2)_v8_filled.pdf"
    if not os.path.exists(pdf_file):
        logger.error(f"Target PDF not found: {pdf_file}")
        return

    # --- Ingest once ---
    canonical_data = ingest_pdf_to_canonical(pdf_file)

    # --- Build context once ---
    ctx = build_static_context(canonical_data)

    # --- 14-model list (gemini-2.0-flash removed as per user req) ---
    models_to_test = [
        # Ultra-Budget
        "google/gemini-2.5-flash-lite",
        "openai/gpt-4o-mini",
        "openai/gpt-5.4-nano",
        "anthropic/claude-3-haiku",
        # Budget
        "google/gemini-3.1-flash-lite-preview",
        "openai/gpt-4.1-mini",
        "google/gemini-2.5-flash",          # ← has native reasoning
        # Mid-Range
        "google/gemini-3-flash-preview",
        "anthropic/claude-3.5-haiku",
        "openai/gpt-5.4-mini",
        "anthropic/claude-haiku-4.5",        # ← extended thinking capable
        # Premium
        "openai/gpt-5",
        "google/gemini-2.5-pro",             # ← has native reasoning
        "openai/gpt-4o",
    ]

    results_dir = Path("provider_testing/benchmarking_v2")
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    for idx, model_id in enumerate(models_to_test):
        logger.info(f"\n[{idx+1}/{len(models_to_test)}] ===== Running: {model_id} =====")

        res = run_two_call_pipeline(model_id, ctx)
        all_results.append(res)

        logger.info(
            f"  Status={res['status']} | "
            f"Call1={res['call_1_latency']}s | Call2={res['call_2_latency']}s | "
            f"Signals={res['signal_count']} | Themes={res['theme_count']} | "
            f"QuestionGroups={res['question_group_count']}"
        )

        # Save per-model combined JSON
        if res["status"] == "PASSED":
            provider = model_id.split("/")[0]
            model_folder = results_dir / provider
            model_folder.mkdir(parents=True, exist_ok=True)
            clean_name = model_id.replace("/", "_")
            output = {
                "metrics": {
                    "model": model_id,
                    "status": res["status"],
                    "call_1_latency_seconds": res["call_1_latency"],
                    "call_2_latency_seconds": res["call_2_latency"],
                    "signal_count": res["signal_count"],
                    "theme_count": res["theme_count"],
                    "question_group_count": res["question_group_count"],
                },
                "call_1_signals_themes": res["call_1_output"],
                "call_2_question_groups": res["call_2_output"],
            }
            with open(model_folder / f"{clean_name}.json", "w") as f:
                json.dump(output, f, indent=2)
            logger.info(f"  Saved: provider_testing/benchmarking_v2/{provider}/{clean_name}.json")

        # Respect rate limits between models
        if idx < len(models_to_test) - 1:
            time.sleep(3)

    # --- Write final markdown comparison report ---
    report_lines = [
        "# Master Model Benchmark Comparison Report — Dummy App 2\n",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}  ",
        f"**PDF:** Dummy App (2) — Ananya Kapoor\n",
        "| # | Model | Status | Call 1 (s) | Call 2 (s) | Signals | Themes | Q-Groups | Error |",
        "|---|-------|--------|------------|------------|---------|--------|----------|-------|",
    ]
    for i, res in enumerate(all_results):
        report_lines.append(
            f"| {i+1} | `{res['model_id']}` | {res['status']} | "
            f"{res['call_1_latency']} | {res['call_2_latency']} | "
            f"{res['signal_count']} | {res['theme_count']} | "
            f"{res['question_group_count']} | {res['error_msg']} |"
        )

    report_path = results_dir / "benchmark_comparison_report.md"
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))

    logger.info(f"\nBenchmark complete. Report: {report_path}")


if __name__ == "__main__":
    run_benchmark()
