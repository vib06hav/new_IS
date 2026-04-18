import json
import logging
import re
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Literal, Optional

from pydantic import ValidationError

from app.api.schemas import ReportChatResponse
from app.llm.client import (
    LLMClientError,
    LLMRequestOptions,
    LLMStructuredOutputUnsupportedError,
    generate,
)


logger = logging.getLogger(__name__)

ReportChatOperation = Literal["retrieve", "transform", "explain", "redirect"]
ReportChatTarget = Literal[
    "identity",
    "academics",
    "tests",
    "activities",
    "leadership",
    "essays",
    "themes",
    "signals",
    "question_groups",
    "full_report",
]
ReportChatAnswerMode = Literal["fact", "reshaped", "precomputed_reasoning", "redirect"]
ReportChatSourceScope = Literal["pages_1_3", "page4_only", "page5_only", "page4_and_5", "mixed"]
ReportChatQuestionShape = Literal["narrow", "broad_summary", "comparison"]


REPORT_CHAT_SECTION_TARGETS = {
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
        "section_label": "Questions",
    },
}


EXPLAIN_KEYWORDS = (
    "why",
    "support",
    "supports",
    "evidence",
    "relate",
    "relates",
    "reason",
    "theme support",
    "signal support",
)
REDIRECT_KEYWORDS = (
    "should interviewer ask",
    "should the interviewer ask",
    "what should i ask",
    "what should the interviewer ask",
    "what should interviewer",
    "what should i probe",
    "what should i focus on",
    "probe more deeply",
    "follow up",
    "follow-up",
    "interview strategy",
    "interview question",
    "interview questions",
    "what stands out",
    "anything concerning",
    "key issues",
    "any problems",
    "what matters most",
    "areas of concern",
    "what are the weaknesses",
    "weaknesses",
    "strengths",
    "mismatch",
    "gap",
    "red flag",
)
TRANSFORM_KEYWORDS = (
    "summarise",
    "summarize",
    "summary",
    "short profile",
    "profile summary",
    "profile look like",
    "candidate like",
    "tell me about",
    "give me a profile",
    "overview",
    "bullet",
    "bullets",
    "trajectory",
)
WEAK_TRANSFORM_KEYWORDS = (
    "list",
    "list out",
    "show",
    "only",
    "filter",
    "all",
)
QUERY_NORMALIZATIONS = (
    ("what's", "what is"),
    ("who's", "who is"),
    ("applicant's", "applicant"),
    ("co-curriculars", "co curricular"),
    ("follow-up", "follow up"),
    ("head boy", "leadership"),
    ("head girl", "leadership"),
    ("writing sample", "essay"),
    ("personal statement", "essay"),
    ("sop", "essay"),
    ("extracurricular", "activity"),
    ("extracurriculars", "activities"),
    ("co curricular", "activity"),
    ("co curriculars", "activities"),
    ("board exam", "academics"),
    ("board exams", "academics"),
    ("jee advanced", "test"),
    ("jee mains", "test"),
    ("competitive exam", "test"),
    ("competitive exams", "tests"),
    ("entrance exam", "test"),
    ("entrance exams", "tests"),
    ("entrance performance", "test score"),
    ("entrance result", "test score"),
    ("marks", "score"),
    ("grade", "score"),
    ("grades", "scores"),
    ("percentage", "score"),
)


@dataclass(frozen=True)
class ReportChatRoute:
    operation: ReportChatOperation
    target: ReportChatTarget
    source_scope: ReportChatSourceScope
    selected_sections: list[str]
    answer_mode: ReportChatAnswerMode
    not_found_summary: str | None = None
    max_result_count: int = 3
    question_shape: ReportChatQuestionShape = "narrow"


class ReportChatError(Exception):
    """Raised when the report chatbot cannot safely answer."""


def _extract_json_candidate(response_text: str) -> str:
    text = response_text.strip()
    if not text:
        return text

    fenced_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    if text.startswith("{") and text.endswith("}"):
        return text

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace : last_brace + 1].strip()

    return text


def _recover_partial_report_chat_payload(response_text: str) -> dict[str, Any] | None:
    candidate = _extract_json_candidate(response_text)
    if not candidate:
        return None

    answer_summary_match = re.search(
        r'"answer_summary"\s*:\s*"((?:\\.|[^"\\])*)',
        candidate,
        flags=re.DOTALL,
    )
    if not answer_summary_match:
        return None

    raw_summary = answer_summary_match.group(1)
    try:
        decoded_summary = json.loads(f'"{raw_summary}"')
    except JSONDecodeError:
        decoded_summary = raw_summary.replace('\\"', '"').replace("\\n", "\n").strip()

    decoded_summary = decoded_summary.strip()
    if not decoded_summary:
        return None

    if not decoded_summary.endswith((".", "!", "?", "…")):
        decoded_summary = f"{decoded_summary}..."

    not_found_match = re.search(r'"not_found"\s*:\s*(true|false)', candidate, flags=re.IGNORECASE)
    not_found_value = not_found_match is not None and not_found_match.group(1).lower() == "true"

    return {
        "answer_summary": decoded_summary,
        "results": [],
        "not_found": not_found_value,
        "response_state": "degraded",
    }


def validate_report_chat_question(question: str, *, max_chars: int, max_words: int) -> str:
    normalized = " ".join(question.split())
    if not normalized:
        raise ReportChatError("Question cannot be empty")
    if len(normalized) > max_chars:
        raise ReportChatError(
            f"Question is too long. Keep it under {max_chars} characters so the report assistant stays focused."
        )
    if len(normalized.split()) > max_words:
        raise ReportChatError(
            f"Question is too long. Keep it under {max_words} words so the report assistant can answer efficiently."
        )
    return normalized


def _normalize_query_text(question: str) -> str:
    normalized = question.lower().replace("’", "'").replace("-", " ")
    for source, replacement in QUERY_NORMALIZATIONS:
        normalized = re.sub(rf"\b{re.escape(source)}\b", replacement, normalized)
    normalized = re.sub(r"(\w)'s\b", r"\1", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _tokenize_query(question: str) -> tuple[str, set[str]]:
    normalized = _normalize_query_text(question)
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    return normalized, tokens


def _matches_keywords(normalized: str, tokens: set[str], keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        if " " in keyword:
            if keyword in normalized:
                return True
        elif keyword in tokens:
            return True
    return False


def _detect_operation_from(normalized: str, tokens: set[str]) -> ReportChatOperation:
    if _matches_keywords(normalized, tokens, REDIRECT_KEYWORDS):
        return "redirect"
    if _matches_keywords(normalized, tokens, EXPLAIN_KEYWORDS):
        return "explain"
    if _matches_keywords(normalized, tokens, TRANSFORM_KEYWORDS):
        return "transform"
    if _matches_keywords(normalized, tokens, WEAK_TRANSFORM_KEYWORDS):
        weak_target = _detect_target_from(normalized, tokens, "retrieve")
        if weak_target in {"activities", "academics", "tests", "leadership", "essays", "full_report"}:
            return "transform"
    return "retrieve"


def _detect_question_shape(normalized: str, tokens: set[str]) -> ReportChatQuestionShape:
    broad_keywords = (
        "whole application",
        "entire report",
        "everything",
        "all details",
        "deep analysis",
        "full profile",
        "overall",
        "good or bad profile",
        "what is this candidate like overall",
        "tell me everything",
    )
    if _matches_keywords(normalized, tokens, broad_keywords):
        return "broad_summary"

    compare_keywords = ("compare", "comparison", "versus", "vs", "gap", "mismatch")
    if _matches_keywords(normalized, tokens, compare_keywords):
        domain_hits = 0
        for domain_keywords in (
            ("academic", "academics", "school", "board", "10th", "12th", "performance"),
            ("test", "tests", "jee", "sat", "act", "mains", "entrance exam"),
            ("activity", "activities", "club", "competition", "robotics"),
            ("essay", "essays", "writing", "statement"),
            ("leadership", "captain", "president", "leader"),
        ):
            if _matches_keywords(normalized, tokens, domain_keywords):
                domain_hits += 1
        if domain_hits >= 2:
            return "comparison"

    return "narrow"


def detect_operation(question: str) -> ReportChatOperation:
    normalized, tokens = _tokenize_query(question)
    return _detect_operation_from(normalized, tokens)


def _detect_target_from(normalized: str, tokens: set[str], operation: ReportChatOperation) -> ReportChatTarget:

    if operation == "redirect":
        if _matches_keywords(normalized, tokens, ("ask", "probe", "interview", "follow up", "question")):
            return "question_groups"
        return "signals"

    if _matches_keywords(normalized, tokens, ("focus area", "focus areas", "theme", "themes")):
        return "themes"
    if _matches_keywords(normalized, tokens, ("signal", "signals", "concern", "weakness", "strength", "mismatch", "gap")):
        return "signals"
    if _matches_keywords(normalized, tokens, ("essay", "essays", "writing", "prompt", "statement")):
        return "essays"
    if _matches_keywords(
        normalized,
        tokens,
        (
            "jee",
            "sat",
            "act",
            "ielts",
            "toefl",
            "competitive exam",
            "entrance exam",
            "entrance score",
            "mains",
            "test",
            "tests",
            "standardized",
        ),
    ):
        return "tests"
    if _matches_keywords(normalized, tokens, ("activity", "activities", "club", "competition", "sports", "robotics")):
        return "activities"
    if _matches_keywords(normalized, tokens, ("leadership", "captain", "president", "leader", "leadership role")):
        return "leadership"
    if operation == "transform" and _matches_keywords(
        normalized,
        tokens,
        ("profile", "applicant", "candidate", "about", "full profile"),
    ):
        return "full_report"
    if _matches_keywords(
        normalized,
        tokens,
        ("10th", "12th", "class 10", "class 12", "board", "academic", "academically", "academics", "school", "performance", "perform"),
    ):
        return "academics"
    if _matches_keywords(normalized, tokens, ("name", "major", "background", "profile", "family", "home", "city", "state", "country", "identity")):
        return "identity"
    if _matches_keywords(
        normalized,
        tokens,
        ("today", "overall", "applicant", "full report", "entire report", "about", "tell me about", "what is this candidate", "full profile", "who is", "give me a profile"),
    ):
        return "full_report"

    if operation == "transform":
        return "full_report"
    if operation == "explain":
        return "signals"
    return "full_report"


def detect_target(question: str, operation: ReportChatOperation) -> ReportChatTarget:
    normalized, tokens = _tokenize_query(question)
    return _detect_target_from(normalized, tokens, operation)


def _page4_or_page5_missing_summary(operation: ReportChatOperation, target: ReportChatTarget) -> str:
    if target == "question_groups":
        return "Interview guidance is not available because Page 5 has not been generated for this report yet."
    if operation == "redirect":
        return "The report does not include a generated Page 4/5 summary for that request yet."
    return "That explanation is not available because the generated report sections are not present yet."


def _result_cap_for(operation: ReportChatOperation) -> int:
    if operation == "redirect":
        return 2
    if operation == "explain":
        return 2
    return 3


def _route_for(
    operation: ReportChatOperation,
    target: ReportChatTarget,
    has_final_report: bool,
    question_shape: ReportChatQuestionShape,
) -> ReportChatRoute:
    if question_shape == "comparison":
        if has_final_report:
            return ReportChatRoute(
                operation="explain" if operation == "retrieve" else operation,
                target="signals",
                source_scope="page4_only",
                selected_sections=["page4_focus_areas"],
                answer_mode="precomputed_reasoning",
                max_result_count=2,
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation="transform" if operation == "retrieve" else operation,
            target="full_report",
            source_scope="pages_1_3",
            selected_sections=[
                "page1_overview",
                "page2_academics",
                "page2_tests",
                "page2_activities",
                "page2_leadership",
                "page3_essays",
            ],
            answer_mode="reshaped",
            max_result_count=2,
            question_shape=question_shape,
        )

    if operation == "redirect":
        if target == "question_groups":
            if not has_final_report:
                return ReportChatRoute(
                    operation=operation,
                    target=target,
                    source_scope="page5_only",
                    selected_sections=[],
                    answer_mode="redirect",
                    not_found_summary=_page4_or_page5_missing_summary(operation, target),
                    max_result_count=_result_cap_for(operation),
                    question_shape=question_shape,
                )
            return ReportChatRoute(
                operation,
                target,
                "page5_only",
                ["page5_question_groups"],
                "redirect",
                max_result_count=_result_cap_for(operation),
                question_shape=question_shape,
            )
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="redirect",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                max_result_count=_result_cap_for(operation),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page4_only",
            ["page4_focus_areas"],
            "redirect",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )

    if operation == "explain":
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="precomputed_reasoning",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                max_result_count=_result_cap_for(operation),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page4_only",
            ["page4_focus_areas"],
            "precomputed_reasoning",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )

    if target == "themes" or target == "signals":
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="fact" if operation == "retrieve" else "precomputed_reasoning",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                max_result_count=_result_cap_for(operation),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page4_only",
            ["page4_focus_areas"],
            "fact" if operation == "retrieve" else "precomputed_reasoning",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )

    if target == "question_groups":
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page5_only",
                selected_sections=[],
                answer_mode="redirect" if operation == "redirect" else "fact",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                max_result_count=_result_cap_for(operation),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page5_only",
            ["page5_question_groups"],
            "redirect" if operation == "redirect" else "fact",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )

    if question_shape == "broad_summary":
        return ReportChatRoute(
            operation="transform",
            target="full_report",
            source_scope="pages_1_3" if not has_final_report else "mixed",
            selected_sections=[
                "page1_overview",
                "page2_academics",
                "page2_tests",
                "page2_activities",
                "page2_leadership",
                "page3_essays",
                *([] if not has_final_report else ["page4_focus_areas"]),
            ],
            answer_mode="reshaped",
            max_result_count=2,
            question_shape=question_shape,
        )

    if target == "identity":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page1_overview"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )
    if target == "academics":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page2_academics"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )
    if target == "tests":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page2_tests"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )
    if target == "activities":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page2_activities"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )
    if target == "leadership":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page2_leadership"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )
    if target == "essays":
        return ReportChatRoute(
            operation,
            target,
            "pages_1_3",
            ["page3_essays"],
            "fact" if operation == "retrieve" else "reshaped",
            max_result_count=_result_cap_for(operation),
            question_shape=question_shape,
        )

    selected_sections = [
        "page1_overview",
        "page2_academics",
        "page2_tests",
        "page2_activities",
        "page2_leadership",
        "page3_essays",
    ]
    return ReportChatRoute(
        operation,
        target,
        "pages_1_3",
        selected_sections,
        "reshaped" if operation == "transform" else "fact",
        max_result_count=_result_cap_for(operation),
        question_shape=question_shape,
    )


def _build_selected_pages(
    selected_sections: list[str],
    review_package_pages: dict[str, Any],
    final_report_content: Optional[dict[str, Any]],
) -> dict[str, Any]:
    pages: dict[str, Any] = {}
    if "page1_overview" in selected_sections:
        pages["page1"] = review_package_pages.get("page_1_background_profile", {})
    if any(section in selected_sections for section in ("page2_academics", "page2_tests", "page2_activities", "page2_leadership")):
        page2 = review_package_pages.get("page_2_academic_and_engagement", {})
        pages["page2"] = {
            key: value
            for key, value in {
                "academic_records": page2.get("academic_records", []) if "page2_academics" in selected_sections else [],
                "standardized_tests": page2.get("standardized_tests", []) if "page2_tests" in selected_sections else [],
                "extracurricular_activities": page2.get("extracurricular_activities", []) if "page2_activities" in selected_sections else [],
                "leadership_roles": page2.get("leadership_roles", []) if "page2_leadership" in selected_sections else [],
            }.items()
            if value
        }
    if "page3_essays" in selected_sections:
        pages["page3"] = review_package_pages.get("page_3_essays", {})
    if final_report_content and "page4_focus_areas" in selected_sections:
        pages["page4"] = final_report_content.get("page_4_focus_areas", {})
    if final_report_content and "page5_question_groups" in selected_sections:
        pages["page5"] = final_report_content.get("page_5_question_groups", {})
    return pages


def build_report_chat_context(
    question: str,
    review_package_pages: dict[str, Any],
    final_report_content: Optional[dict[str, Any]],
) -> dict[str, Any]:
    has_final_report = bool(final_report_content)
    normalized, tokens = _tokenize_query(question)
    operation = _detect_operation_from(normalized, tokens)
    target = _detect_target_from(normalized, tokens, operation)
    question_shape = _detect_question_shape(normalized, tokens)
    route = _route_for(operation, target, has_final_report, question_shape)
    pages = _build_selected_pages(route.selected_sections, review_package_pages, final_report_content)

    context: dict[str, Any] = {
        "source_scope": route.source_scope,
        "selected_sections": route.selected_sections,
        "detected_operation": route.operation,
        "detected_target": route.target,
        "question_shape_bucket": question_shape,
        "answer_mode": route.answer_mode,
        "max_result_count": route.max_result_count,
        "pages": pages,
        "section_targets": [
            {
                "section_key": section_key,
                "target_tab": target_meta["target_tab"],
                "anchor_id": target_meta["anchor_id"],
                "page_label": target_meta["page_label"],
                "section_label": target_meta["section_label"],
            }
            for section_key, target_meta in REPORT_CHAT_SECTION_TARGETS.items()
            if section_key in route.selected_sections
        ],
    }
    if route.not_found_summary:
        context["not_found_summary"] = route.not_found_summary

    logger.info(
        "Report chat routed operation=%s target=%s selected_sections=%s source_scope=%s",
        route.operation,
        route.target,
        route.selected_sections,
        route.source_scope,
    )
    return context


def _build_report_chat_repair_messages(raw_response_text: str, max_result_count: int) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Convert the malformed assistant output into valid JSON only.\n"
                "Do not add facts or infer missing evidence.\n"
                "If you cannot safely reconstruct results, return results=[].\n"
                "Return at most "
                f"{max_result_count}"
                " results.\n"
                'Return exactly this shape: {"answer_summary":"string","results":[{"label":"string","value":"string","target_tab":"page1|page2|page3|page4|page5","section_key":"page1_overview|page2_academics|page2_tests|page2_activities|page2_leadership|page3_essays|page4_focus_areas|page5_question_groups","anchor_id":"string"}],"not_found":boolean,"response_state":"clean|repaired|retried|degraded"}.\n'
                'Use response_state="repaired".'
            ),
        },
        {
            "role": "user",
            "content": raw_response_text,
        },
    ]


def _looks_like_absence_summary(summary: str) -> bool:
    lowered = summary.lower()
    absence_markers = (
        "could not find",
        "not available",
        "not present",
        "does not provide",
        "does not contain",
        "not included",
        "is unavailable",
        "unable to find",
        "is absent",
    )
    return any(marker in lowered for marker in absence_markers)


def _normalize_report_chat_response(parsed: ReportChatResponse, context: dict[str, Any]) -> ReportChatResponse:
    if parsed.results:
        return ReportChatResponse(
            answer_summary=parsed.answer_summary,
            results=parsed.results,
            not_found=False,
            response_state=parsed.response_state,
        )

    summary = (parsed.answer_summary or "").strip()
    question_shape = str(context.get("question_shape_bucket", "narrow"))
    operation = str(context.get("detected_operation", "retrieve"))

    if summary and (question_shape in {"broad_summary", "comparison"} or operation in {"transform", "redirect", "explain"}):
        return ReportChatResponse(
            answer_summary=summary,
            results=[],
            not_found=False,
            response_state=parsed.response_state,
        )

    if parsed.not_found and _looks_like_absence_summary(summary):
        return parsed

    if summary and not parsed.not_found:
        return ReportChatResponse(
            answer_summary=summary,
            results=[],
            not_found=False,
            response_state=parsed.response_state,
        )

    return parsed


def _report_chat_json_schema(max_result_count: int) -> dict[str, Any]:
    return {
        "name": "report_chat_response",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "answer_summary": {"type": "string"},
                "results": {
                    "type": "array",
                    "maxItems": max_result_count,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                            "target_tab": {"type": "string", "enum": ["page1", "page2", "page3", "page4", "page5"]},
                            "section_key": {
                                "type": "string",
                                "enum": [
                                    "page1_overview",
                                    "page2_academics",
                                    "page2_tests",
                                    "page2_activities",
                                    "page2_leadership",
                                    "page3_essays",
                                    "page4_focus_areas",
                                    "page5_question_groups",
                                ],
                            },
                            "anchor_id": {"type": "string"},
                        },
                        "required": ["label", "value", "target_tab", "section_key", "anchor_id"],
                    },
                },
                "not_found": {"type": "boolean"},
                "response_state": {
                    "type": "string",
                    "enum": ["clean", "repaired", "retried", "degraded"],
                },
            },
            "required": ["answer_summary", "results", "not_found", "response_state"],
        },
    }


def _build_report_chat_messages(question: str, context: dict[str, Any]) -> list[dict[str, str]]:
    max_result_count = int(context.get("max_result_count", 3))
    return [
        {
            "role": "system",
            "content": (
                "You answer one-shot questions from a structured application report.\n"
                "Use only the supplied report context.\n"
                "This assistant is read-only and non-inferential.\n"
                "Never add new judgment, evaluation, or conclusions beyond the provided report.\n"
                "The context includes detected_operation, detected_target, answer_mode, selected sections, section targets, and max_result_count.\n"
                "Behavior by answer_mode:\n"
                "- fact: return exact factual information from the provided report context.\n"
                "- reshaped: restate the same information in a new format without adding conclusions.\n"
                "- precomputed_reasoning: only restate existing Page 4 reasoning/evidence already in the report.\n"
                "- redirect: answer briefly using only Page 4/5 content, then point to the most relevant Page 4/5 section.\n"
                "Use only section targets listed in the provided context.\n"
                "Do not use external knowledge.\n"
                "Do not wrap the JSON in markdown fences.\n"
                f"Return at most {max_result_count} results.\n"
                "For broad or full-report questions, return a concise summary and only the top relevant anchors instead of an exhaustive dump.\n"
                "Return JSON only with this shape: "
                '{"answer_summary":"string","results":[{"label":"string","value":"string","target_tab":"page1|page2|page3|page4|page5","section_key":"page1_overview|page2_academics|page2_tests|page2_activities|page2_leadership|page3_essays|page4_focus_areas|page5_question_groups","anchor_id":"string"}],"not_found":boolean,"response_state":"clean|repaired|retried|degraded"}.\n'
                'Set response_state="clean" when answering normally.\n'
                "If the answer is absent or unsupported by the supplied report, return not_found=true and results=[].\n"
                "Keep answer_summary concise, factual, and grounded in the provided report only."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"question": question, "report_context": context}),
        },
    ]


def _parse_report_chat_payload(response_text: str) -> tuple[dict[str, Any] | None, str]:
    json_candidate = _extract_json_candidate(response_text)
    try:
        parsed_payload = json.loads(json_candidate)
        response_state = "repaired" if json_candidate != response_text.strip() else "clean"
        return parsed_payload, response_state
    except JSONDecodeError:
        recovered_payload = _recover_partial_report_chat_payload(response_text)
        if recovered_payload is not None:
            return recovered_payload, "degraded"
    return None, "invalid"


def _validate_report_chat_payload(
    parsed_payload: dict[str, Any],
    *,
    response_state: str,
    max_result_count: int,
) -> ReportChatResponse:
    payload = dict(parsed_payload)
    payload["response_state"] = response_state
    if len(payload.get("results", [])) > max_result_count:
        payload["results"] = payload["results"][:max_result_count]
    return ReportChatResponse.model_validate(payload)


def answer_report_question(question: str, context: dict[str, Any]) -> ReportChatResponse:
    if context.get("not_found_summary") and not context.get("section_targets"):
        return ReportChatResponse(
            answer_summary=str(context["not_found_summary"]),
            results=[],
            not_found=True,
            response_state="clean",
        )

    messages = _build_report_chat_messages(question, context)
    max_result_count = int(context.get("max_result_count", 3))
    schema_request = LLMRequestOptions(
        response_format_type="json_schema",
        response_schema=_report_chat_json_schema(max_result_count),
        temperature_override=0.1,
    )
    json_object_request = LLMRequestOptions(
        response_format_type="json_object",
        temperature_override=0.1,
    )

    try:
        response_text = generate(messages, call_label="report_chat", request_options=schema_request)
    except LLMStructuredOutputUnsupportedError:
        logger.warning("Report chat provider rejected json_schema; downgrading to json_object mode.")
        try:
            response_text = generate(messages, call_label="report_chat", request_options=json_object_request)
        except LLMClientError as exc:
            raise ReportChatError("Report assistant is temporarily unavailable.") from exc
    except LLMClientError as exc:
        raise ReportChatError("Report assistant is temporarily unavailable.") from exc

    parsed_payload, response_state = _parse_report_chat_payload(response_text)
    if parsed_payload is None:
        logger.warning("Report chat parse failed on primary attempt; running repair-model pass.")
        try:
            repair_text = generate(
                _build_report_chat_repair_messages(response_text, max_result_count),
                call_label="report_chat",
                request_options=LLMRequestOptions(
                    response_format_type="json_object",
                    temperature_override=0.0,
                    prefer_fallback_model=True,
                ),
            )
        except LLMClientError:
            repair_text = ""

        if repair_text:
            parsed_payload, repair_state = _parse_report_chat_payload(repair_text)
            if parsed_payload is not None:
                response_state = "repaired" if repair_state != "degraded" else "degraded"

    if parsed_payload is None:
        logger.warning("Report chat repair-model pass failed; retrying with fallback model.")
        try:
            retry_text = generate(
                messages,
                call_label="report_chat",
                request_options=LLMRequestOptions(
                    response_format_type="json_object",
                    temperature_override=0.1,
                    prefer_fallback_model=True,
                ),
            )
        except LLMClientError as exc:
            raise ReportChatError("Report assistant is temporarily unavailable.") from exc
        parsed_payload, retry_state = _parse_report_chat_payload(retry_text)
        if parsed_payload is None:
            logger.error(
                "Report chat invalid JSON response after repair and retry. raw_response=%r repair_response=%r retry_response=%r question_shape=%s",
                response_text,
                repair_text if 'repair_text' in locals() else "",
                retry_text,
                context.get("question_shape_bucket"),
            )
            raise ReportChatError("Report assistant returned an invalid response.")
        response_state = "retried" if retry_state == "clean" else "degraded"

    try:
        parsed = _validate_report_chat_payload(
            parsed_payload,
            response_state=response_state,
            max_result_count=max_result_count,
        )
    except ValidationError as exc:
        logger.warning("Report chat schema validation failed on parsed payload; retrying with fallback model.")
        try:
            retry_text = generate(
                messages,
                call_label="report_chat",
                request_options=LLMRequestOptions(
                    response_format_type="json_object",
                    temperature_override=0.1,
                    prefer_fallback_model=True,
                ),
            )
        except LLMClientError as retry_exc:
            raise ReportChatError("Report assistant is temporarily unavailable.") from retry_exc
        parsed_retry_payload, retry_state = _parse_report_chat_payload(retry_text)
        if parsed_retry_payload is None:
            logger.error(
                "Report chat schema retry failed. raw_response=%r retry_response=%r question_shape=%s errors=%s",
                response_text,
                retry_text,
                context.get("question_shape_bucket"),
                exc.errors(),
            )
            raise ReportChatError("Report assistant returned an invalid response.") from exc
        try:
            parsed = _validate_report_chat_payload(
                parsed_retry_payload,
                response_state="retried" if retry_state == "clean" else "degraded",
                max_result_count=max_result_count,
            )
        except ValidationError as retry_exc:
            logger.error(
                "Report chat schema validation failed after retry. raw_response=%r retry_response=%r question_shape=%s errors=%s",
                response_text,
                retry_text,
                context.get("question_shape_bucket"),
                retry_exc.errors(),
            )
            raise ReportChatError("Report assistant returned an invalid response.") from retry_exc

    parsed = _normalize_report_chat_response(parsed, context)

    if parsed.not_found:
        logger.info(
            "Report chat completed status=not_found shape=%s operation=%s target=%s response_state=%s result_count=%s",
            context.get("question_shape_bucket"),
            context.get("detected_operation"),
            context.get("detected_target"),
            parsed.response_state,
            len(parsed.results),
        )
        return parsed

    if not parsed.results:
        normalized = ReportChatResponse(
            answer_summary=parsed.answer_summary or "I could summarize that from the current report, but section links are unavailable.",
            results=[],
            not_found=False,
            response_state="degraded" if parsed.response_state == "clean" else parsed.response_state,
        )
        logger.info(
            "Report chat completed status=degraded_success shape=%s operation=%s target=%s response_state=%s result_count=0",
            context.get("question_shape_bucket"),
            context.get("detected_operation"),
            context.get("detected_target"),
            normalized.response_state,
        )
        return normalized

    logger.info(
        "Report chat completed status=clean_success shape=%s operation=%s target=%s response_state=%s result_count=%s",
        context.get("question_shape_bucket"),
        context.get("detected_operation"),
        context.get("detected_target"),
        parsed.response_state,
        len(parsed.results),
    )
    return parsed
