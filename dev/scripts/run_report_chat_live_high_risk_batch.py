import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import ValidationError

from app.api.helpers import build_review_package_summary, get_final_report
from app.api.schemas import ReportChatResponse
from app.database import SessionLocal
from app.llm.client import LLMClientError, generate
from app.llm.token_counter import estimate_messages_tokens, estimate_text_tokens
from app.models.application import Application
from app.models.final_report import FinalReport
from app.report_chat import (
    _build_report_chat_messages,
    _extract_json_candidate,
    _recover_partial_report_chat_payload,
    build_report_chat_context,
    validate_report_chat_question,
)


HIGH_RISK_QUESTIONS = [
    "Summarise the whole application in detail.",
    "List everything clearly from this report.",
    "Give all details about this candidate.",
    "What is this candidate like overall and why?",
    "Explain themes and give interview questions.",
    "Compare academics, tests, activities, and essays.",
    "How should I evaluate this candidate overall?",
    "What really stands out and why?",
    "What matters most in this application?",
    "What are the weaknesses and what should I ask next?",
    "What are the strengths and what should the interviewer probe?",
    "Compare academics and test performance and tell me if there is a gap.",
    "Summarise academics, activities, and leadership in bullets.",
    "Give a full profile plus the most important concerns.",
    "List all signals and explain why they matter.",
    "Explain every theme and the evidence behind it.",
    "Tell me everything important here in one answer.",
    "Give me a deep analysis of this applicant.",
    "What should the interviewer focus on and why?",
    "Is this a good or bad profile and what follow-up questions should I ask?",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run 20 high-risk live report-chat prompts and persist raw model outputs.",
    )
    parser.add_argument(
        "--application-id",
        help="Application UUID to use. If omitted, the most recent application with a final report is used.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output directory. Defaults to tests/outputs/report_chat_live_high_risk/<timestamp>.",
    )
    return parser


def default_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = PROJECT_ROOT / "tests" / "outputs" / "report_chat_live_high_risk" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def select_application(db, requested_application_id: str | None) -> tuple[Application, FinalReport]:
    query = (
        db.query(Application, FinalReport)
        .join(FinalReport, FinalReport.application_id == Application.id)
        .order_by(FinalReport.created_at.desc())
    )

    if requested_application_id:
        application_uuid = UUID(requested_application_id)
        row = query.filter(Application.id == application_uuid).first()
        if row is None:
            raise SystemExit(f"No application with a final report found for application_id={requested_application_id}")
        return row

    row = query.first()
    if row is None:
        raise SystemExit("No applications with final reports were found in the database.")
    return row


def run_question(
    *,
    output_dir: Path,
    index: int,
    question: str,
    review_pages_1_3: dict[str, Any],
    final_report_content: dict[str, Any],
) -> dict[str, Any]:
    prefix = f"{index:02d}"
    question_dir = output_dir / f"{prefix}_{slugify(question)}"
    question_dir.mkdir(parents=True, exist_ok=True)

    question_status: dict[str, Any] = {
        "index": index,
        "question": question,
        "status": "unknown",
    }

    write_text(question_dir / "01_question.txt", question)

    try:
        validated_question = validate_report_chat_question(question, max_chars=500, max_words=80)
    except Exception as exc:
        question_status["status"] = "question_rejected"
        question_status["error"] = str(exc)
        write_json(question_dir / "99_result_summary.json", question_status)
        return question_status

    context = build_report_chat_context(validated_question, review_pages_1_3, final_report_content)
    messages = _build_report_chat_messages(validated_question, context)
    write_json(question_dir / "02_context.json", context)
    write_json(question_dir / "03_messages.json", messages)

    question_status["detected_operation"] = context["detected_operation"]
    question_status["detected_target"] = context["detected_target"]
    question_status["source_scope"] = context["source_scope"]
    question_status["selected_sections"] = context["selected_sections"]
    question_status["estimated_prompt_tokens"] = estimate_messages_tokens(messages)

    if context.get("not_found_summary") and not context.get("section_targets"):
        raw_output = json.dumps(
            {
                "answer_summary": str(context["not_found_summary"]),
                "results": [],
                "not_found": True,
                "response_state": "clean",
            }
        )
        write_text(question_dir / "04_raw_output.txt", raw_output)
        write_json(question_dir / "05_parsed_output.json", json.loads(raw_output))
        question_status["status"] = "safe_not_found_without_llm"
        question_status["estimated_response_tokens"] = estimate_text_tokens(raw_output)
        write_json(question_dir / "99_result_summary.json", question_status)
        return question_status

    try:
        raw_output = generate(messages, call_label="report_chat")
    except LLMClientError as exc:
        question_status["status"] = "transport_error"
        question_status["error"] = str(exc)
        write_json(question_dir / "99_result_summary.json", question_status)
        return question_status

    write_text(question_dir / "04_raw_output.txt", raw_output)
    question_status["estimated_response_tokens"] = estimate_text_tokens(raw_output)

    json_candidate = _extract_json_candidate(raw_output)
    write_text(question_dir / "05_json_candidate.txt", json_candidate)

    try:
        parsed_payload = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        recovered_payload = _recover_partial_report_chat_payload(raw_output)
        if recovered_payload is None:
            question_status["status"] = "invalid_json"
            question_status["error"] = str(exc)
            write_json(question_dir / "99_result_summary.json", question_status)
            return question_status

        parsed_payload = recovered_payload
        question_status["recovered_partial_json"] = True

    write_json(question_dir / "06_parsed_output.json", parsed_payload)

    try:
        validated_response = ReportChatResponse.model_validate(parsed_payload)
    except ValidationError as exc:
        question_status["status"] = "schema_invalid"
        question_status["error"] = exc.errors()
        write_json(question_dir / "07_schema_errors.json", exc.errors())
        write_json(question_dir / "99_result_summary.json", question_status)
        return question_status

    if question_status.get("recovered_partial_json"):
        question_status["status"] = "recovered_not_found" if validated_response.not_found else "recovered_success"
    else:
        question_status["status"] = "not_found" if validated_response.not_found else "success"
    question_status["result_count"] = len(validated_response.results)
    write_json(question_dir / "99_result_summary.json", question_status)
    return question_status


def slugify(text: str) -> str:
    lowered = text.lower()
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in lowered)
    compact = "_".join(part for part in cleaned.split("_") if part)
    return compact[:60] or "question"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        application, final_report = select_application(db, args.application_id)
        review_package = build_review_package_summary(application, None)
        if review_package is None:
            from app.api.helpers import get_canonical_record

            canonical_record = get_canonical_record(db, application.id)
            review_package = build_review_package_summary(application, canonical_record)
        if review_package is None:
            raise SystemExit(f"Could not build review package for application_id={application.id}")

        persisted_final_report = get_final_report(db, application.id)
        final_report_content = persisted_final_report.content if persisted_final_report else final_report.content
        if not isinstance(final_report_content, dict):
            raise SystemExit(f"Final report content is unavailable for application_id={application.id}")

        run_metadata = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "application_id": str(application.id),
            "application_display_id": application.display_id,
            "question_count": len(HIGH_RISK_QUESTIONS),
            "output_dir": str(output_dir),
        }
        write_json(output_dir / "00_run_metadata.json", run_metadata)

        results: list[dict[str, Any]] = []
        for index, question in enumerate(HIGH_RISK_QUESTIONS, start=1):
            results.append(
                run_question(
                    output_dir=output_dir,
                    index=index,
                    question=question,
                    review_pages_1_3=review_package.pages_1_3.model_dump(),
                    final_report_content=final_report_content,
                )
            )

        summary = {
            "application_id": str(application.id),
            "application_display_id": application.display_id,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "question_count": len(results),
            "status_counts": {},
            "results": results,
        }
        for result in results:
            summary["status_counts"][result["status"]] = summary["status_counts"].get(result["status"], 0) + 1
        write_json(output_dir / "99_batch_summary.json", summary)

        print(f"Live report-chat high-risk batch complete for application {application.display_id} ({application.id})")
        print(f"Output directory: {output_dir}")
        for status, count in sorted(summary["status_counts"].items()):
            print(f"{status}: {count}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
