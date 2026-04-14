import json
from typing import Any, Optional

from app.api.schemas import ReportChatResponse
from app.llm.client import LLMClientError, generate


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


def _question_sections(question: str, has_final_report: bool) -> list[str]:
    lowered = question.lower()
    matched: list[str] = []
    rules = [
        ("page1_overview", ("name", "major", "background", "profile", "family", "home", "city", "state", "country", "identity")),
        ("page2_academics", ("academic", "academics", "school", "grades", "gpa", "board", "class 10", "class 12", "marks", "score")),
        ("page2_tests", ("sat", "act", "ielts", "toefl", "test", "tests", "standardized")),
        ("page2_activities", ("activity", "activities", "club", "competition", "extracurricular", "co-curricular", "sports", "robotics")),
        ("page2_leadership", ("leadership", "captain", "president", "head", "leader", "role")),
        ("page3_essays", ("essay", "essays", "writing", "prompt", "why this major", "statement")),
        ("page4_focus_areas", ("focus area", "focus areas", "theme", "themes", "signal", "signals", "page 4")),
        ("page5_question_groups", ("question group", "question groups", "interview question", "interview questions", "questions", "page 5")),
    ]
    for section_key, keywords in rules:
        if section_key in {"page4_focus_areas", "page5_question_groups"} and not has_final_report:
            continue
        if any(keyword in lowered for keyword in keywords):
            matched.append(section_key)

    if matched:
        return matched

    fallback = ["page1_overview", "page2_academics", "page2_tests", "page2_activities", "page2_leadership", "page3_essays"]
    if has_final_report and any(keyword in lowered for keyword in ("interview", "final report", "generated report")):
        fallback.extend(["page4_focus_areas", "page5_question_groups"])
    return fallback


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
    selected_sections = _question_sections(question, has_final_report=bool(final_report_content))
    pages = _build_selected_pages(selected_sections, review_package_pages, final_report_content)
    context: dict[str, Any] = {
        "source_scope": "pages_1_5" if final_report_content else "pages_1_3",
        "selected_sections": selected_sections,
        "pages": pages,
        "section_targets": [
            {
                "section_key": section_key,
                "target_tab": target["target_tab"],
                "anchor_id": target["anchor_id"],
                "page_label": target["page_label"],
                "section_label": target["section_label"],
            }
            for section_key, target in REPORT_CHAT_SECTION_TARGETS.items()
            if section_key in selected_sections
        ],
    }

    return context


def answer_report_question(question: str, context: dict[str, Any]) -> ReportChatResponse:
    messages = [
        {
            "role": "system",
            "content": (
                "You answer one-shot factual questions from a structured application report.\n"
                "Use only the supplied report context.\n"
                "Do not infer beyond direct evidence.\n"
                "Do not use external knowledge.\n"
                "Return JSON only with this shape: "
                '{"answer_summary":"string","results":[{"label":"string","value":"string","target_tab":"page1|page2|page3|page4|page5","section_key":"page1_overview|page2_academics|page2_tests|page2_activities|page2_leadership|page3_essays|page4_focus_areas|page5_question_groups","anchor_id":"string"}],"not_found":boolean}.\n'
                "If the answer is absent or uncertain, return not_found=true and results=[].\n"
                "Use only section targets listed in the provided context.\n"
                "Keep answer_summary concise and factual."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"question": question, "report_context": context}),
        },
    ]

    try:
        response_text = generate(messages, call_label="report_chat")
    except LLMClientError as exc:
        raise ReportChatError("Report assistant is temporarily unavailable.") from exc

    try:
        parsed = ReportChatResponse.model_validate(json.loads(response_text))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        raise ReportChatError("Report assistant returned an invalid response.") from exc

    if parsed.not_found or not parsed.results:
        return ReportChatResponse(
            answer_summary=parsed.answer_summary or "I could not find that in the current report.",
            results=[],
            not_found=True,
        )

    return parsed
