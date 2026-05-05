import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.helpers import build_review_package_summary, get_final_report
from app.auth.security import create_access_token
from app.database import SessionLocal
from app.llm.client import LLMClientError, generate
from app.models.application import Application
from app.models.final_report import FinalReport
from app.models.user import User
from app.report_chat import _build_report_chat_messages, build_report_chat_context, validate_report_chat_question


TEST_QUESTIONS = [
    "What are the 10th and 12th grade marks for this applicant?",
    "List the extracurricular activities and leadership roles mentioned in the report.",
    "What is the JEE score or percentile recorded for this candidate?",
    "Summarize the key themes identified in the Focus Areas (Page 4).",
    "How does the applicant's background or personal journey influence their interest in technology?",
    "What specific technical projects did the applicant describe in their essays?",
    "What are the recommended opening questions for the interview from Page 5?",
    "What should I do next in the interview workflow?",
    "Based on the report, is this candidate recommended for admission?",
    "Compare the applicant's academic performance with their extracurricular engagement.",
    "Does the report mention any experience with Python or specific programming languages?",
    "Give me a high-level, objective overview of this applicant's profile."
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end live report-chat suite against the real API endpoint.",
    )
    parser.add_argument("--application-id", help="Application UUID to use. Defaults to latest application with final report.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL.")
    parser.add_argument(
        "--output-dir",
        help="Optional output directory. Defaults to tests/outputs/report_chat_endpoint_live/<timestamp>.",
    )
    parser.add_argument(
        "--skip-raw-diagnostic",
        action="store_true",
        help="Skip the extra direct model diagnostic call and only record endpoint results.",
    )
    parser.add_argument(
        "--max-http-retries",
        type=int,
        default=2,
        help="How many times to retry a request when the endpoint returns 429.",
    )
    parser.add_argument(
        "--retry-429-wait-seconds",
        type=float,
        default=15.0,
        help="How long to wait before retrying after a 429 response.",
    )
    return parser


def default_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = PROJECT_ROOT / "tests" / "outputs" / "report_chat_endpoint_live" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def slugify(text: str) -> str:
    lowered = text.lower()
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in lowered)
    compact = "_".join(part for part in cleaned.split("_") if part)
    return compact[:60] or "question"


def select_application_and_user(db, requested_application_id: str | None) -> tuple[Application, FinalReport, User]:
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
        application, final_report = row
    else:
        row = query.first()
        if row is None:
            raise SystemExit("No applications with final reports were found in the database.")
        application, final_report = row

    admin_user = db.query(User).filter(User.id == application.uploaded_by).first()
    if admin_user is None:
        admin_user = db.query(User).filter(User.role == "admin").order_by(User.created_at.asc()).first()
    if admin_user is None:
        raise SystemExit("Could not find an admin user for endpoint authentication.")

    return application, final_report, admin_user


def classify_endpoint_status(status_code: int, body: dict[str, Any] | None) -> str:
    if status_code != 200 or body is None:
        return "server_error"
    if body.get("not_found") is True:
        return "not_found"
    if body.get("response_state") == "degraded":
        return "degraded_success"
    return "clean_success"


def run_question(
    *,
    output_dir: Path,
    index: int,
    question: str,
    application_id: str,
    auth_token: str,
    base_url: str,
    review_pages_1_3: dict[str, Any],
    final_report_content: dict[str, Any],
    include_raw_diagnostic: bool,
    max_http_retries: int,
    retry_429_wait_seconds: float,
) -> dict[str, Any]:
    prefix = f"{index:02d}"
    question_dir = output_dir / f"{prefix}_{slugify(question)}"
    question_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"index": index, "question": question}
    write_text(question_dir / "01_question.txt", question)

    validated_question = validate_report_chat_question(question, max_chars=500, max_words=80)
    context = build_report_chat_context(validated_question, review_pages_1_3, final_report_content)
    
    # Ensure sources are JSON serializable
    if "sources" in context:
        context["sources"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in context["sources"]]
        
    write_json(question_dir / "02_route_context.json", context)

    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    retry_count = 0
    with httpx.Client(timeout=120.0) as client:
        while True:
            response = client.post(
                f"{base_url.rstrip('/')}/applications/{application_id}/report-chat",
                headers=headers,
                json={"question": validated_question},
            )
            if response.status_code != 429 or retry_count >= max_http_retries:
                break
            retry_count += 1
            time.sleep(retry_429_wait_seconds)

    result["http_status"] = response.status_code
    result["http_retry_count"] = retry_count
    result["detected_intent"] = context.get("detected_intent")
    result["detected_target"] = context.get("detected_target")
    result["selected_sections"] = [s["section_key"] for s in context.get("sources", [])]

    body: dict[str, Any] | None
    try:
        body = response.json()
    except ValueError:
        body = None

    if body is not None:
        write_json(question_dir / "03_api_response.json", body)
        result["response_state"] = body.get("response_state")
        result["not_found"] = body.get("not_found")
        result["result_count"] = len(body.get("results", []))
    else:
        write_text(question_dir / "03_api_response.txt", response.text)

    result["status"] = classify_endpoint_status(response.status_code, body)

    if include_raw_diagnostic:
        messages = _build_report_chat_messages(validated_question, context)
        write_json(question_dir / "04_raw_messages.json", messages)
        try:
            raw_output = generate(messages, call_label="report_chat")
            write_text(question_dir / "05_raw_model_output.txt", raw_output)
        except LLMClientError as exc:
            write_text(question_dir / "05_raw_model_error.txt", str(exc))

    write_json(question_dir / "99_result_summary.json", result)
    return result


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        application, final_report, admin_user = select_application_and_user(db, args.application_id)
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

        token = create_access_token({"sub": admin_user.email, "role": admin_user.role})
        questions = TEST_QUESTIONS

        run_metadata = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "application_id": str(application.id),
            "application_display_id": application.display_id,
            "base_url": args.base_url,
            "question_count": len(questions),
            "output_dir": str(output_dir),
            "include_raw_diagnostic": not args.skip_raw_diagnostic,
        }
        write_json(output_dir / "00_run_metadata.json", run_metadata)

        results = []
        for index, question in enumerate(questions, start=1):
            results.append(
                run_question(
                    output_dir=output_dir,
                    index=index,
                    question=question,
                    application_id=str(application.id),
                    auth_token=token,
                    base_url=args.base_url,
                    review_pages_1_3=review_package.pages_1_3.model_dump(),
                    final_report_content=final_report_content,
                    include_raw_diagnostic=not args.skip_raw_diagnostic,
                    max_http_retries=args.max_http_retries,
                    retry_429_wait_seconds=args.retry_429_wait_seconds,
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
        for item in results:
            summary["status_counts"][item["status"]] = summary["status_counts"].get(item["status"], 0) + 1
        write_json(output_dir / "99_batch_summary.json", summary)

        print(f"Live report-chat endpoint suite complete for application {application.display_id} ({application.id})")
        print(f"Output directory: {output_dir}")
        for status, count in sorted(summary["status_counts"].items()):
            print(f"{status}: {count}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
