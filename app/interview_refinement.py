from __future__ import annotations

from typing import Literal

from app.api.schemas import InterviewWorkspaceContent
from app.config import settings
from app.llm.client import LLMClientError, generate


InterviewRefinementMode = Literal["question_note", "follow_up_note", "final_summary"]


class InterviewRefinementError(Exception):
    """Raised when interviewer refinement input is invalid or cannot be completed."""


def validate_refinement_text(text: str) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        raise InterviewRefinementError("Text is required before refinement can run.")
    if len(cleaned) > settings.INTERVIEW_REFINEMENT_MAX_TEXT_CHARS:
        raise InterviewRefinementError(
            f"Text exceeds the {settings.INTERVIEW_REFINEMENT_MAX_TEXT_CHARS} character limit for refinement."
        )
    return cleaned


def validate_refinement_instruction(instruction: str | None) -> str:
    cleaned = str(instruction or "").strip()
    if len(cleaned) > settings.INTERVIEW_REFINEMENT_MAX_INSTRUCTION_CHARS:
        raise InterviewRefinementError(
            f"Instruction exceeds the {settings.INTERVIEW_REFINEMENT_MAX_INSTRUCTION_CHARS} character limit."
        )
    return cleaned


def refine_interview_text(
    *,
    mode: InterviewRefinementMode,
    text: str,
    instruction: str,
    content: InterviewWorkspaceContent,
    theme_id: str | None = None,
    question_id: str | None = None,
    follow_up_id: str | None = None,
) -> str:
    validated_text = validate_refinement_text(text)
    validated_instruction = validate_refinement_instruction(instruction)
    context = _build_mode_context(
        mode=mode,
        content=content,
        theme_id=theme_id,
        question_id=question_id,
        follow_up_id=follow_up_id,
    )

    messages = _build_refinement_messages(
        mode=mode,
        text=validated_text,
        instruction=validated_instruction,
        context=context,
    )
    refined = generate(messages, call_label="interview_refinement").strip()
    if not refined:
        raise InterviewRefinementError("Refinement returned an empty response.")
    return refined


def _build_mode_context(
    *,
    mode: InterviewRefinementMode,
    content: InterviewWorkspaceContent,
    theme_id: str | None,
    question_id: str | None,
    follow_up_id: str | None,
) -> str:
    if mode == "question_note":
      return _build_question_note_context(content, theme_id=theme_id, question_id=question_id)
    if mode == "follow_up_note":
      return _build_follow_up_context(
          content,
          theme_id=theme_id,
          question_id=question_id,
          follow_up_id=follow_up_id,
      )
    if mode == "final_summary":
      return _build_final_summary_context(content)
    raise InterviewRefinementError("Unsupported refinement mode.")


def _build_question_note_context(
    content: InterviewWorkspaceContent,
    *,
    theme_id: str | None,
    question_id: str | None,
) -> str:
    if not theme_id or not question_id:
        raise InterviewRefinementError("Theme and question identifiers are required for question note refinement.")

    for theme in content.themes:
        if theme.id != theme_id:
            continue
        for question in theme.questions:
            if question.id == question_id:
                return "\n".join(
                    [
                        f"Focus area: {theme.title or theme.question_group_title}",
                        f"Group label: {theme.question_group_title}",
                        f"Line of inquiry: {theme.interview_direction}",
                        f"Question: {question.text}",
                        f"Question status: {question.status}",
                    ]
                )

    raise InterviewRefinementError("The target question could not be found for refinement.")


def _build_follow_up_context(
    content: InterviewWorkspaceContent,
    *,
    theme_id: str | None,
    question_id: str | None,
    follow_up_id: str | None,
) -> str:
    if not theme_id or not question_id or not follow_up_id:
        raise InterviewRefinementError("Theme, question, and follow-up identifiers are required for follow-up refinement.")

    for theme in content.themes:
        if theme.id != theme_id:
            continue
        for question in theme.questions:
            if question.id != question_id:
                continue
            for follow_up in question.follow_ups:
                if follow_up.id == follow_up_id:
                    return "\n".join(
                        [
                            f"Focus area: {theme.title or theme.question_group_title}",
                            f"Group label: {theme.question_group_title}",
                            f"Line of inquiry: {theme.interview_direction}",
                            f"Question: {question.text}",
                            f"Follow-up status: {follow_up.status}",
                            f"Follow-up text: {follow_up.text}",
                        ]
                    )

    raise InterviewRefinementError("The target follow-up could not be found for refinement.")


def _build_final_summary_context(content: InterviewWorkspaceContent) -> str:
    lines = []
    for theme_index, theme in enumerate(content.themes, start=1):
        lines.append(f"Focus Area {theme_index}: {theme.title or theme.question_group_title}")
        if theme.question_group_title:
            lines.append(f"Group label: {theme.question_group_title}")
        if theme.interview_direction:
            lines.append(f"Line of inquiry: {theme.interview_direction}")
        for question_index, question in enumerate(sorted(theme.questions, key=lambda item: item.order), start=1):
            lines.append(f"- Question {question_index} [{question.status}]: {question.text}")
            if question.note:
                lines.append(f"  Note: {question.note}")
            for follow_up_index, follow_up in enumerate(sorted(question.follow_ups, key=lambda item: item.order), start=1):
                lines.append(f"  Follow-up {follow_up_index} [{follow_up.status}]: {follow_up.text}")
                if follow_up.note:
                    lines.append(f"    Note: {follow_up.note}")
    return "\n".join(lines) if lines else "No interview details were recorded."


def _build_refinement_messages(
    *,
    mode: InterviewRefinementMode,
    text: str,
    instruction: str,
    context: str,
) -> list[dict[str, str]]:
    mode_label = {
        "question_note": "question note",
        "follow_up_note": "follow-up note",
        "final_summary": "final interview summary",
    }[mode]
    system_prompt = (
        "You are refining interviewer-authored admissions interview notes. "
        "Your job is to improve clarity, structure, and phrasing while staying grounded in the text and context provided. "
        "Do not invent evidence, claims, judgments, or specifics not supported by the source text and context. "
        "You may modestly expand emphasis only when the instruction explicitly asks for it. "
        "Return only the refined text, with no preamble."
    )
    instruction_line = instruction if instruction else "No extra instruction was provided. Focus on clarity and structure only."
    user_prompt = (
        f"Refine this {mode_label}.\n\n"
        f"Context:\n{context}\n\n"
        f"Original text:\n{text}\n\n"
        f"Instruction:\n{instruction_line}\n\n"
        "Keep the meaning grounded in the original. Use paragraphs or bullets only if they improve readability."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
