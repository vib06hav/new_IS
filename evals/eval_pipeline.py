"""
eval_pipeline.py
----------------
Evaluation harness for the Interview Standardiser LLM pipeline.

Runs the two LLM calls (signal interpreter + interview generator) against a
set of golden canonical records and scores the outputs using an LLM judge.

Usage:
    python evals/eval_pipeline.py [--sample <sample_id>] [--call <1|2|all>]

Requirements:
    - The backend must be running (or the llm client must be importable).
    - Golden canonical input files must exist in evals/golden_inputs/.
    - Golden output references are in evals/golden_samples/.

Output:
    Prints a per-sample scorecard and writes a full run report to
    evals/reports/run_<timestamp>.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EVALS_DIR = Path(__file__).parent
GOLDEN_SAMPLES_DIR = EVALS_DIR / "golden_samples"
REPORTS_DIR = EVALS_DIR / "reports"

SAMPLE_IDS = ["sample_001", "sample_002", "sample_003"]

# Rubric weights for the judge
CALL_1_RUBRIC = {
    "signal_specificity":   0.35,   # Signals name things specific to this applicant
    "depth_opening_quality": 0.25,  # Depth openings are genuine, not generic questions
    "theme_independence":   0.20,   # Themes are genuinely distinct, not overlapping
    "prohibited_term_pass": 0.10,   # No prohibited terms (Admit, Reject, etc.)
    "structure_valid":      0.10,   # JSON schema is well-formed
}

CALL_2_RUBRIC = {
    "specific_referent_present": 0.30,  # Every question names something from this application
    "unanswerable_generically":  0.30,  # Questions cannot be answered without engaging the referent
    "serves_interview_direction": 0.25, # Questions serve the theme's interview_direction
    "prohibited_form_pass":       0.15, # No "Tell me about" / "Can you elaborate" forms
}

PROHIBITED_TERMS_CALL_1 = ["Admit", "Reject", "Likelihood", "Top candidate", "Risk factor"]
PROHIBITED_TERMS_CALL_2 = [
    "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor",
    "Strength", "Weakness", "Outstanding", "Exceptional", "Excellent",
    "Poor", "Impressive", "Concerning", "Tell me about", "Can you elaborate",
    "walk me through", "What drew you to",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_prohibited_terms(text: str, terms: list[str]) -> list[str]:
    """Return list of prohibited terms found in text."""
    found = []
    for term in terms:
        if term.lower() in text.lower():
            found.append(term)
    return found


def score_call_1_structural(output: dict) -> dict:
    """
    Performs deterministic (rule-based) checks on Call 1 output.
    These do not require an LLM judge.
    """
    violations = []
    signals = output.get("signals", [])
    themes = output.get("themes", [])

    # Schema checks
    if not signals:
        violations.append("No signals produced")
    if not themes:
        violations.append("No themes produced")
    if not (4 <= len(signals) <= 6):
        violations.append(f"Signal count out of range: {len(signals)} (expected 4-6)")
    if not (3 <= len(themes) <= 4):
        violations.append(f"Theme count out of range: {len(themes)} (expected 3-4)")

    # Prohibited term check across all signal text
    all_signal_text = " ".join(
        f"{s.get('title','')} {s.get('depth_opening','')} {s.get('why_it_matters','')}"
        for s in signals
    )
    found = check_prohibited_terms(all_signal_text, PROHIBITED_TERMS_CALL_1)
    if found:
        violations.append(f"Prohibited terms in signals: {found}")

    # Each theme must reference at least one signal
    signal_ids = {s["signal_id"] for s in signals}
    for theme in themes:
        for sid in theme.get("supporting_signal_ids", []):
            if sid not in signal_ids:
                violations.append(f"Theme {theme['theme_id']} references unknown signal {sid}")

    structure_score = 1.0 if not violations else max(0.0, 1.0 - 0.2 * len(violations))
    return {
        "violations": violations,
        "structure_score": round(structure_score, 2),
    }


def score_call_2_structural(output: dict) -> dict:
    """
    Performs deterministic checks on Call 2 output.
    """
    violations = []
    groups = output.get("question_groups", [])

    if not groups:
        violations.append("No question groups produced")

    for group in groups:
        questions = group.get("questions", [])
        if not (3 <= len(questions) <= 4):
            violations.append(
                f"Group {group.get('theme_id')} has {len(questions)} questions (expected 3-4)"
            )
        all_q_text = " ".join(questions)
        found = check_prohibited_terms(all_q_text, PROHIBITED_TERMS_CALL_2)
        if found:
            violations.append(
                f"Group {group.get('theme_id')} uses prohibited forms/terms: {found}"
            )

    structure_score = 1.0 if not violations else max(0.0, 1.0 - 0.2 * len(violations))
    return {
        "violations": violations,
        "structure_score": round(structure_score, 2),
    }


def build_judge_prompt_call_1(output: dict, reference: dict) -> str:
    """Builds the LLM judge prompt for Call 1 signal quality."""
    return f"""
You are evaluating the output of an LLM that generates interview signals for
a student application review system.

Score the OUTPUT below against the REFERENCE on the following criteria.
Return a JSON object with scores from 0.0 to 1.0 per criterion and a brief
justification per criterion.

CRITERIA:
1. signal_specificity: Are signals specific to this applicant, or could they
   be written about any applicant with a similar profile?
2. depth_opening_quality: Do depth_openings name genuine, usable interview
   territory - not generic questions dressed as analysis?
3. theme_independence: Are the themes genuinely distinct, or do they overlap
   in coverage?

REFERENCE (accepted golden output):
{json.dumps(reference, indent=2)}

OUTPUT TO JUDGE:
{json.dumps(output, indent=2)}

Return ONLY valid JSON in this format:
{{
  "signal_specificity": {{"score": 0.0, "justification": "..."}},
  "depth_opening_quality": {{"score": 0.0, "justification": "..."}},
  "theme_independence": {{"score": 0.0, "justification": "..."}}
}}
"""


def build_judge_prompt_call_2(output: dict, reference: dict, signals: dict) -> str:
    """Builds the LLM judge prompt for Call 2 question quality."""
    return f"""
You are evaluating the output of an LLM that generates interview questions
for a student interview review system.

Score the OUTPUT below on the following criteria:
1. specific_referent_present: Does each question name something specific from
   this particular applicant's profile (not a general category)?
2. unanswerable_generically: Can each question be answered well only by
   engaging the specific referent named - or could a well-spoken student
   answer it without engaging the referent at all?
3. serves_interview_direction: Does each question group serve the theme's
   interview_direction as defined in the signal data?

SIGNALS & THEMES CONTEXT:
{json.dumps(signals, indent=2)}

REFERENCE (accepted golden questions):
{json.dumps(reference, indent=2)}

OUTPUT TO JUDGE:
{json.dumps(output, indent=2)}

Return ONLY valid JSON in this format:
{{
  "specific_referent_present": {{"score": 0.0, "justification": "..."}},
  "unanswerable_generically": {{"score": 0.0, "justification": "..."}},
  "serves_interview_direction": {{"score": 0.0, "justification": "..."}}
}}
"""


# ---------------------------------------------------------------------------
# Stub LLM judge (replace with real generate() call when running live)
# ---------------------------------------------------------------------------

def run_judge(prompt: str) -> dict:
    """
    Stub for the LLM judge call.
    Replace with: generate([{"role": "user", "content": prompt}], call_label="judge")
    and parse the returned JSON.
    """
    print("    [JUDGE] LLM judge call stubbed - returning mock scores.")
    return {
        "score_a": {"score": 0.82, "justification": "Stub value - run with live LLM."},
        "score_b": {"score": 0.75, "justification": "Stub value - run with live LLM."},
        "score_c": {"score": 0.88, "justification": "Stub value - run with live LLM."},
    }


# ---------------------------------------------------------------------------
# Core eval logic
# ---------------------------------------------------------------------------

def eval_sample(sample_id: str, run_call: str) -> dict:
    print(f"\n{'='*60}")
    print(f"  Evaluating: {sample_id}")
    print(f"{'='*60}")

    result = {"sample_id": sample_id, "call_1": None, "call_2": None}

    # ---- Call 1 ----
    if run_call in ("1", "all"):
        ref_path = GOLDEN_SAMPLES_DIR / f"{sample_id}_call1_signals.json"
        if not ref_path.exists():
            print(f"  [SKIP] Call 1 reference not found: {ref_path.name}")
        else:
            reference = load_json(ref_path)

            # In a real run, load actual pipeline output from the run's output directory.
            # For now, we score the reference against itself (should always be ~1.0).
            output = reference  # TODO: replace with live pipeline output

            print("  [CALL 1] Running structural checks...")
            structural = score_call_1_structural(output)
            if structural["violations"]:
                for v in structural["violations"]:
                    print(f"    ⚠  {v}")
            else:
                print("    ✓  No structural violations")

            print("  [CALL 1] Running LLM judge...")
            judge_prompt = build_judge_prompt_call_1(output, reference)
            judge_scores = run_judge(judge_prompt)

            # Aggregate
            weighted = structural["structure_score"] * CALL_1_RUBRIC["structure_valid"]
            for key, stub_val in [
                ("signal_specificity", 0.82),
                ("depth_opening_quality", 0.76),
                ("theme_independence", 0.89),
                ("prohibited_term_pass", 1.0 if not structural["violations"] else 0.5),
            ]:
                weighted += stub_val * CALL_1_RUBRIC.get(key, 0)

            result["call_1"] = {
                "structural": structural,
                "judge_raw": judge_scores,
                "aggregate_score": round(weighted, 3),
            }
            print(f"  [CALL 1] Aggregate score: {result['call_1']['aggregate_score']:.3f}")

    # ---- Call 2 ----
    if run_call in ("2", "all"):
        ref_path = GOLDEN_SAMPLES_DIR / f"{sample_id}_call2_questions.json"
        sig_path = GOLDEN_SAMPLES_DIR / f"{sample_id}_call1_signals.json"
        if not ref_path.exists():
            print(f"  [SKIP] Call 2 reference not found: {ref_path.name}")
        else:
            reference = load_json(ref_path)
            signals = load_json(sig_path) if sig_path.exists() else {}
            output = reference  # TODO: replace with live pipeline output

            print("  [CALL 2] Running structural checks...")
            structural = score_call_2_structural(output)
            if structural["violations"]:
                for v in structural["violations"]:
                    print(f"    ⚠  {v}")
            else:
                print("    ✓  No structural violations")

            print("  [CALL 2] Running LLM judge...")
            judge_prompt = build_judge_prompt_call_2(output, reference, signals)
            judge_scores = run_judge(judge_prompt)

            weighted = structural["structure_score"] * CALL_2_RUBRIC["prohibited_form_pass"]
            for key, stub_val in [
                ("specific_referent_present", 0.80),
                ("unanswerable_generically", 0.73),
                ("serves_interview_direction", 0.85),
            ]:
                weighted += stub_val * CALL_2_RUBRIC.get(key, 0)

            result["call_2"] = {
                "structural": structural,
                "judge_raw": judge_scores,
                "aggregate_score": round(weighted, 3),
            }
            print(f"  [CALL 2] Aggregate score: {result['call_2']['aggregate_score']:.3f}")

    return result


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

def write_report(results: list[dict]) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"run_{timestamp}.json"

    total_call_1 = [r["call_1"]["aggregate_score"] for r in results if r.get("call_1")]
    total_call_2 = [r["call_2"]["aggregate_score"] for r in results if r.get("call_2")]

    summary = {
        "run_timestamp": timestamp,
        "samples_evaluated": len(results),
        "call_1_mean_score": round(sum(total_call_1) / len(total_call_1), 3) if total_call_1 else None,
        "call_2_mean_score": round(sum(total_call_2) / len(total_call_2), 3) if total_call_2 else None,
        "results": results,
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return report_path


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run eval harness for IS pipeline LLM calls.")
    parser.add_argument(
        "--sample",
        default="all",
        help="Sample ID to evaluate (e.g. sample_001), or 'all' for all samples.",
    )
    parser.add_argument(
        "--call",
        default="all",
        choices=["1", "2", "all"],
        help="Which LLM call to evaluate: 1, 2, or all.",
    )
    args = parser.parse_args()

    samples = SAMPLE_IDS if args.sample == "all" else [args.sample]

    print(f"\nInterview Standardiser - LLM Eval Harness")
    print(f"Samples : {samples}")
    print(f"Calls   : {args.call}")
    print(f"Mode    : STUB (set run_judge() to a live call to score real outputs)\n")

    results = []
    for sample_id in samples:
        result = eval_sample(sample_id, run_call=args.call)
        results.append(result)

    report_path = write_report(results)

    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for r in results:
        c1 = f"{r['call_1']['aggregate_score']:.3f}" if r.get("call_1") else "skipped"
        c2 = f"{r['call_2']['aggregate_score']:.3f}" if r.get("call_2") else "skipped"
        print(f"  {r['sample_id']:15s}  call_1={c1}  call_2={c2}")

    print(f"\nFull report written to: {report_path}\n")


if __name__ == "__main__":
    main()
