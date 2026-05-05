from __future__ import annotations

from copy import deepcopy
from typing import Any
import uuid


QUESTION_STATUS_VALUES = {"unasked", "satisfactory", "mixed", "unsatisfactory"}
QUESTION_SOURCE_VALUES = {"generated", "custom"}
WORKSPACE_STATUS_VALUES = {"draft", "launched", "postgame", "completed"}


def _normalize_follow_up(
    raw_follow_up: Any,
    *,
    parent_question_id: str,
    follow_up_index: int,
) -> dict[str, Any] | None:
    if not isinstance(raw_follow_up, dict):
        return None

    follow_up_text = str(raw_follow_up.get("text") or raw_follow_up.get("question") or "").strip()
    if not follow_up_text:
        return None

    raw_status = str(raw_follow_up.get("status") or "unasked").strip()
    try:
        order = int(raw_follow_up.get("order") if raw_follow_up.get("order") is not None else follow_up_index)
    except (TypeError, ValueError):
        order = follow_up_index

    return {
        "id": str(raw_follow_up.get("id") or f"{parent_question_id}-f{follow_up_index + 1}"),
        "text": follow_up_text,
        "source": "custom",
        "status": raw_status if raw_status in QUESTION_STATUS_VALUES else "unasked",
        "note": str(raw_follow_up.get("note") or "").strip(),
        "order": order,
    }


def _normalize_question(
    raw_question: Any,
    *,
    theme_id: str,
    question_index: int,
    default_source: str,
) -> dict[str, Any] | None:
    if isinstance(raw_question, str):
        question_text = raw_question.strip()
        if not question_text:
            return None
        return {
            "id": f"{theme_id}-q{question_index + 1}",
            "text": question_text,
            "source": default_source,
            "status": "unasked",
            "note": "",
            "order": question_index,
            "follow_ups": [],
        }

    if not isinstance(raw_question, dict):
        return None

    question_text = str(
        raw_question.get("question")
        or raw_question.get("text")
        or raw_question.get("sample_question")
        or raw_question.get("hook")
        or ""
    ).strip()
    if not question_text:
        return None

    raw_status = str(raw_question.get("status") or "unasked").strip()
    raw_source = str(raw_question.get("source") or default_source).strip()
    try:
        order = int(raw_question.get("order") if raw_question.get("order") is not None else question_index)
    except (TypeError, ValueError):
        order = question_index

    question_id = str(
        raw_question.get("id")
        or raw_question.get("question_id")
        or raw_question.get("opening_id")
        or f"{theme_id}-q{question_index + 1}"
    )
    follow_ups = []
    for follow_up_index, raw_follow_up in enumerate(raw_question.get("follow_ups") or raw_question.get("followUps") or []):
        follow_up = _normalize_follow_up(
            raw_follow_up,
            parent_question_id=question_id,
            follow_up_index=follow_up_index,
        )
        if follow_up is not None:
            follow_ups.append(follow_up)

    return {
        "id": question_id,
        "text": question_text,
        "source": raw_source if raw_source in QUESTION_SOURCE_VALUES else default_source,
        "status": raw_status if raw_status in QUESTION_STATUS_VALUES else "unasked",
        "note": str(raw_question.get("note") or "").strip(),
        "order": order,
        "follow_ups": follow_ups,
    }


def build_workspace_seed(final_report_content: dict[str, Any]) -> dict[str, Any]:
    page_4 = final_report_content.get("page_4_focus_areas") or {}
    page_5 = final_report_content.get("page_5_question_groups") or {}
    focus_areas = page_4.get("focus_areas") or []
    question_groups = page_5.get("question_groups") or []
    question_group_by_focus_area = {
        str(group.get("focus_area_id")): group
        for group in question_groups
        if isinstance(group, dict) and group.get("focus_area_id")
    }

    theme_cards: list[dict[str, Any]] = []
    for index, focus_area in enumerate(focus_areas):
        if not isinstance(focus_area, dict):
            continue
        theme_id = str(focus_area.get("focus_area_id") or f"focus-area-{index + 1}")
        group = question_group_by_focus_area.get(theme_id, {})
        group_title = str(
            group.get("group_label")
            or focus_area.get("title")
            or f"Focus Area {index + 1}"
        ).strip()
        line_of_inquiry = str(
            group.get("line_of_inquiry")
            or focus_area.get("interview_direction")
            or ""
        ).strip()
        questions = [
            _normalize_question(
                raw_question,
                theme_id=theme_id,
                question_index=question_index,
                default_source="generated",
            )
            for question_index, raw_question in enumerate(group.get("questions") or [])
        ]
        theme_cards.append(
            {
                "id": theme_id,
                "source": "generated",
                "title": str(focus_area.get("title") or f"Focus Area {index + 1}").strip(),
                "interview_direction": line_of_inquiry,
                "territory": str(focus_area.get("territory") or "").strip(),
                "what_makes_it_worth_time": str(focus_area.get("what_makes_it_worth_time") or "").strip(),
                "question_group_title": group_title or "Question group",
                "questions": [question for question in questions if question is not None],
            }
        )

    return {
        "themes": theme_cards,
        "final_summary": "",
    }


def normalize_workspace_content(content: dict[str, Any]) -> dict[str, Any]:
    themes_input = content.get("themes") if isinstance(content, dict) else []
    normalized_themes: list[dict[str, Any]] = []

    if isinstance(themes_input, list):
        for index, theme in enumerate(themes_input):
            if not isinstance(theme, dict):
                continue

            raw_id = theme.get("id")
            source = str(theme.get("source") or "custom")
            theme_id = str(raw_id or f"custom-{index + 1}-{uuid.uuid4().hex[:8]}")
            normalized_questions = []
            for question_index, raw_question in enumerate(theme.get("questions") or []):
                question = _normalize_question(
                    raw_question,
                    theme_id=theme_id,
                    question_index=question_index,
                    default_source="custom" if source != "generated" else "generated",
                )
                if question is not None:
                    normalized_questions.append(question)

            normalized_themes.append(
                {
                    "id": theme_id,
                    "source": source if source in {"generated", "custom"} else "custom",
                    "title": str(theme.get("title") or "Untitled theme").strip(),
                    "interview_direction": str(
                        theme.get("interview_direction")
                        or theme.get("line_of_inquiry")
                        or ""
                    ).strip(),
                    "territory": str(theme.get("territory") or "").strip(),
                    "what_makes_it_worth_time": str(theme.get("what_makes_it_worth_time") or "").strip(),
                    "question_group_title": str(
                        theme.get("question_group_title")
                        or theme.get("group_label")
                        or "Question group"
                    ).strip(),
                    "questions": normalized_questions,
                }
            )

    return {
        "themes": normalized_themes,
        "final_summary": str(content.get("final_summary") or content.get("postgame_summary") or "").strip()
        if isinstance(content, dict)
        else "",
    }


def clone_workspace_content(content: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(normalize_workspace_content(content))
