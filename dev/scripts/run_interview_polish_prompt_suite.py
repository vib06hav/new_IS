import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.schemas import InterviewWorkspaceContent
from app.interview_refinement import (
    _build_final_summary_context,
    _build_follow_up_context,
    _build_question_note_context,
    _build_refinement_messages,
    validate_refinement_instruction,
    validate_refinement_text,
)
from app.llm.client import generate


SUPPORTED_BACKEND_CASES = {"question_note", "follow_up_note", "overall_evaluation"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build prompt fixtures for every frontend polish surface in the interview workflow.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional output directory. Defaults to tests/outputs/interview_polish_prompt_suite/<timestamp>.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Also run the live refinement model for backend-supported cases.",
    )
    return parser


def default_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = PROJECT_ROOT / "tests" / "outputs" / "interview_polish_prompt_suite" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def build_sample_content() -> InterviewWorkspaceContent:
    payload = {
        "themes": [
            {
                "id": "theme-generated-1",
                "source": "generated",
                "title": "Technical Depth vs Practice",
                "interview_direction": "need to test if this is actual builder depth or just polished talk. dont let convo stay in impressive-sounding generalities",
                "territory": "",
                "what_makes_it_worth_time": "",
                "question_group_title": "Proof of Real Technical Ownership",
                "questions": [
                    {
                        "id": "question-generated-1",
                        "text": "when the robotics project stopped being straightforward, what was the real technical call you had to make and why that route not the other obvious one?",
                        "source": "generated",
                        "status": "mixed",
                        "note": "started strong / sounded like real ownership at first. then got slippery on why this design vs others. not bad exactly, just i couldnt tell if thinking was deep or rehearsed",
                        "order": 0,
                        "follow_ups": [
                            {
                                "id": "followup-custom-1",
                                "text": "ok but before landing there what did you seriously consider and what made you drop those?",
                                "source": "custom",
                                "status": "mixed",
                                "note": "needed a lot more prompting here. answer wasnt nonsense, just still felt post-hoc / not fully lived-in on the tradeoff side",
                                "order": 0,
                            }
                        ],
                    },
                    {
                        "id": "question-generated-2",
                        "text": "outside class what have you really built yourself, and where did it actually break or get messy?",
                        "source": "generated",
                        "status": "satisfactory",
                        "note": "much better here. concrete sequence, actual debugging, less polished but more believable",
                        "order": 1,
                        "follow_ups": [],
                    },
                ],
            },
            {
                "id": "theme-custom-1",
                "source": "custom",
                "title": "Communication Under Pressure",
                "interview_direction": "want to see if clarity holds once they cant rely on the prepared version of the story",
                "territory": "",
                "what_makes_it_worth_time": "",
                "question_group_title": "Clarity Under Pressure",
                "questions": [
                    {
                        "id": "question-custom-1",
                        "text": "tell me about a time your first read or approach was wrong, and what changed once you realised it",
                        "source": "custom",
                        "status": "unasked",
                        "note": "",
                        "order": 0,
                        "follow_ups": [],
                    }
                ],
            },
        ],
        "final_summary": (
            "overall i buy the technical interest, maybe even real strength, but im less settled on depth than the surface answer might suggest. "
            "best when anchored in concrete execution / debugging. less convincing once the conversation moved to tradeoffs, especially when there wasnt an easy prepared storyline."
        ),
    }
    return InterviewWorkspaceContent.model_validate(payload)


def build_cases(content: InterviewWorkspaceContent) -> list[dict[str, Any]]:
    return [
        {
            "slug": "line_of_inquiry",
            "label": "Line of Inquiry",
            "frontend_surface": "Interview Plan",
            "backend_mode": None,
            "supported_by_backend": False,
            "instruction": "make it sharper + easier to use live, but keep the caution/uncertainty",
            "text": content.themes[0].interview_direction,
            "context": build_line_of_inquiry_context(content, theme_id="theme-generated-1"),
        },
        {
            "slug": "question_text",
            "label": "Question",
            "frontend_surface": "Interview Plan",
            "backend_mode": None,
            "supported_by_backend": False,
            "instruction": "tighten it, keep it natural, dont make it sound like a polished panel prompt",
            "text": content.themes[0].questions[0].text,
            "context": build_question_text_context(content, theme_id="theme-generated-1", question_id="question-generated-1"),
        },
        {
            "slug": "follow_up_text",
            "label": "Follow-up",
            "frontend_surface": "Interview Evaluation",
            "backend_mode": None,
            "supported_by_backend": False,
            "instruction": "make it cleaner as a probe, but dont make it accusatory or too leading",
            "text": content.themes[0].questions[0].follow_ups[0].text,
            "context": build_follow_up_text_context(
                content,
                theme_id="theme-generated-1",
                question_id="question-generated-1",
                follow_up_id="followup-custom-1",
            ),
        },
        {
            "slug": "question_note",
            "label": "Response Note",
            "frontend_surface": "Interview Evaluation",
            "backend_mode": "question_note",
            "supported_by_backend": True,
            "instruction": "clean this up, but do not make me sound more certain than i was",
            "text": content.themes[0].questions[0].note,
            "context": _build_question_note_context(content, theme_id="theme-generated-1", question_id="question-generated-1"),
        },
        {
            "slug": "follow_up_note",
            "label": "Follow-up Response Note",
            "frontend_surface": "Interview Evaluation",
            "backend_mode": "follow_up_note",
            "supported_by_backend": True,
            "instruction": "make this easier to scan, but keep the skepticism level exactly where it is",
            "text": content.themes[0].questions[0].follow_ups[0].note,
            "context": _build_follow_up_context(
                content,
                theme_id="theme-generated-1",
                question_id="question-generated-1",
                follow_up_id="followup-custom-1",
            ),
        },
        {
            "slug": "overall_evaluation",
            "label": "Overall Evaluation",
            "frontend_surface": "Interview Evaluation",
            "backend_mode": "final_summary",
            "supported_by_backend": True,
            "instruction": "make this cleaner for submission, but keep the unresolved hesitation instead of rounding it off",
            "text": content.final_summary,
            "context": _build_final_summary_context(content),
        },
    ]


def build_line_of_inquiry_context(content: InterviewWorkspaceContent, *, theme_id: str) -> str:
    for theme in content.themes:
        if theme.id != theme_id:
            continue
        question_titles = [question.text for question in sorted(theme.questions, key=lambda item: item.order)[:3]]
        lines = [
            f"Focus area: {theme.title or theme.question_group_title}",
            f"Question set label: {theme.question_group_title}",
            "Target text type: interviewer-authored planning guidance for how to explore this focus area in the interview.",
            "Important: polish the line of inquiry itself, not the focus area title or any interview question.",
        ]
        if question_titles:
            lines.append("Questions currently in this set:")
            lines.extend(f"- {title}" for title in question_titles)
        return "\n".join(lines)
    raise ValueError(f"Theme not found: {theme_id}")


def build_question_text_context(content: InterviewWorkspaceContent, *, theme_id: str, question_id: str) -> str:
    for theme in content.themes:
        if theme.id != theme_id:
            continue
        for question in theme.questions:
            if question.id != question_id:
                continue
            return "\n".join(
                [
                    f"Focus area: {theme.title or theme.question_group_title}",
                    f"Question set label: {theme.question_group_title}",
                    f"Interview focus: {theme.interview_direction}",
                    "Target text type: interviewer-facing main interview question prompt.",
                    "Important: polish the question wording itself, not the response note or evaluation.",
                ]
            )
    raise ValueError(f"Question not found: {question_id}")


def build_follow_up_text_context(
    content: InterviewWorkspaceContent,
    *,
    theme_id: str,
    question_id: str,
    follow_up_id: str,
) -> str:
    for theme in content.themes:
        if theme.id != theme_id:
            continue
        for question in theme.questions:
            if question.id != question_id:
                continue
            for follow_up in question.follow_ups:
                if follow_up.id != follow_up_id:
                    continue
                return "\n".join(
                    [
                        f"Focus area: {theme.title or theme.question_group_title}",
                        f"Question set label: {theme.question_group_title}",
                        f"Interview focus: {theme.interview_direction}",
                        f"Main interview question asked to the applicant: {question.text}",
                        "Target text type: interviewer-facing follow-up prompt used to probe deeper in the interview.",
                        "Important: polish the follow-up wording itself, not the follow-up response note.",
                    ]
                )
    raise ValueError(f"Follow-up not found: {follow_up_id}")


def build_frontend_only_messages(*, mode_label: str, text: str, instruction: str, context: str) -> list[dict[str, str]]:
    instruction_line = (
        instruction
        if instruction
        else "No extra instruction was provided. Focus on clarity, structure, and intent preservation only."
    )
    system_prompt = (
        "You are polishing interviewer-authored admissions interview writing. "
        "Your job is to improve clarity, structure, and phrasing while staying grounded in the text and context provided. "
        "Preserve the original speech act and function of the text. "
        "If the source is a planning note, keep it planning-oriented. If the source is a question, keep it a question. "
        "Do not rewrite interviewer prep text into evaluation text. "
        "Do not invent evidence, claims, judgments, or specifics not supported by the source text and context. "
        "Do not upgrade certainty, exaggerate conclusions, or add new interpretation beyond the original text. "
        "You may modestly improve emphasis only when the instruction explicitly asks for it. "
        "Return only the polished text, with no preamble."
    )
    user_prompt = (
        f"Polish this {mode_label}.\n\n"
        f"Context:\n{context}\n\n"
        f"Original text:\n{text}\n\n"
        f"Instruction:\n{instruction_line}\n\n"
        "Keep the meaning grounded in the original. Preserve the text's role in the workflow. "
        "Use paragraphs or bullets only if they improve readability."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_messages_for_case(case: dict[str, Any]) -> list[dict[str, str]]:
    text = validate_refinement_text(case["text"])
    instruction = validate_refinement_instruction(case["instruction"])
    if case["backend_mode"] == "question_note":
        return _build_refinement_messages(mode="question_note", text=text, instruction=instruction, context=case["context"])
    if case["backend_mode"] == "follow_up_note":
        return _build_refinement_messages(mode="follow_up_note", text=text, instruction=instruction, context=case["context"])
    if case["backend_mode"] == "final_summary":
        return _build_refinement_messages(mode="final_summary", text=text, instruction=instruction, context=case["context"])
    return build_frontend_only_messages(
        mode_label=case["label"].lower(),
        text=text,
        instruction=instruction,
        context=case["context"],
    )


def run_live_refinement(case: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
    if not case["supported_by_backend"]:
        return {
            "status": "skipped_frontend_only_case",
            "reason": "This polish surface is present in the frontend but does not have a backend refinement mode yet.",
        }
    response = generate(messages, call_label="interview_refinement").strip()
    return {
        "status": "success" if response else "empty_response",
        "refined_text": response,
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    content = build_sample_content()
    cases = build_cases(content)
    suite_summary: list[dict[str, Any]] = []

    write_json(output_dir / "00_workspace_fixture.json", content.model_dump(mode="json"))

    for index, case in enumerate(cases, start=1):
        case_dir = output_dir / f"{index:02d}_{case['slug']}"
        case_dir.mkdir(parents=True, exist_ok=True)

        messages = build_messages_for_case(case)
        case_summary = {
            "index": index,
            "slug": case["slug"],
            "label": case["label"],
            "frontend_surface": case["frontend_surface"],
            "supported_by_backend": case["supported_by_backend"],
            "backend_mode": case["backend_mode"],
        }

        write_json(case_dir / "01_case_meta.json", case_summary)
        write_text(case_dir / "02_original_text.txt", case["text"])
        write_text(case_dir / "03_instruction.txt", case["instruction"])
        write_text(case_dir / "04_context.txt", case["context"])
        write_json(case_dir / "05_messages.json", messages)

        if args.live:
            live_result = run_live_refinement(case, messages)
            write_json(case_dir / "06_live_result.json", live_result)
            case_summary["live_status"] = live_result["status"]
        else:
            case_summary["live_status"] = "not_requested"

        suite_summary.append(case_summary)

    write_json(
        output_dir / "99_suite_summary.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "live_mode": bool(args.live),
            "supported_backend_cases": sorted(SUPPORTED_BACKEND_CASES),
            "cases": suite_summary,
        },
    )

    print(f"Wrote interview polish prompt suite to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
