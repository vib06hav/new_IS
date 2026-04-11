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


def build_report_chat_context(
    review_package_pages: dict[str, Any],
    final_report_content: Optional[dict[str, Any]],
) -> dict[str, Any]:
    context: dict[str, Any] = {
        "source_scope": "pages_1_3",
        "pages": {
            "page1": review_package_pages.get("page_1_background_profile", {}),
            "page2": review_package_pages.get("page_2_academic_and_engagement", {}),
            "page3": review_package_pages.get("page_3_essays", {}),
        },
        "section_targets": [
            {
                "section_key": section_key,
                "target_tab": target["target_tab"],
                "anchor_id": target["anchor_id"],
                "page_label": target["page_label"],
                "section_label": target["section_label"],
            }
            for section_key, target in REPORT_CHAT_SECTION_TARGETS.items()
        ],
    }

    if final_report_content:
        context["source_scope"] = "pages_1_5"
        context["pages"]["page4"] = final_report_content.get("page_4_focus_areas", {})
        context["pages"]["page5"] = final_report_content.get("page_5_question_groups", {})

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
