import json
import logging
import re
from typing import Any, Literal, Optional

from app.api.schemas import ReportChatResponse, ReportChatSource
from app.llm.client import LLMClientError, LLMRequestOptions, generate


logger = logging.getLogger(__name__)

ReportChatIntent = Literal["content", "workflow", "action", "mixed"]
ReportChatTarget = Literal[
    "identity",
    "academics",
    "tests",
    "activities",
    "leadership",
    "essays",
    "focus_areas",
    "questions",
    "final_report",
    "workflow",
    "mixed",
]
ReportChatFailureKind = Literal["content", "structural"]
ReportChatAnswerShape = Literal["fact", "workflow", "broad_synthesis", "mixed"]


REPORT_CHAT_SECTION_TARGETS: dict[str, dict[str, str]] = {
    "page1_overview": {
        "target_tab": "page1",
        "anchor_id": "report-page1-overview",
        "page_label": "Page 1",
        "section_label": "Overview",
    },
    "page2_academics": {
        "target_tab": "page2",
        "anchor_id": "report-page2-academics",
        "page_label": "Page 2",
        "section_label": "Academics",
    },
    "page2_tests": {
        "target_tab": "page2",
        "anchor_id": "report-page2-tests",
        "page_label": "Page 2",
        "section_label": "Tests",
    },
    "page2_activities": {
        "target_tab": "page2",
        "anchor_id": "report-page2-activities",
        "page_label": "Page 2",
        "section_label": "Activities",
    },
    "page2_leadership": {
        "target_tab": "page2",
        "anchor_id": "report-page2-leadership",
        "page_label": "Page 2",
        "section_label": "Leadership",
    },
    "page3_essays": {
        "target_tab": "page3",
        "anchor_id": "report-page3-essays",
        "page_label": "Page 3",
        "section_label": "Writing",
    },
    "page4_focus_areas": {
        "target_tab": "page4",
        "anchor_id": "report-page4-focus-areas",
        "page_label": "Page 4",
        "section_label": "Focus Areas",
    },
    "page5_question_groups": {
        "target_tab": "page5",
        "anchor_id": "report-page5-question-groups",
        "page_label": "Page 5",
        "section_label": "Question Groups",
    },
}

PAGE_MAP = {
    "page1": {
        "label": "Page 1",
        "name": "Overview",
        "purpose": "Applicant background and identity context.",
    },
    "page2": {
        "label": "Page 2",
        "name": "Academics & Activities",
        "purpose": "Marks, tests, activities, and leadership evidence.",
    },
    "page3": {
        "label": "Page 3",
        "name": "Writing",
        "purpose": "Essays and written expression.",
    },
    "page4": {
        "label": "Page 4",
        "name": "Focus Areas",
        "purpose": "Interpretive Context Dossier containing focus areas.",
    },
    "page5": {
        "label": "Page 5",
        "name": "Question Groups",
        "purpose": "Lean live-interview question sheet with lines of inquiry.",
    },
    "page6": {
        "label": "Page 6",
        "name": "Final Interview Report",
        "purpose": "Post-interview outcomes and final summary after completion.",
    },
}

QUESTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "page1_overview": ("background", "overview", "family", "city", "state", "major", "identity", "profile"),
    "page2_academics": ("academics", "academic", "marks", "mark", "grade", "grades", "score", "scores", "physics", "chemistry", "math", "mathematics", "subject", "subjects", "10th", "11th", "12th", "school"),
    "page2_tests": ("test", "tests", "jee", "sat", "act", "ielts", "toefl", "entrance", "exam", "percentile", "rank"),
    "page2_activities": ("activity", "activities", "extracurricular", "co curricular", "co-curricular", "sports", "music", "piano", "reading", "olympiad", "club", "competition", "internship", "yoga"),
    "page2_leadership": ("leadership", "captain", "president", "head boy", "head girl", "leader", "role"),
    "page3_essays": ("essay", "essays", "writing", "statement", "prompt", "writing sample"),
    "page4_focus_areas": ("focus area", "focus areas", "theme", "themes", "signal", "signals", "stand out", "stands out"),
    "page5_question_groups": ("question", "questions", "probe", "follow up", "follow-up", "line of inquiry", "direction", "question group", "question groups"),
}

WORKFLOW_KEYWORDS = (
    "what is page",
    "what does page",
    "why is page",
    "where do i find",
    "where should i look",
    "how does page",
    "how should i use",
    "what happens after",
    "what happens before",
    "what stage",
)
ACTION_KEYWORDS = (
    "what can i do",
    "what should i do",
    "what do i do next",
    "next step",
    "what should i ask next",
    "what should i probe",
    "how should i prepare",
)
MIXED_KEYWORDS = (
    "what stands out and",
    "where are the",
    "tell me about",
    "summarize",
    "compare",
)
DISALLOWED_JUDGMENT_PATTERNS = (
    r"\bgood applicant\b",
    r"\bbad applicant\b",
    r"\bshould we admit\b",
    r"\bshould we reject\b",
    r"\brate this candidate\b",
    r"\brank this candidate\b",
    r"\bstrong applicant\b",
    r"\bweak applicant\b",
)
OUT_OF_SCOPE_PATTERNS = (
    r"\bwrite code\b",
    r"\bcode this\b",
    r"\bimplement\b",
    r"\bdebug\b",
    r"\bfix this bug\b",
    r"\bpython\b",
    r"\bjavascript\b",
    r"\btypescript\b",
    r"\bsql\b",
    r"\bbuild an app\b",
    r"\bcreate a script\b",
)
STRUCTURAL_LEAK_PATTERNS = (
    r"```json",
    r"```",
    r'"answer_summary"\s*:',
    r'"response_kind"\s*:',
    r'"suggested_followups"\s*:',
    r'"response\b',
    r"suggested follow-ups?\s*:",
)
DANGLING_SCHEMA_ENDINGS = (
    '"response',
    '"answer_summary',
    '"response_kind',
    '"suggested_followups',
    '{"answer_summary"',
)

class ReportChatError(Exception):
    """Raised when the report chatbot cannot safely answer."""


def validate_report_chat_question(question: str, *, max_chars: int, max_words: int) -> str:
    normalized = " ".join(question.split())
    if not normalized:
        raise ReportChatError("Question cannot be empty")
    if len(normalized) > max_chars:
        raise ReportChatError(
            f"Question is too long. Keep it under {max_chars} characters so the report copilot stays focused."
        )
    if len(normalized.split()) > max_words:
        raise ReportChatError(
            f"Question is too long. Keep it under {max_words} words so the report copilot can answer efficiently."
        )
    return normalized


def detect_operation(question: str) -> str:
    return _detect_intent(question)[0]


def detect_target(question: str, operation: str | None = None) -> ReportChatTarget:
    del operation
    return _detect_intent(question)[1]


def build_report_chat_context(
    question: str,
    review_package_pages: dict[str, Any],
    final_report_content: Optional[dict[str, Any]],
    *,
    workspace: Optional[dict[str, Any]] = None,
    surface_type: str = "report_viewer",
    current_page: Optional[str] = None,
    workflow_stage: Optional[str] = None,
    available_actions: Optional[list[str]] = None,
) -> dict[str, Any]:
    normalized_question = " ".join(question.split())
    intent, target = _detect_intent(normalized_question)
    effective_stage = workflow_stage or _infer_workflow_stage(surface_type, workspace)
    effective_page = current_page or _default_current_page(surface_type)
    actions = list(available_actions or [])

    page4 = final_report_content.get("page_4_focus_areas", {}) if isinstance(final_report_content, dict) else {}
    page5 = final_report_content.get("page_5_question_groups", {}) if isinstance(final_report_content, dict) else {}
    deterministic_signals = _extract_deterministic_signals(final_report_content)
    page6 = _build_page6_context(workspace)

    section_keys = _select_relevant_section_keys(normalized_question, effective_page, surface_type)
    sources = _build_sources(section_keys)

    report_context = {
        "pages_1_3": review_package_pages,
        "pages_4_5": {
            "page_4_focus_areas": page4 if isinstance(page4, dict) else {},
            "page_5_question_groups": page5 if isinstance(page5, dict) else {},
        },
        "page_6_final_report": page6,
        "workspace_content": workspace.get("content", {}) if isinstance(workspace, dict) else {},
        "deterministic_signals": deterministic_signals,
    }
    evidence_text = json.dumps(
        {
            "page_map": PAGE_MAP,
            "surface_type": surface_type,
            "current_page": effective_page,
            "workflow_stage": effective_stage,
            "available_actions": actions,
            "report_context": report_context,
        },
        default=str,
    )

    return {
        "question": normalized_question,
        "surface_type": surface_type,
        "current_page": effective_page,
        "workflow_stage": effective_stage,
        "available_actions": actions,
        "page_map": PAGE_MAP,
        "report_context": report_context,
        "deterministic_signals": deterministic_signals,
        "workspace": workspace or {},
        "sources": sources,
        "response_kind": intent,
        "detected_intent": intent,
        "detected_target": target,
        "constraints": [
            "Use only provided resources.",
            "Do not invent or alter numbers, subjects, activities, or interview outcomes.",
            "Do not infer missing facts.",
            "Do not judge or rank the student overall.",
        ],
        "evidence_text": evidence_text,
    }


def _build_report_chat_messages(
    question: str,
    context: dict[str, Any],
    *,
    retry_mode: Optional[ReportChatFailureKind] = None,
) -> list[dict[str, str]]:
    answer_shape = _determine_answer_shape(question, context)
    system_lines = [
        "You are a grounded report copilot for a 6-page interview workflow.",
        "Answer only from the provided report, workflow, and UI context.",
        "Maintain an objective, neutral, and factual tone. Avoid personality, conversational filler, or subjective praise.",
        "You may summarize, compare, explain pages, and suggest next steps based on the available actions.",
        "Do not invent numbers, subjects, activities, page contents, interview outcomes, or people.",
        "Do not infer missing facts or judge the student overall.",
        "Do not recommend admit, reject, rank, or score the student.",
        "If something is unavailable in the resources, say that directly.",
        "Return a JSON object with keys: answer_summary, response_kind, suggested_followups.",
        "response_kind must be one of: content, workflow, action, mixed.",
        "suggested_followups must be an array of 1 to 3 concise user-facing prompts.",
        "answer_summary must be plain-text prose only. Do not include JSON, code fences, markdown headings, or bullet lists.",
        "Do not place follow-up suggestions inside answer_summary.",
        "Put follow-up prompts only in suggested_followups.",
        "For a simple factual or yes/no question, answer in 1 to 2 sentences.",
        "For a workflow or navigation question, answer in 2 to 4 sentences.",
        "For a broad synthesis question, answer in one short paragraph unless the user asked for more detail.",
    ]
    if answer_shape == "fact":
        system_lines.append(
            "This is a narrow factual question. Answer in one sentence if possible. "
            "Do not expand, do not add context, do not suggest related themes. "
            "Only qualify if the fact genuinely requires it."
        )
    elif answer_shape == "workflow":
        system_lines.append(
            "This is a workflow or navigation question. Answer in 2 to 3 sentences maximum. "
            "State what the page or stage is for, then what the user should do. Stop there."
        )
    elif answer_shape == "broad_synthesis":
        system_lines.append(
            "This is a synthesis question. Write one focused paragraph. "
            "Lead with the most important insight, then support it briefly. "
            "Do not list every detail - prioritize what matters most for the interview."
        )
    else:
        system_lines.append(
            "This question mixes content and workflow. Answer the content part in 1 to 2 sentences, "
            "then the workflow part in 1 sentence. Keep the total under 4 sentences."
        )

    if retry_mode == "content":
        system_lines.append(
            "Your previous answer was rejected because it contained unsupported content. Use only exact grounded details present in the context."
        )
    if retry_mode == "structural":
        system_lines.append(
            "Your previous answer was structurally invalid. Return compact valid JSON only, and keep answer_summary shorter than before."
        )

    payload = {
        "question": question,
        "surface_type": context.get("surface_type"),
        "current_page": context.get("current_page"),
        "workflow_stage": context.get("workflow_stage"),
        "available_actions": context.get("available_actions"),
        "page_map": context.get("page_map"),
        "report_context": context.get("report_context"),
        "constraints": context.get("constraints"),
    }

    return [
        {"role": "system", "content": "\n".join(system_lines)},
        {"role": "user", "content": json.dumps(payload, default=str)},
    ]


def _extract_json_candidate(text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    return match.group(0) if match else cleaned


def _recover_partial_report_chat_payload(text: str) -> tuple[Optional[dict[str, Any]], Optional[ReportChatFailureKind]]:
    candidate = _extract_json_candidate(text)
    if candidate:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed, None
        except Exception:
            return None, "structural"
    return None, "structural"


def answer_report_question(question: str, context: dict[str, Any]) -> ReportChatResponse:
    scope_response = _scope_guard_response(question, context)
    if scope_response is not None:
        return scope_response

    attempt_result = _generate_copilot_payload(question, context, retry_mode=None)
    failure_kind = _payload_validation_error(attempt_result, context) if attempt_result is not None else "structural"
    if failure_kind is not None:
        attempt_result = _generate_copilot_payload(question, context, retry_mode=failure_kind)

    if attempt_result is None:
        return _fallback_response(context)

    failure_kind = _payload_validation_error(attempt_result, context)
    if failure_kind is not None:
        logger.warning("Report copilot validation degraded response: %s", failure_kind)
        return _fallback_response(context)

    return ReportChatResponse(
        answer_summary=attempt_result["answer_summary"],
        response_kind=attempt_result["response_kind"],
        sources=context.get("sources", []),
        not_found=False,
        response_state="retried" if attempt_result.get("_retried") else "clean",
        suggested_followups=attempt_result["suggested_followups"],
    )


def _generate_copilot_payload(
    question: str,
    context: dict[str, Any],
    *,
    retry_mode: Optional[ReportChatFailureKind],
) -> Optional[dict[str, Any]]:
    try:
        response_text = generate(
            _build_report_chat_messages(question, context, retry_mode=retry_mode),
            call_label="report_chat",
            request_options=LLMRequestOptions(response_format_type="json_object"),
        )
    except LLMClientError:
        return None

    payload, recovery_failure = _recover_partial_report_chat_payload(response_text)
    if recovery_failure is not None or payload is None:
        return None

    answer_summary = _normalize_answer_text(payload.get("answer_summary"))
    if not answer_summary:
        return None

    response_kind = str(payload.get("response_kind") or context.get("response_kind") or "content").strip().lower()
    if response_kind not in {"content", "workflow", "action", "mixed"}:
        response_kind = str(context.get("response_kind") or "content")

    suggested_followups = _normalize_followups(payload.get("suggested_followups"))
    if not suggested_followups:
        suggested_followups = _default_followups(context)

    return {
        "answer_summary": answer_summary,
        "response_kind": response_kind,
        "suggested_followups": suggested_followups,
        "_retried": retry_mode is not None,
    }


def _payload_validation_error(payload: Optional[dict[str, Any]], context: dict[str, Any]) -> Optional[ReportChatFailureKind]:
    if payload is None:
        return "structural"
    answer = payload.get("answer_summary", "")
    if not answer:
        return "content"
    if _contains_structural_leak(answer):
        return "structural"
    if _contains_disallowed_judgment(answer):
        return "content"
    return None


def _scope_guard_response(question: str, context: dict[str, Any]) -> ReportChatResponse | None:
    normalized = question.lower()
    if any(re.search(pattern, normalized) for pattern in OUT_OF_SCOPE_PATTERNS):
        return ReportChatResponse(
            answer_summary="I can only help with this report and the interview workflow around it. I cannot take on coding or unrelated tasks here.",
            response_kind="degraded",
            sources=context.get("sources", []),
            not_found=False,
            response_state="clean",
            suggested_followups=_default_followups(context),
        )
    if any(re.search(pattern, normalized) for pattern in DISALLOWED_JUDGMENT_PATTERNS):
        return ReportChatResponse(
            answer_summary="I can describe what the report shows, but I cannot judge, rank, admit, or reject the candidate.",
            response_kind="degraded",
            sources=context.get("sources", []),
            not_found=False,
            response_state="clean",
            suggested_followups=_default_followups(context),
        )
    return None


def _fallback_response(context: dict[str, Any]) -> ReportChatResponse:
    return ReportChatResponse(
        answer_summary=_fallback_answer(context),
        response_kind="degraded",
        sources=context.get("sources", []),
        not_found=False,
        response_state="degraded",
        suggested_followups=_default_followups(context),
    )


def _fallback_answer(context: dict[str, Any]) -> str:
    question = str(context.get("question") or "").lower()
    report_context = context.get("report_context") or {}
    pages_1_3 = report_context.get("pages_1_3") or {}
    page2 = pages_1_3.get("page_2_academic_and_engagement") if isinstance(pages_1_3, dict) else {}
    page3 = pages_1_3.get("page_3_essays") if isinstance(pages_1_3, dict) else {}
    page4 = (report_context.get("pages_4_5") or {}).get("page_4_focus_areas", {})
    page5 = (report_context.get("pages_4_5") or {}).get("page_5_question_groups", {})
    page6 = report_context.get("page_6_final_report") or {}
    actions = context.get("available_actions") or []

    if any(token in question for token in ("what can i do", "what should i do", "next step")):
        return _workflow_fallback(context.get("current_page"), context.get("workflow_stage"), actions)

    if "page 5" in question or "question" in question or "probe" in question or "inquiry" in question:
        groups = page5.get("question_groups", []) if isinstance(page5, dict) else []
        if isinstance(groups, list) and groups:
            titles = [str(group.get("group_label")).strip() for group in groups[:3] if isinstance(group, dict) and str(group.get("group_label")).strip()]
            if titles:
                return "Page 5 contains question groups for: " + ", ".join(titles) + "."
        return "Page 5 is the question sheet, but this report does not currently show generated question groups."

    if "page 4" in question or "focus" in question or "theme" in question or "signal" in question:
        focus_areas = page4.get("focus_areas", []) if isinstance(page4, dict) else []
        if isinstance(focus_areas, list) and focus_areas:
            titles = [str(item.get("title")).strip() for item in focus_areas[:3] if isinstance(item, dict) and str(item.get("title")).strip()]
            if titles:
                return "Page 4 synthesizes the report into focus areas such as " + ", ".join(titles) + "."
        return "Page 4 is the synthesis layer for interviewer focus areas, but this report does not currently show generated focus areas."

    if "activity" in question:
        summary = _summarize_activities(page2 if isinstance(page2, dict) else {})
        if summary:
            return summary

    if any(token in question for token in ("mark", "grade", "score", "physics", "academic", "10th", "11th", "12th")):
        summary = _summarize_academics(
            page2 if isinstance(page2, dict) else {},
            question=question,
        )
        if summary:
            return summary

    if any(token in question for token in ("test", "jee", "sat", "act", "entrance")):
        summary = _summarize_tests(page2 if isinstance(page2, dict) else {})
        if summary:
            return summary

    if any(token in question for token in ("essay", "writing")):
        essays = page3.get("essays", []) if isinstance(page3, dict) else []
        if isinstance(essays, list) and essays:
            return f"The writing section contains {len(essays)} essay response(s) that can be used for deeper follow-up."

    if context.get("current_page") == "page6" and isinstance(page6, dict):
        summary = _safe_string(page6.get("final_summary"))
        if summary:
            return summary
        totals = page6.get("totals", {})
        if isinstance(totals, dict) and totals.get("openings"):
            return (
                f"The final interview report records {totals.get('openings')} interview-opening outcomes, "
                f"including {totals.get('satisfactory', 0)} satisfactory and {totals.get('mixed', 0)} mixed results."
            )

    return _workflow_fallback(context.get("current_page"), context.get("workflow_stage"), actions)


def _workflow_fallback(current_page: Any, workflow_stage: Any, actions: list[str]) -> str:
    page_name = _page_name_from_key(str(current_page or ""))
    stage_label = _stage_label(str(workflow_stage or "prep"))
    if actions:
        return f"You are in {page_name} during the {stage_label} stage. From here you can " + ", ".join(actions[:4]) + "."
    return f"You are in {page_name} during the {stage_label} stage, and the copilot can help explain the report, the workflow, and your next step."


def _normalize_answer_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def _normalize_followups(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            continue
        normalized = " ".join(entry.split()).strip()
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
        if len(cleaned) >= 3:
            break
    return cleaned


def _contains_disallowed_judgment(answer: str) -> bool:
    lowered = answer.lower()
    return any(re.search(pattern, lowered) for pattern in DISALLOWED_JUDGMENT_PATTERNS)


def _contains_structural_leak(answer: str) -> bool:
    lowered = answer.lower().strip()
    if not lowered:
        return False
    if any(re.search(pattern, lowered) for pattern in STRUCTURAL_LEAK_PATTERNS):
        return True
    if any(lowered.endswith(ending) for ending in DANGLING_SCHEMA_ENDINGS):
        return True
    return False


def _detect_intent(question: str) -> tuple[ReportChatIntent, ReportChatTarget]:
    normalized = question.lower()
    has_workflow = any(keyword in normalized for keyword in WORKFLOW_KEYWORDS)
    has_action = any(keyword in normalized for keyword in ACTION_KEYWORDS)
    has_mixed = any(keyword in normalized for keyword in MIXED_KEYWORDS)

    if has_workflow and has_action:
        return "mixed", "mixed"
    if has_workflow and has_mixed:
        return "mixed", "mixed"
    if has_action and has_mixed:
        return "mixed", "mixed"
    if has_action:
        return "action", "workflow"
    if has_workflow:
        return "workflow", "workflow"

    if "final interview report" in normalized or "interview outcome" in normalized:
        return "content", "final_report"
    if any(token in normalized for token in ("activity", "activities", "extracurricular", "co curricular")):
        return "content", "activities"
    if any(token in normalized for token in ("leadership", "captain", "president")):
        return "content", "leadership"
    if any(token in normalized for token in ("essay", "essays", "writing")):
        return "content", "essays"
    if any(token in normalized for token in ("test", "jee", "sat", "act", "entrance")):
        return "content", "tests"
    if any(token in normalized for token in ("mark", "marks", "grade", "grades", "score", "scores", "physics", "subject", "academic", "10th", "11th", "12th")):
        return "content", "academics"
    if any(token in normalized for token in ("theme", "themes", "signal", "signals", "focus area")):
        return "content", "focus_areas"
    if any(token in normalized for token in ("question", "questions", "probe", "follow up", "follow-up", "opening", "openings", "hook")):
        return "content", "questions"
    return "content", "mixed"


def _determine_answer_shape(question: str, context: dict[str, Any]) -> ReportChatAnswerShape:
    normalized = question.lower()
    intent = str(context.get("detected_intent") or "content")
    target = str(context.get("detected_target") or "mixed")

    if intent == "workflow":
        return "workflow"
    if intent == "mixed":
        return "mixed"

    # Synthesis questions always win before factual checks, even when phrased briefly.
    if any(token in normalized for token in ("difference between", "compare", "what stands out", "summarize", "tell me about")):
        return "broad_synthesis"

    # Status/completion questions should stay narrow regardless of detected target.
    if any(token in normalized for token in ("is this", "is it", "does this", "completed", "complete", "done", "status")):
        return "fact"

    # Specific data lookups are facts.
    if any(token in normalized for token in ("class 10", "10th", "11th", "12th", "what are the")):
        return "fact"

    if target in {"workflow", "questions", "focus_areas"}:
        return "workflow"
    if target in {"academics", "tests", "activities", "leadership", "identity"}:
        return "fact"
    return "broad_synthesis"


def _infer_workflow_stage(surface_type: str, workspace: Optional[dict[str, Any]]) -> str:
    if surface_type == "overlay":
        return "live_interview"
    if surface_type == "postgame":
        return "postgame"
    if surface_type == "final_report":
        return "completed"

    workspace_status = _safe_string((workspace or {}).get("status"))
    if workspace_status == "launched":
        return "live_interview"
    if workspace_status == "postgame":
        return "postgame"
    if workspace_status == "completed":
        return "completed"
    return "prep"


def _default_current_page(surface_type: str) -> str:
    if surface_type == "configure":
        return "configure"
    if surface_type == "overlay":
        return "overlay"
    if surface_type == "postgame":
        return "postgame"
    if surface_type == "final_report":
        return "page6"
    return "page1"


def _extract_deterministic_signals(final_report_content: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(final_report_content, dict):
        return []
    signal_data = final_report_content.get("signal_data")
    if not isinstance(signal_data, dict):
        return []
    signals = signal_data.get("deterministic_signals")
    if not isinstance(signals, list):
        return []
    return [entry for entry in signals if isinstance(entry, dict)]


def _build_page6_context(workspace: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(workspace, dict):
        return {}

    content = workspace.get("content")
    if not isinstance(content, dict):
        return {}

    totals = {"openings": 0, "satisfactory": 0, "mixed": 0, "unsatisfactory": 0, "unasked": 0}
    for theme in content.get("themes", []):
        if not isinstance(theme, dict):
            continue
        for question in theme.get("openings", theme.get("questions", [])):
            if isinstance(question, dict):
                _tally_status(totals, _safe_string(question.get("status")))
                for follow_up in question.get("follow_ups", []):
                    if isinstance(follow_up, dict):
                        _tally_status(totals, _safe_string(follow_up.get("status")))

    return {
        "status": workspace.get("status"),
        "final_summary": content.get("final_summary", ""),
        "themes": content.get("themes", []),
        "totals": totals,
    }


def _tally_status(totals: dict[str, int], status: Optional[str]) -> None:
    totals["openings"] += 1
    if status in {"satisfactory", "mixed", "unsatisfactory", "unasked"}:
        totals[status] += 1
    else:
        totals["unasked"] += 1


def _select_relevant_section_keys(question: str, current_page: Optional[str], surface_type: str) -> list[str]:
    normalized = question.lower()
    selected: list[str] = []

    for section_key, keywords in QUESTION_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            selected.append(section_key)

    current_page_map = {
        "page1": "page1_overview",
        "page2": "page2_academics",
        "page3": "page3_essays",
        "page4": "page4_focus_areas",
        "page5": "page5_question_groups",
    }
    if current_page in current_page_map:
        selected.insert(0, current_page_map[current_page])

    if surface_type in {"configure", "overlay", "postgame", "final_report"} and not selected:
        selected.extend(["page2_academics", "page2_activities", "page5_question_groups"])

    deduped: list[str] = []
    for key in selected:
        if key in REPORT_CHAT_SECTION_TARGETS and key not in deduped:
            deduped.append(key)
        if len(deduped) >= 4:
            break
    return deduped


def _build_sources(section_keys: list[str]) -> list[ReportChatSource]:
    sources: list[ReportChatSource] = []
    for section_key in section_keys:
        target = REPORT_CHAT_SECTION_TARGETS.get(section_key)
        if not target:
            continue
        sources.append(
            ReportChatSource(
                label=f"{target['page_label']} - {target['section_label']}",
                target_tab=target["target_tab"],  # type: ignore[arg-type]
                section_key=section_key,  # type: ignore[arg-type]
                anchor_id=target["anchor_id"],
            )
        )
    return sources


def _default_followups(context: dict[str, Any]) -> list[str]:
    current_page = str(context.get("current_page") or "")
    workflow_stage = str(context.get("workflow_stage") or "")

    if current_page == "page6" or workflow_stage == "completed":
        return [
            "Summarize the final interview outcome",
            "Compare the final outcome with the earlier report",
            "Which themes held up after the interview?",
        ]
    if workflow_stage == "live_interview":
        return [
            "What should I probe next?",
            "Which theme still feels unresolved?",
            "What follow-up question would be useful here?",
        ]
    if workflow_stage == "postgame":
        return [
            "What gaps remain in the interview notes?",
            "Help me tighten the final summary",
            "Which question outcomes look mixed or unresolved?",
        ]
    if current_page == "page5":
        return [
            "How should I use these openings in the interview?",
            "Which opening group should I prioritize first?",
            "What follow-ups would deepen one of these openings?",
        ]
    if current_page == "page4":
        return [
            "Explain the main focus areas",
            "Which signals matter most here?",
            "How should these themes shape the interview?",
        ]
    return [
        "What stands out across this report?",
        "How should I use this in the interview?",
        "Which page should I review next?",
    ]


def _summarize_academics(page2: dict[str, Any], *, question: str | None = None) -> str:
    records = [entry for entry in page2.get("academic_records", []) if isinstance(entry, dict)]
    if not records:
        return ""

    if question:
        specific_level = _extract_academic_level_from_question(question)
        if specific_level:
            matched_record = _match_academic_record(records, specific_level)
            if matched_record:
                score = _format_score(
                    matched_record.get("score_raw"),
                    matched_record.get("max_score_raw"),
                    matched_record.get("grading_mode"),
                )
                if score:
                    return f"The {specific_level} result in the report is {score}."

    parts: list[str] = []
    for entry in records[:4]:
        level = _safe_string(entry.get("academic_level")) or "Academic record"
        score = _format_score(entry.get("score_raw"), entry.get("max_score_raw"), entry.get("grading_mode"))
        if score:
            parts.append(f"{level}: {score}")
    if not parts:
        return ""
    return "The academic record includes " + ", ".join(parts) + "."


def _extract_academic_level_from_question(question: str) -> str | None:
    normalized = question.lower()
    if any(token in normalized for token in ("class 9", "9th", "ninth")):
        return "9TH"
    if any(token in normalized for token in ("class 10", "10th", "tenth")):
        return "10TH"
    if any(token in normalized for token in ("class 11", "11th", "eleventh")):
        return "11TH"
    if any(token in normalized for token in ("class 12", "12th", "twelfth")):
        return "12TH"
    return None


def _match_academic_record(records: list[dict[str, Any]], desired_level: str) -> dict[str, Any] | None:
    for entry in records:
        level = (_safe_string(entry.get("academic_level")) or "").upper()
        if level == desired_level:
            return entry
    return None


def _summarize_tests(page2: dict[str, Any]) -> str:
    tests = [entry for entry in page2.get("standardized_tests", []) if isinstance(entry, dict)]
    if not tests:
        return ""
    parts: list[str] = []
    for entry in tests[:3]:
        name = _safe_string(entry.get("test_name")) or "test"
        score = _safe_string(entry.get("total_score")) or _safe_string(entry.get("percentile")) or _safe_string(entry.get("rank"))
        parts.append(f"{name}{f' ({score})' if score else ''}")
    return "The report lists test results including " + ", ".join(parts) + "."


def _summarize_activities(page2: dict[str, Any]) -> str:
    activity_groups = []
    for key in ("extracurricular_activities", "co_curricular_activities"):
        entries = page2.get(key, [])
        if isinstance(entries, list):
            activity_groups.extend(entry for entry in entries if isinstance(entry, dict))
    if not activity_groups:
        return ""

    parts: list[str] = []
    for entry in activity_groups[:4]:
        name = _safe_string(entry.get("activity_name")) or "activity"
        level = _safe_string(entry.get("level"))
        duration = _safe_string(entry.get("duration_years")) or _safe_string(entry.get("duration"))
        detail = ", ".join(part for part in [level, f"{duration} years" if duration else None] if part)
        parts.append(f"{name}{f' ({detail})' if detail else ''}")
    return "The activities section highlights " + ", ".join(parts) + "."


def _format_score(score_raw: Any, max_score_raw: Any, grading_mode: Any) -> str | None:
    score = _safe_string(score_raw)
    max_score = _safe_string(max_score_raw)
    grading = _safe_string(grading_mode)
    if score and max_score:
        return f"{score}/{max_score}"
    if score and grading:
        return f"{score} ({grading})"
    return score


def _safe_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _page_name_from_key(page_key: str) -> str:
    if page_key in PAGE_MAP:
        return f"{PAGE_MAP[page_key]['label']} {PAGE_MAP[page_key]['name']}"
    if page_key == "configure":
        return "the configure workspace"
    if page_key == "overlay":
        return "the interview overlay"
    if page_key == "postgame":
        return "the postgame workspace"
    return "the report"


def _stage_label(stage: str) -> str:
    if stage == "live_interview":
        return "live interview"
    if stage == "postgame":
        return "postgame"
    if stage == "completed":
        return "completed"
    return "prep"
