from __future__ import annotations

from copy import deepcopy
from typing import Any
import uuid


QUESTION_STATUS_VALUES = {"unasked", "satisfactory", "mixed", "unsatisfactory"}
QUESTION_SOURCE_VALUES = {"generated", "custom"}
WORKSPACE_STATUS_VALUES = {"draft", "launched", "postgame", "completed"}


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
        }

    if not isinstance(raw_question, dict):
        return None

    question_text = str(raw_question.get("text") or raw_question.get("question") or "").strip()
    if not question_text:
        return None

    raw_status = str(raw_question.get("status") or "unasked").strip()
    raw_source = str(raw_question.get("source") or default_source).strip()
    try:
        order = int(raw_question.get("order") if raw_question.get("order") is not None else question_index)
    except (TypeError, ValueError):
        order = question_index
    return {
        "id": str(raw_question.get("id") or f"{theme_id}-q{question_index + 1}"),
        "text": question_text,
        "source": raw_source if raw_source in QUESTION_SOURCE_VALUES else default_source,
        "status": raw_status if raw_status in QUESTION_STATUS_VALUES else "unasked",
        "note": str(raw_question.get("note") or "").strip(),
        "order": order,
    }


def build_workspace_seed(final_report_content: dict[str, Any]) -> dict[str, Any]:
    page_4 = final_report_content.get("page_4_focus_areas") or {}
    page_5 = final_report_content.get("page_5_question_groups") or {}
    themes = page_4.get("themes") or []
    question_groups = page_5.get("question_groups") or []
    question_group_by_theme = {
        str(group.get("theme_id")): group
        for group in question_groups
        if isinstance(group, dict) and group.get("theme_id")
    }

    theme_cards: list[dict[str, Any]] = []
    for index, theme in enumerate(themes):
        if not isinstance(theme, dict):
            continue
        theme_id = str(theme.get("theme_id") or f"theme-{index + 1}")
        group = question_group_by_theme.get(theme_id, {})
        theme_cards.append(
            {
                "id": theme_id,
                "source": "generated",
                "title": str(theme.get("title") or f"Theme {index + 1}"),
                "unifying_axis": str(theme.get("unifying_axis") or ""),
                "interview_direction": str(theme.get("interview_direction") or ""),
                "question_group_title": str(group.get("group_title") or theme.get("title") or f"Theme {index + 1}"),
                "questions": [
                    _normalize_question(
                        question,
                        theme_id=theme_id,
                        question_index=question_index,
                        default_source="generated",
                    )
                    for question_index, question in enumerate(group.get("questions") or [])
                ],
            }
        )

    return {
        "themes": [
            {
                **theme,
                "questions": [question for question in theme["questions"] if question is not None],
            }
            for theme in theme_cards
        ],
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
                    "unifying_axis": str(theme.get("unifying_axis") or "").strip(),
                    "interview_direction": str(theme.get("interview_direction") or "").strip(),
                    "question_group_title": str(theme.get("question_group_title") or "Question group").strip(),
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
