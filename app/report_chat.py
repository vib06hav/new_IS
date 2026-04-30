import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Literal, Optional

from app.api.schemas import ReportChatResponse, ReportChatSource
from app.llm.client import LLMClientError, generate


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
ReportChatResponseKind = Literal["lookup", "domain_summary", "scope_redirect", "degraded"]
ReportChatCoverageMode = Literal["single_fact", "all_items", "domain_summary"]


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
    "tell me about",
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
SCOPE_REDIRECT_KEYWORDS = (
    "candidate",
    "participant",
    "profile",
    "overall",
    "whole",
    "entire",
    "person",
    "impressive",
    "strong applicant",
    "weak applicant",
    "assess",
    "evaluation",
    "evaluate",
    "judge",
)
SUMMARY_ALLOWED_TARGETS = {
    "academics",
    "tests",
    "activities",
    "leadership",
    "essays",
    "themes",
    "signals",
    "question_groups",
}
COMMON_QUERY_FILLER_TOKENS = {
    "a",
    "all",
    "an",
    "and",
    "any",
    "are",
    "can",
    "for",
    "give",
    "in",
    "is",
    "listed",
    "list",
    "me",
    "of",
    "on",
    "show",
    "the",
    "their",
    "there",
    "these",
    "this",
    "those",
    "what",
    "which",
}
ACTIVITY_DOMAIN_TOKENS = {
    "activity",
    "activities",
    "club",
    "clubs",
    "competition",
    "competitions",
    "sports",
    "internship",
    "internships",
    "extracurricular",
    "extracurriculars",
    "co",
    "curricular",
    "cocurricular",
}
LEADERSHIP_DOMAIN_TOKENS = {
    "leadership",
    "leader",
    "leaders",
    "role",
    "roles",
    "captain",
    "president",
}
TEST_DOMAIN_TOKENS = {
    "test",
    "tests",
    "standardized",
    "exam",
    "exams",
    "entrance",
    "score",
    "scores",
    "result",
    "results",
}
ACADEMIC_DOMAIN_TOKENS = {
    "academic",
    "academics",
    "board",
    "boards",
    "class",
    "school",
    "performance",
    "score",
    "scores",
    "subject",
    "subjects",
}
ESSAY_DOMAIN_TOKENS = {
    "essay",
    "essays",
    "writing",
    "prompt",
    "statement",
}


@dataclass(frozen=True)
class ReportChatRoute:
    operation: ReportChatOperation
    target: ReportChatTarget
    source_scope: ReportChatSourceScope
    selected_sections: list[str]
    answer_mode: ReportChatAnswerMode
    not_found_summary: str | None = None
    question_shape: ReportChatQuestionShape = "narrow"


class ReportChatError(Exception):
    """Raised when the report chatbot cannot safely answer."""


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
    normalized = question.lower().replace("â€™", "'").replace("-", " ")
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


def _contains_score_intent(normalized: str, tokens: set[str]) -> bool:
    return _matches_keywords(
        normalized,
        tokens,
        ("score", "scores", "marks", "grade", "grades", "percentage", "percentile", "rank", "result"),
    )


def _detect_operation_from(normalized: str, tokens: set[str]) -> ReportChatOperation:
    if _matches_keywords(normalized, tokens, REDIRECT_KEYWORDS):
        return "redirect"
    if _matches_keywords(normalized, tokens, EXPLAIN_KEYWORDS):
        return "explain"
    if _matches_keywords(normalized, tokens, TRANSFORM_KEYWORDS):
        return "transform"
    if _matches_keywords(normalized, tokens, WEAK_TRANSFORM_KEYWORDS):
        weak_target = _detect_target_from(normalized, tokens, "retrieve")
        if weak_target in SUMMARY_ALLOWED_TARGETS:
            return "transform"
    return "retrieve"


def _detect_question_shape(normalized: str, tokens: set[str]) -> ReportChatQuestionShape:
    broad_keywords = (
        "whole application",
        "entire report",
        "everything",
        "all details",
        "full profile",
        "what is this candidate like overall",
        "tell me everything",
    )
    if _matches_keywords(normalized, tokens, broad_keywords):
        return "broad_summary"

    compare_keywords = ("compare", "comparison", "versus", "vs", "gap", "mismatch")
    if _matches_keywords(normalized, tokens, compare_keywords):
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
    if _matches_keywords(normalized, tokens, ("activity", "activities", "club", "competition", "sports", "robotics", "internship")):
        return "activities"
    if _matches_keywords(normalized, tokens, ("leadership", "captain", "president", "leader", "leadership role")):
        return "leadership"
    if _matches_keywords(
        normalized,
        tokens,
        ("10th", "11th", "12th", "class 10", "class 11", "class 12", "board", "academic", "academically", "academics", "school", "performance", "perform"),
    ):
        return "academics"
    if _matches_keywords(normalized, tokens, ("name", "major", "background", "family", "home", "city", "state", "country", "identity")):
        return "identity"
    if _matches_keywords(
        normalized,
        tokens,
        ("today", "overall", "applicant", "full report", "entire report", "about", "what is this candidate", "full profile"),
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
        return "The report does not include generated focus areas or interview questions for that request yet."
    return "That summary is not available because the generated report sections are not present yet."


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
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation="transform",
            target="full_report",
            source_scope="pages_1_3",
            selected_sections=[
                "page2_academics",
                "page2_tests",
            ],
            answer_mode="reshaped",
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
                    question_shape=question_shape,
                )
            return ReportChatRoute(operation, target, "page5_only", ["page5_question_groups"], "redirect", question_shape=question_shape)
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="redirect",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                question_shape=question_shape,
            )
        return ReportChatRoute(operation, target, "page4_only", ["page4_focus_areas"], "redirect", question_shape=question_shape)

    if operation == "explain":
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="precomputed_reasoning",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page4_only",
            ["page4_focus_areas"],
            "precomputed_reasoning",
            question_shape=question_shape,
        )

    if target in {"themes", "signals"}:
        if not has_final_report:
            return ReportChatRoute(
                operation=operation,
                target=target,
                source_scope="page4_only",
                selected_sections=[],
                answer_mode="precomputed_reasoning" if operation != "retrieve" else "fact",
                not_found_summary=_page4_or_page5_missing_summary(operation, target),
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page4_only",
            ["page4_focus_areas"],
            "precomputed_reasoning" if operation != "retrieve" else "fact",
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
                question_shape=question_shape,
            )
        return ReportChatRoute(
            operation,
            target,
            "page5_only",
            ["page5_question_groups"],
            "redirect" if operation == "redirect" else "fact",
            question_shape=question_shape,
        )

    if target == "identity":
        return ReportChatRoute(operation, target, "pages_1_3", ["page1_overview"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)
    if target == "academics":
        return ReportChatRoute(operation, target, "pages_1_3", ["page2_academics"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)
    if target == "tests":
        return ReportChatRoute(operation, target, "pages_1_3", ["page2_tests"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)
    if target == "activities":
        return ReportChatRoute(operation, target, "pages_1_3", ["page2_activities"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)
    if target == "leadership":
        return ReportChatRoute(operation, target, "pages_1_3", ["page2_leadership"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)
    if target == "essays":
        return ReportChatRoute(operation, target, "pages_1_3", ["page3_essays"], "fact" if operation == "retrieve" else "reshaped", question_shape=question_shape)

    selected_sections = [
        "page1_overview",
        "page2_academics",
        "page2_tests",
        "page2_activities",
        "page2_leadership",
        "page3_essays",
    ]
    if has_final_report:
        selected_sections.extend(["page4_focus_areas", "page5_question_groups"])
    return ReportChatRoute(operation, target, "mixed" if has_final_report else "pages_1_3", selected_sections, "reshaped", question_shape=question_shape)


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
                "co_curricular_activities": page2.get("co_curricular_activities", []) if "page2_activities" in selected_sections else [],
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


def _extract_annotations(final_report_content: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(final_report_content, dict):
        return {}
    signal_data = final_report_content.get("signal_data")
    if not isinstance(signal_data, dict):
        return {}
    annotations = signal_data.get("annotations")
    return annotations if isinstance(annotations, dict) else {}


def _determine_response_kind(
    normalized: str,
    tokens: set[str],
    operation: ReportChatOperation,
    target: ReportChatTarget,
    question_shape: ReportChatQuestionShape,
) -> ReportChatResponseKind:
    if target == "full_report":
        return "scope_redirect"
    if question_shape == "broad_summary":
        return "scope_redirect"
    if operation == "redirect" and target == "signals":
        return "scope_redirect"
    if operation in {"transform", "redirect"} and _matches_keywords(normalized, tokens, SCOPE_REDIRECT_KEYWORDS):
        return "scope_redirect"
    if operation == "retrieve":
        return "lookup"
    return "domain_summary"


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
    response_kind = _determine_response_kind(normalized, tokens, route.operation, route.target, question_shape)
    pages = _build_selected_pages(route.selected_sections, review_package_pages, final_report_content)

    context: dict[str, Any] = {
        "raw_question": question,
        "normalized_question": normalized,
        "question_tokens": sorted(tokens),
        "response_kind": response_kind,
        "source_scope": route.source_scope,
        "selected_sections": route.selected_sections,
        "detected_operation": route.operation,
        "detected_target": route.target,
        "question_shape_bucket": question_shape,
        "answer_mode": route.answer_mode,
        "pages": pages,
        "annotations": _extract_annotations(final_report_content),
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
    context["coverage_mode"] = _detect_coverage_mode(question, context)

    logger.info(
        "Report chat routed response_kind=%s operation=%s target=%s selected_sections=%s source_scope=%s coverage_mode=%s",
        response_kind,
        route.operation,
        route.target,
        route.selected_sections,
        route.source_scope,
        context["coverage_mode"],
    )
    return context


def _section_target(section_key: str) -> dict[str, str]:
    return REPORT_CHAT_SECTION_TARGETS[section_key]


def _entity_anchor_id(entity_id: str) -> str:
    return f"report-entity-{entity_id.lower()}"


def _fragment_anchor_id(fragment_id: str) -> str:
    return f"report-fragment-{fragment_id.lower()}"


def _build_source(
    section_key: str,
    *,
    label: Optional[str] = None,
    entity_id: Optional[str] = None,
    fragment_id: Optional[str] = None,
) -> ReportChatSource:
    target = _section_target(section_key)
    anchor_id = target["anchor_id"]
    if fragment_id:
        anchor_id = _fragment_anchor_id(fragment_id)
    elif entity_id:
        anchor_id = _entity_anchor_id(entity_id)

    return ReportChatSource(
        label=label or target["section_label"],
        target_tab=target["target_tab"],
        section_key=section_key,
        anchor_id=anchor_id,
        entity_id=entity_id,
        fragment_id=fragment_id,
    )


def _safe_string(value: Any) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _filter_informative_tokens(tokens: set[str], domain_tokens: set[str]) -> set[str]:
    return {token for token in tokens if token not in COMMON_QUERY_FILLER_TOKENS and token not in domain_tokens}


def _detect_activity_bucket(question: str) -> str | None:
    lowered = question.lower().replace("-", " ")
    if "co curricular" in lowered or "cocurricular" in lowered:
        return "co_curricular"
    if "extracurricular" in lowered or "extra curricular" in lowered:
        return "extracurricular"
    return None


def _normalized_text(value: Any) -> str:
    return _normalize_query_text(_safe_string(value) or "")


def _extract_academic_level(normalized: str) -> str | None:
    patterns = (
        ("class 10", "Class 10"),
        ("10th", "Class 10"),
        ("class 11", "Class 11"),
        ("11th", "Class 11"),
        ("class 12", "Class 12"),
        ("12th", "Class 12"),
    )
    for needle, label in patterns:
        if needle in normalized:
            return label
    return None


def _record_matches_level(record: dict[str, Any], level: str) -> bool:
    return _normalized_text(record.get("academic_level")) == _normalize_query_text(level)


def _find_subject_match(record: dict[str, Any], tokens: set[str]) -> dict[str, Any] | None:
    for subject in record.get("subject_entries", []) or []:
        if not isinstance(subject, dict):
            continue
        subject_name = _normalized_text(subject.get("subject_name"))
        if not subject_name:
            continue
        subject_tokens = set(subject_name.split())
        if subject_tokens & tokens:
            return subject
    return None


def _format_score(value: Any, max_value: Any = None, grading_mode: Any = None) -> str | None:
    score = _safe_string(value)
    if not score:
        return None
    max_score = _safe_string(max_value)
    if max_score:
        return f"{score}/{max_score}"
    if _safe_string(grading_mode) and _safe_string(grading_mode).lower() == "percentage":
        return f"{score}%"
    return score


def _find_test_match(tests: list[dict[str, Any]], normalized: str, tokens: set[str]) -> dict[str, Any] | None:
    named_matches: list[dict[str, Any]] = []
    for entry in tests:
        if not isinstance(entry, dict):
            continue
        test_name = _normalized_text(entry.get("test_name"))
        if not test_name:
            continue
        if test_name in normalized or set(test_name.split()) & tokens:
            named_matches.append(entry)
    if named_matches:
        return named_matches[0]
    if len(tests) == 1 and (_contains_score_intent(normalized, tokens) or "entrance" in tokens or "test" in tokens):
        return tests[0]
    return None


def _find_activity_match(activities: list[dict[str, Any]], tokens: set[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for entry in activities:
        haystack = " ".join(
            filter(
                None,
                (
                    _safe_string(entry.get("activity_name")),
                    _safe_string(entry.get("activity_type")),
                    _safe_string(entry.get("position_title")),
                    _safe_string(entry.get("description_raw")),
                ),
            )
        )
        haystack_tokens = set(_normalize_query_text(haystack).split())
        if haystack_tokens & tokens:
            matches.append(entry)
    return matches


def _activity_entries(page2: dict[str, Any], bucket: str | None = None) -> list[dict[str, Any]]:
    if bucket == "extracurricular":
        entries = page2.get("extracurricular_activities", [])
        return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    if bucket == "co_curricular":
        entries = page2.get("co_curricular_activities", [])
        return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []

    combined: list[dict[str, Any]] = []
    for collection_name in ("extracurricular_activities", "co_curricular_activities"):
        entries = page2.get(collection_name, [])
        if isinstance(entries, list):
            combined.extend(entry for entry in entries if isinstance(entry, dict))
    return combined


def _source_list_for_entries(section_key: str, entries: list[dict[str, Any]], label_key: str) -> list[ReportChatSource]:
    built: list[ReportChatSource] = []
    for entry in entries:
        label = _safe_string(entry.get(label_key))
        entity_id = _safe_string(entry.get("entity_id"))
        if label and entity_id:
            built.append(_build_source(section_key, label=label, entity_id=entity_id))
        if len(built) >= 4:
            break
    return built


def _render_label_series(labels: list[str]) -> str:
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"


def _list_activity_items(entries: list[dict[str, Any]], bucket: str | None) -> ReportChatResponse:
    if not entries:
        if bucket == "extracurricular":
            return _lookup_response("No extracurricular activities are listed in the Activities section.", [_build_source("page2_activities")], not_found=True)
        if bucket == "co_curricular":
            return _lookup_response("No co-curricular activities are listed in the Activities section.", [_build_source("page2_activities")], not_found=True)
        return _lookup_response("No activities are listed in the Activities section.", [_build_source("page2_activities")], not_found=True)

    extracurricular_labels = [label for label in (_safe_string(entry.get("activity_name")) for entry in entries if _activity_type_bucket(entry.get("activity_type")) == "extracurricular") if label]
    co_curricular_labels = [label for label in (_safe_string(entry.get("activity_name")) for entry in entries if _activity_type_bucket(entry.get("activity_type")) == "co_curricular") if label]

    if bucket == "extracurricular":
        message = f"The extracurricular activities listed are {_render_label_series(extracurricular_labels)}."
    elif bucket == "co_curricular":
        message = f"The co-curricular activities listed are {_render_label_series(co_curricular_labels)}."
    elif extracurricular_labels and co_curricular_labels:
        message = (
            f"The activities section lists extracurricular activities: {_render_label_series(extracurricular_labels)}. "
            f"It also lists co-curricular activities: {_render_label_series(co_curricular_labels)}."
        )
    elif extracurricular_labels:
        message = f"The activities section lists extracurricular activities: {_render_label_series(extracurricular_labels)}."
    elif co_curricular_labels:
        message = f"The activities section lists co-curricular activities: {_render_label_series(co_curricular_labels)}."
    else:
        generic_labels = [label for label in (_safe_string(entry.get("activity_name")) for entry in entries) if label]
        message = f"The activities listed are {_render_label_series(generic_labels)}."

    return _lookup_response(message, _source_list_for_entries("page2_activities", entries, "activity_name"))


def _list_test_items(tests: list[dict[str, Any]]) -> ReportChatResponse:
    if not tests:
        return _lookup_response("No tests are listed in the Tests section.", [_build_source("page2_tests")], not_found=True)

    labels: list[str] = []
    for entry in tests:
        test_name = _safe_string(entry.get("test_name")) or "Test"
        score = _safe_string(entry.get("total_score")) or _safe_string(entry.get("percentile")) or _safe_string(entry.get("rank"))
        labels.append(f"{test_name} ({score})" if score else test_name)
    return _lookup_response(
        f"The listed tests are {_render_label_series(labels)}.",
        _source_list_for_entries("page2_tests", tests, "test_name"),
    )


def _list_academic_items(records: list[dict[str, Any]]) -> ReportChatResponse:
    if not records:
        return _lookup_response("No academic records are listed in the Academics section.", [_build_source("page2_academics")], not_found=True)

    labels: list[str] = []
    for entry in records:
        level = _safe_string(entry.get("academic_level")) or "Academic record"
        overall_score = _format_score(entry.get("score_raw"), entry.get("max_score_raw"), entry.get("grading_mode"))
        labels.append(f"{level} ({overall_score})" if overall_score else level)
    return _lookup_response(
        f"The academic records listed are {_render_label_series(labels)}.",
        _source_list_for_entries("page2_academics", records, "academic_level"),
    )


def _list_leadership_items(entries: list[dict[str, Any]]) -> ReportChatResponse:
    if not entries:
        return _lookup_response("No leadership roles are listed in the Leadership section.", [_build_source("page2_leadership")], not_found=True)

    labels = [label for label in (_safe_string(entry.get("position_title")) for entry in entries) if label]
    if not labels:
        return _lookup_response("Leadership details are available in the Leadership section.", [_build_source("page2_leadership")])
    return _lookup_response(
        f"The leadership roles listed are {_render_label_series(labels)}.",
        _source_list_for_entries("page2_leadership", entries, "position_title"),
    )


def _list_essay_items(entries: list[dict[str, Any]]) -> ReportChatResponse:
    if not entries:
        return _lookup_response("No essays are listed in the Writing section.", [_build_source("page3_essays")], not_found=True)

    labels = [label for label in (_safe_string(entry.get("prompt")) for entry in entries) if label]
    if not labels:
        return _lookup_response("Essays are available in the Writing section.", [_build_source("page3_essays")])
    return _lookup_response(f"The essay prompts listed are {_render_label_series(labels)}.", [_build_source("page3_essays")])


def _detect_coverage_mode(question: str, context: dict[str, Any]) -> ReportChatCoverageMode:
    if context.get("response_kind") != "lookup":
        return "domain_summary"

    target = context.get("detected_target")
    normalized = context.get("normalized_question", "")
    tokens = set(context.get("question_tokens", []))
    pages = context.get("pages") or {}

    if target == "activities":
        page2 = pages.get("page2") if isinstance(pages, dict) else {}
        bucket = _detect_activity_bucket(question)
        entries = _activity_entries(page2 if isinstance(page2, dict) else {}, bucket)
        informative = _filter_informative_tokens(tokens, ACTIVITY_DOMAIN_TOKENS)
        if informative and entries:
            matches = _find_activity_match(entries, informative)
            if matches and len(matches) < len(entries):
                return "single_fact"
        return "all_items"

    if target == "leadership":
        informative = _filter_informative_tokens(tokens, LEADERSHIP_DOMAIN_TOKENS)
        return "single_fact" if informative else "all_items"

    if target == "tests":
        informative = _filter_informative_tokens(tokens, TEST_DOMAIN_TOKENS)
        if _contains_score_intent(normalized, tokens) or informative:
            return "single_fact"
        return "all_items"

    if target == "academics":
        page2 = pages.get("page2") if isinstance(pages, dict) else {}
        records = [entry for entry in page2.get("academic_records", []) if isinstance(entry, dict)] if isinstance(page2, dict) else []
        subject_match = any(_find_subject_match(record, tokens) for record in records)
        informative = _filter_informative_tokens(tokens, ACADEMIC_DOMAIN_TOKENS)
        if _extract_academic_level(normalized) or _contains_score_intent(normalized, tokens) or subject_match or informative:
            return "single_fact"
        return "all_items"

    if target == "essays":
        informative = _filter_informative_tokens(tokens, ESSAY_DOMAIN_TOKENS)
        if "prompt" in tokens or informative:
            return "single_fact"
        return "all_items"

    return "single_fact"


def _redirect_summary() -> ReportChatResponse:
    return ReportChatResponse(
        answer_summary="I can summarize specific report areas like academics, activities, writing, focus areas, or interview questions, but not the participant as a whole.",
        response_kind="scope_redirect",
        sources=[],
        not_found=False,
        response_state="clean",
    )


def _not_found_response(message: str) -> ReportChatResponse:
    return ReportChatResponse(
        answer_summary=message,
        response_kind="degraded",
        sources=[],
        not_found=True,
        response_state="clean",
    )


def _lookup_response(
    answer_summary: str,
    sources: list[ReportChatSource],
    *,
    response_kind: ReportChatResponseKind = "lookup",
    not_found: bool = False,
    response_state: str = "clean",
) -> ReportChatResponse:
    return ReportChatResponse(
        answer_summary=answer_summary,
        response_kind=response_kind,
        sources=sources,
        not_found=not_found,
        response_state=response_state,  # type: ignore[arg-type]
    )


def _broader_pointer_answer(context: dict[str, Any], message: str) -> ReportChatResponse:
    section_targets = context.get("section_targets") or []
    if section_targets:
        section_key = section_targets[0]["section_key"]
        return _lookup_response(message, [_build_source(section_key)])
    return _lookup_response(message, [], response_kind="degraded", response_state="degraded")


def _answer_lookup(question: str, context: dict[str, Any]) -> ReportChatResponse:
    normalized = context["normalized_question"]
    tokens = set(context["question_tokens"])
    target = context["detected_target"]
    pages = context["pages"]
    coverage_mode = context.get("coverage_mode", "single_fact")

    if target == "identity":
        page1 = pages.get("page1", {})
        identity = page1.get("identity", {}) if isinstance(page1, dict) else {}
        full_name = _safe_string(identity.get("full_name"))
        preferred_major = _safe_string(identity.get("preferred_major"))
        geo = identity.get("geographic_context") if isinstance(identity, dict) else {}
        location = ", ".join(filter(None, (_safe_string(geo.get("city")), _safe_string(geo.get("state")), _safe_string(geo.get("country"))))) if isinstance(geo, dict) else None

        if "name" in tokens and full_name:
            return _lookup_response(f"The applicant name is {full_name}.", [_build_source("page1_overview")])
        if "major" in tokens and preferred_major:
            return _lookup_response(f"The preferred major is {preferred_major}.", [_build_source("page1_overview")])
        if {"city", "state", "country", "location", "home"} & tokens and location:
            return _lookup_response(f"The report lists the location as {location}.", [_build_source("page1_overview")])
        return _broader_pointer_answer(context, "The relevant background details are in the Overview section.")

    if target == "academics":
        page2 = pages.get("page2", {})
        records = [entry for entry in page2.get("academic_records", []) if isinstance(entry, dict)] if isinstance(page2, dict) else []
        if coverage_mode == "all_items":
            return _list_academic_items(records)
        level = _extract_academic_level(normalized)
        score_intent = _contains_score_intent(normalized, tokens)
        matching_record = next((entry for entry in records if level and _record_matches_level(entry, level)), None)

        if matching_record:
            entity_id = _safe_string(matching_record.get("entity_id"))
            label = _safe_string(matching_record.get("academic_level")) or "Academics"
            subject_match = _find_subject_match(matching_record, tokens)
            if subject_match and score_intent:
                return _lookup_response(
                    f"I found the relevant marks in the {label} academic record.",
                    [_build_source("page2_academics", label=label, entity_id=entity_id)],
                )

            overall_score = _format_score(
                matching_record.get("score_raw"),
                matching_record.get("max_score_raw"),
                matching_record.get("grading_mode"),
            )
            if score_intent and overall_score:
                return _lookup_response(
                    f"The {label} overall score is {overall_score}.",
                    [_build_source("page2_academics", label=label, entity_id=entity_id)],
                )

            return _lookup_response(
                f"The relevant academic details are in the {label} record.",
                [_build_source("page2_academics", label=label, entity_id=entity_id)],
            )

        if len(records) == 1 and score_intent:
            only_record = records[0]
            label = _safe_string(only_record.get("academic_level")) or "Academics"
            overall_score = _format_score(
                only_record.get("score_raw"),
                only_record.get("max_score_raw"),
                only_record.get("grading_mode"),
            )
            if overall_score:
                return _lookup_response(
                    f"The {label} overall score is {overall_score}.",
                    [_build_source("page2_academics", label=label, entity_id=_safe_string(only_record.get("entity_id")))],
                )

        return _broader_pointer_answer(context, "The relevant academic details are in the Academics section.")

    if target == "tests":
        page2 = pages.get("page2", {})
        tests = [entry for entry in page2.get("standardized_tests", []) if isinstance(entry, dict)] if isinstance(page2, dict) else []
        if coverage_mode == "all_items":
            return _list_test_items(tests)
        matched_test = _find_test_match(tests, normalized, tokens)
        if matched_test:
            test_name = _safe_string(matched_test.get("test_name")) or "Test"
            entity_id = _safe_string(matched_test.get("entity_id"))
            score = _safe_string(matched_test.get("total_score")) or _safe_string(matched_test.get("percentile")) or _safe_string(matched_test.get("rank"))
            if score:
                suffix = "score"
                if matched_test.get("percentile"):
                    suffix = "percentile"
                elif matched_test.get("rank"):
                    suffix = "rank"
                return _lookup_response(
                    f"The {test_name} {suffix} is {score}.",
                    [_build_source("page2_tests", label=test_name, entity_id=entity_id)],
                )
            return _lookup_response(
                f"The relevant test details are under {test_name}.",
                [_build_source("page2_tests", label=test_name, entity_id=entity_id)],
            )

        return _broader_pointer_answer(context, "The relevant test details are in the Tests section.")

    if target == "activities":
        page2 = pages.get("page2", {})
        bucket = _detect_activity_bucket(question)
        activities = _activity_entries(page2 if isinstance(page2, dict) else {}, bucket)
        if coverage_mode == "all_items":
            return _list_activity_items(activities, bucket)
        matches = _find_activity_match(activities, tokens)
        if matches:
            activity_name = _safe_string(matches[0].get("activity_name")) or "activity"
            return _lookup_response(
                f"The report includes {activity_name} in the Activities section.",
                [_build_source("page2_activities")],
            )
        if "internship" in tokens:
            return _lookup_response(
                "I did not find a specific internship entry, but the Activities section is the best place to review related experience.",
                [_build_source("page2_activities")],
                not_found=True,
            )
        return _broader_pointer_answer(context, "The relevant activity details are in the Activities section.")

    if target == "leadership":
        page2 = pages.get("page2", {})
        leadership = [entry for entry in page2.get("leadership_roles", []) if isinstance(entry, dict)] if isinstance(page2, dict) else []
        if coverage_mode == "all_items":
            return _list_leadership_items(leadership)
        if leadership:
            title = _safe_string(leadership[0].get("position_title"))
            if title:
                return _lookup_response(
                    f"The report lists {title} in the Leadership section.",
                    [_build_source("page2_leadership")],
                )
        return _broader_pointer_answer(context, "The relevant leadership details are in the Leadership section.")

    if target == "essays":
        page3 = pages.get("page3", {})
        essays = [entry for entry in page3.get("essays", []) if isinstance(entry, dict)] if isinstance(page3, dict) else []
        if coverage_mode == "all_items":
            return _list_essay_items(essays)
        if essays:
            prompt = _safe_string(essays[0].get("prompt"))
            if prompt and "prompt" in tokens:
                return _lookup_response(f"The essay prompt shown is {prompt}.", [_build_source("page3_essays")])
        return _broader_pointer_answer(context, "The relevant writing details are in the Writing section.")

    if target in {"themes", "signals"}:
        page4 = pages.get("page4", {})
        themes = [entry for entry in page4.get("themes", []) if isinstance(entry, dict)] if isinstance(page4, dict) else []
        signals = [entry for entry in page4.get("signals", []) if isinstance(entry, dict)] if isinstance(page4, dict) else []
        if themes:
            theme_title = _safe_string(themes[0].get("title"))
            if theme_title:
                return _lookup_response(f"The main focus area is {theme_title}.", [_build_source("page4_focus_areas")])
        if signals:
            signal_title = _safe_string(signals[0].get("title"))
            if signal_title:
                return _lookup_response(f"The report highlights {signal_title}.", [_build_source("page4_focus_areas")])
        return _broader_pointer_answer(context, "The relevant generated focus areas are in the Focus Areas section.")

    if target == "question_groups":
        page5 = pages.get("page5", {})
        groups = [entry for entry in page5.get("question_groups", []) if isinstance(entry, dict)] if isinstance(page5, dict) else []
        if groups:
            group_title = _safe_string(groups[0].get("group_title"))
            if group_title:
                return _lookup_response(
                    f"The interview prompts are grouped under {group_title}.",
                    [_build_source("page5_question_groups")],
                )
        return _broader_pointer_answer(context, "The relevant interview prompts are in the Questions section.")

    return _lookup_response(
        "I found relevant information in the report, but I cannot safely narrow it further right now.",
        [],
        response_kind="degraded",
        response_state="degraded",
    )


def _summary_sources(context: dict[str, Any]) -> list[ReportChatSource]:
    target = context["detected_target"]
    section_targets = context.get("section_targets") or []

    if target == "essays":
        annotations = context.get("annotations") or {}
        fragments = annotations.get("page_3_fragments") if isinstance(annotations, dict) else None
        if isinstance(fragments, dict):
            built: list[ReportChatSource] = []
            excerpt_index = 1
            for fragment_list in fragments.values():
                if not isinstance(fragment_list, list):
                    continue
                for fragment in fragment_list:
                    if not isinstance(fragment, dict):
                        continue
                    fragment_id = _safe_string(fragment.get("fragment_id"))
                    if fragment_id:
                        built.append(
                            _build_source(
                                "page3_essays",
                                label=f"Essay excerpt {excerpt_index}",
                                fragment_id=fragment_id,
                            )
                        )
                        excerpt_index += 1
                    if len(built) >= 2:
                        return built
            if built:
                return built

    return [_build_source(target_info["section_key"]) for target_info in section_targets[:3]]


def _summary_fallback(context: dict[str, Any]) -> str:
    target = context["detected_target"]
    fallbacks = {
        "academics": "The report contains academic records and performance details.",
        "tests": "The report contains standardized test details.",
        "activities": "The report contains activity and extracurricular information.",
        "leadership": "The report contains leadership information.",
        "essays": "The report contains essay and writing information.",
        "themes": "The report contains generated focus areas.",
        "signals": "The report contains generated focus areas.",
        "question_groups": "The report contains generated interview question areas.",
    }
    return fallbacks.get(target, "The report contains relevant information for that area.")


def _normalize_activity_type_label(value: Any) -> str | None:
    raw = _safe_string(value)
    if not raw:
        return None
    normalized = raw.replace("_", " ").strip().lower()
    if normalized == "co curricular":
        return "Co-curricular"
    return normalized.capitalize()


def _activity_type_bucket(value: Any) -> str | None:
    raw = _safe_string(value)
    if not raw:
        return None
    normalized = raw.replace("_", " ").replace("-", " ").strip().lower()
    if normalized == "co curricular":
        return "co_curricular"
    if normalized == "extracurricular":
        return "extracurricular"
    return normalized


def _duration_years_value(entry: dict[str, Any]) -> str | None:
    duration_years = _safe_string(entry.get("duration_years"))
    if duration_years:
        return duration_years
    return _safe_string(entry.get("duration"))


def _build_activity_summary_context(page2: dict[str, Any]) -> dict[str, Any]:
    def build_collection(collection_name: str) -> list[dict[str, Any]]:
        cleaned_entries: list[dict[str, Any]] = []
        entries = page2.get(collection_name, [])
        if not isinstance(entries, list):
            return cleaned_entries
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            cleaned: dict[str, Any] = {}
            activity_name = _safe_string(entry.get("activity_name"))
            activity_type = _normalize_activity_type_label(entry.get("activity_type"))
            level = _safe_string(entry.get("level"))
            duration_years = _duration_years_value(entry)
            source_note = _safe_string(entry.get("achievement")) or _safe_string(entry.get("description_raw"))
            if activity_name:
                cleaned["name"] = activity_name
            if activity_type:
                cleaned["type_label"] = activity_type
            if level:
                cleaned["level_label"] = level
            if duration_years:
                cleaned["duration_years"] = duration_years
            if source_note:
                cleaned["source_note"] = source_note
            if cleaned:
                cleaned_entries.append(cleaned)
        return cleaned_entries

    return {
        "extracurricular_activities": build_collection("extracurricular_activities"),
        "co_curricular_activities": build_collection("co_curricular_activities"),
    }


def _build_summary_report_context(context: dict[str, Any]) -> dict[str, Any]:
    target = context.get("detected_target")
    pages = context.get("pages")
    if not isinstance(pages, dict):
        return {}
    if target == "activities":
        page2 = pages.get("page2")
        if isinstance(page2, dict):
            return {"page2": _build_activity_summary_context(page2)}
    return pages


def _build_summary_messages(question: str, context: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You summarize a single report domain from a structured application report.\n"
                "Use only the supplied report context.\n"
                "Do not evaluate, rank, judge, or summarize the participant as a whole.\n"
                "Do not invent citations or mention unavailable evidence.\n"
                "Treat duration_years values as counts of years.\n"
                "Use clean, readable product language instead of repeating awkward source field phrasing.\n"
                "For activity summaries, cover both extracurricular and co-curricular entries when both are present.\n"
                "Keep the answer to 2-4 concise sentences.\n"
                "Return plain text only."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": question,
                    "domain": context.get("detected_target"),
                    "selected_sections": context.get("selected_sections"),
                    "report_context": _build_summary_report_context(context),
                }
            ),
        },
    ]


def _answer_domain_summary(question: str, context: dict[str, Any]) -> ReportChatResponse:
    target = context["detected_target"]
    if target not in SUMMARY_ALLOWED_TARGETS:
        return _redirect_summary()

    try:
        response_text = generate(_build_summary_messages(question, context), call_label="report_chat")
        answer_summary = " ".join(response_text.split()).strip()
    except LLMClientError:
        answer_summary = ""

    if not answer_summary:
        return ReportChatResponse(
            answer_summary=_summary_fallback(context),
            response_kind="degraded",
            sources=[],
            not_found=False,
            response_state="degraded",
        )

    return ReportChatResponse(
        answer_summary=answer_summary,
        response_kind="domain_summary",
        sources=_summary_sources(context),
        not_found=False,
        response_state="clean",
    )


def answer_report_question(question: str, context: dict[str, Any]) -> ReportChatResponse:
    if context.get("response_kind") == "scope_redirect":
        return _redirect_summary()

    if context.get("not_found_summary") and not context.get("section_targets"):
        return _not_found_response(str(context["not_found_summary"]))

    if context.get("response_kind") == "lookup":
        return _answer_lookup(question, context)

    response = _answer_domain_summary(question, context)
    logger.info(
        "Report chat completed response_kind=%s shape=%s operation=%s target=%s response_state=%s source_count=%s",
        response.response_kind,
        context.get("question_shape_bucket"),
        context.get("detected_operation"),
        context.get("detected_target"),
        response.response_state,
        len(response.sources),
    )
    return response
