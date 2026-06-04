from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    PrebuildFeedbackState,
    PrebuildQuestionThreadSummary,
    PrebuildQuestionVersionSummary,
    PrebuildThemeFeedbackSummary,
)
from app.config import settings
from app.llm.client import LLMClientError, generate
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.final_report import FinalReport
from app.models.interview_workspace import InterviewWorkspace
from app.models.question_generated_version import QuestionGeneratedVersion
from app.models.question_generation_thread import QuestionGenerationThread
from app.models.question_version_rating import QuestionVersionRating
from app.models.theme_rating import ThemeRating
from app.models.user import User
from app.models.vector_corpus_document import VectorCorpusDocument


VISIBLE_VERSION_LIMIT = 5
QUESTION_REGEN_MAX_OUTPUT_CHARS = 1200
TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}")


@dataclass(frozen=True)
class PrebuildPermissions:
    locked: bool
    can_rate_themes: bool
    can_manage_questions: bool
    surface_phase: str | None


def get_prebuild_permissions(
    *,
    application: Application,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
) -> PrebuildPermissions:
    locked = workspace is not None
    if locked:
        return PrebuildPermissions(locked=True, can_rate_themes=False, can_manage_questions=False, surface_phase=None)

    if current_user.role == "admin":
        if assignment is not None:
            return PrebuildPermissions(locked=False, can_rate_themes=False, can_manage_questions=False, surface_phase=None)
        return PrebuildPermissions(
            locked=False,
            can_rate_themes=True,
            can_manage_questions=True,
            surface_phase="pre_assignment",
        )

    if current_user.role == "interviewer" and assignment is not None and assignment.interviewer_id == current_user.id:
        return PrebuildPermissions(
            locked=False,
            can_rate_themes=True,
            can_manage_questions=True,
            surface_phase="post_assignment_prebuild",
        )

    return PrebuildPermissions(locked=False, can_rate_themes=False, can_manage_questions=False, surface_phase=None)


def build_prebuild_feedback_state(
    *,
    db: Session,
    application: Application,
    final_report: FinalReport | None,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
) -> PrebuildFeedbackState | None:
    if not final_report or not isinstance(final_report.content, dict):
        return None

    permissions = get_prebuild_permissions(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
    )
    themes = _extract_focus_areas(final_report.content)
    theme_feedback = _build_theme_feedback(
        db=db,
        application_id=application.id,
        themes=themes,
        current_user=current_user,
    )
    question_threads = _build_question_thread_summaries(
        db=db,
        application_id=application.id,
        current_user=current_user,
    )
    return PrebuildFeedbackState(
        application_id=application.id,
        prebuild_generation_locked=permissions.locked,
        can_rate_themes=permissions.can_rate_themes,
        can_manage_questions=permissions.can_manage_questions,
        theme_feedback=theme_feedback,
        question_threads=question_threads,
    )


def ensure_question_threads_for_application(
    *,
    db: Session,
    application: Application,
    final_report: FinalReport,
) -> bool:
    if not isinstance(final_report.content, dict):
        return False

    changed = False
    focus_areas = {
        str(item.get("focus_area_id")): item
        for item in _extract_focus_areas(final_report.content)
        if isinstance(item, dict) and item.get("focus_area_id")
    }
    for group in _extract_question_groups(final_report.content):
        if not isinstance(group, dict):
            continue
        focus_area_id = str(group.get("focus_area_id") or "")
        if not focus_area_id:
            continue
        focus_area = focus_areas.get(focus_area_id, {})
        for raw_question in group.get("questions") or []:
            if not isinstance(raw_question, dict):
                continue
            base_question_id = str(raw_question.get("question_id") or "").strip()
            question_text = str(raw_question.get("question") or "").strip()
            if not base_question_id or not question_text:
                continue

            thread = (
                db.query(QuestionGenerationThread)
                .filter(
                    QuestionGenerationThread.application_id == application.id,
                    QuestionGenerationThread.focus_area_id == focus_area_id,
                    QuestionGenerationThread.base_question_id == base_question_id,
                )
                .first()
            )
            if thread is None:
                question_role = _derive_question_role(
                    focus_area_title=str(focus_area.get("title") or ""),
                    line_of_inquiry=str(group.get("line_of_inquiry") or focus_area.get("interview_direction") or ""),
                    question_text=question_text,
                    framing_note=str(raw_question.get("framing_note") or ""),
                    explicit_question_role=str(raw_question.get("question_role") or ""),
                )
                thread = QuestionGenerationThread(
                    application_id=application.id,
                    focus_area_id=focus_area_id,
                    base_question_id=base_question_id,
                    question_role=question_role,
                    question_group_label_snapshot=str(group.get("group_label") or ""),
                    theme_title_snapshot=str(focus_area.get("title") or ""),
                    theme_direction_snapshot=str(group.get("line_of_inquiry") or focus_area.get("interview_direction") or ""),
                )
                db.add(thread)
                db.flush()
                changed = True
            elif not str(thread.question_role or "").strip():
                thread.question_role = _derive_question_role(
                    focus_area_title=str(focus_area.get("title") or ""),
                    line_of_inquiry=str(group.get("line_of_inquiry") or focus_area.get("interview_direction") or ""),
                    question_text=question_text,
                    framing_note=str(raw_question.get("framing_note") or ""),
                    explicit_question_role=str(raw_question.get("question_role") or ""),
                )
                changed = True

            existing_versions = (
                db.query(QuestionGeneratedVersion)
                .filter(QuestionGeneratedVersion.thread_id == thread.id)
                .order_by(QuestionGeneratedVersion.version_index.asc())
                .all()
            )
            if not existing_versions:
                version = QuestionGeneratedVersion(
                    thread_id=thread.id,
                    application_id=application.id,
                    focus_area_id=focus_area_id,
                    base_question_id=base_question_id,
                    version_index=1,
                    question_text=question_text,
                    why_this=_normalize_optional_why_this(raw_question.get("framing_note")),
                    generation_source="system_initial",
                    generated_by_user_id=None,
                    parent_version_id=None,
                    is_active=True,
                    theme_title_snapshot=thread.theme_title_snapshot,
                    theme_direction_snapshot=thread.theme_direction_snapshot,
                    question_group_label_snapshot=thread.question_group_label_snapshot,
                    application_context_snapshot=_build_application_snapshot(final_report.content),
                    retrieval_context_snapshot={"seeded": True, "retrieved_examples": []},
                )
                db.add(version)
                db.flush()
                thread.current_active_version_id = version.id
                _upsert_question_vector_document(db=db, version=version)
                changed = True
            else:
                active_version = next((item for item in existing_versions if item.is_active), None) or existing_versions[-1]
                if not active_version.is_active:
                    active_version.is_active = True
                    changed = True
                if thread.current_active_version_id != active_version.id:
                    changed = True
                thread.current_active_version_id = active_version.id

            _upsert_theme_vector_document(
                db=db,
                application_id=application.id,
                focus_area=focus_area,
                theme_direction=str(group.get("line_of_inquiry") or focus_area.get("interview_direction") or ""),
            )
    db.flush()
    return changed


def upsert_theme_rating(
    *,
    db: Session,
    application: Application,
    final_report: FinalReport | None,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
    focus_area_id: str,
    rating: int,
) -> ThemeRating:
    _validate_rating_value(rating)
    _require_prebuild_role_access(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
        require_question_management=False,
    )
    rating_record = (
        db.query(ThemeRating)
        .filter(
            ThemeRating.application_id == application.id,
            ThemeRating.focus_area_id == focus_area_id,
            ThemeRating.rated_by_user_id == current_user.id,
        )
        .first()
    )
    surface_phase = "pre_assignment" if current_user.role == "admin" else "post_assignment_prebuild"
    if rating_record is None:
        rating_record = ThemeRating(
            application_id=application.id,
            focus_area_id=focus_area_id,
            surface_role=current_user.role,
            surface_phase=surface_phase,
            rated_by_user_id=current_user.id,
            rating=rating,
        )
        db.add(rating_record)
    else:
        rating_record.rating = rating
        rating_record.surface_role = current_user.role
        rating_record.surface_phase = surface_phase

    if final_report and isinstance(final_report.content, dict):
        focus_area = next(
            (
                item
                for item in _extract_focus_areas(final_report.content)
                if isinstance(item, dict) and str(item.get("focus_area_id")) == focus_area_id
            ),
            None,
        )
        if isinstance(focus_area, dict):
            matching_group = next(
                (
                    group
                    for group in _extract_question_groups(final_report.content)
                    if isinstance(group, dict) and str(group.get("focus_area_id")) == focus_area_id
                ),
                None,
            )
            _upsert_theme_vector_document(
                db=db,
                application_id=application.id,
                focus_area=focus_area,
                theme_direction=str((matching_group or {}).get("line_of_inquiry") or focus_area.get("interview_direction") or ""),
            )
    db.flush()
    return rating_record


def upsert_question_version_rating(
    *,
    db: Session,
    application: Application,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
    thread_id: UUID,
    version_id: UUID,
    rating: int,
) -> QuestionVersionRating:
    _validate_rating_value(rating)
    _require_prebuild_role_access(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
        require_question_management=True,
    )
    version = _get_thread_version_or_404(db=db, application_id=application.id, thread_id=thread_id, version_id=version_id)
    rating_record = (
        db.query(QuestionVersionRating)
        .filter(
            QuestionVersionRating.question_version_id == version.id,
            QuestionVersionRating.rated_by_user_id == current_user.id,
        )
        .first()
    )
    surface_phase = "pre_assignment" if current_user.role == "admin" else "post_assignment_prebuild"
    if rating_record is None:
        rating_record = QuestionVersionRating(
            question_version_id=version.id,
            application_id=application.id,
            rated_by_user_id=current_user.id,
            surface_role=current_user.role,
            surface_phase=surface_phase,
            rating=rating,
        )
        db.add(rating_record)
    else:
        rating_record.rating = rating
        rating_record.surface_role = current_user.role
        rating_record.surface_phase = surface_phase
    db.flush()
    _upsert_question_vector_document(db=db, version=version)
    return rating_record


def activate_question_version(
    *,
    db: Session,
    application: Application,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
    thread_id: UUID,
    version_id: UUID,
) -> QuestionGenerationThread:
    _require_prebuild_role_access(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
        require_question_management=True,
    )
    thread = _get_thread_or_404(db=db, application_id=application.id, thread_id=thread_id)
    target_version = _get_thread_version_or_404(db=db, application_id=application.id, thread_id=thread_id, version_id=version_id)
    versions = (
        db.query(QuestionGeneratedVersion)
        .filter(QuestionGeneratedVersion.thread_id == thread.id)
        .all()
    )
    for version in versions:
        version.is_active = version.id == target_version.id
    thread.current_active_version_id = target_version.id
    db.flush()
    return thread


def regenerate_question(
    *,
    db: Session,
    application: Application,
    final_report: FinalReport,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
    thread_id: UUID,
) -> QuestionGenerationThread:
    _require_prebuild_role_access(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
        require_question_management=True,
    )
    thread = _get_thread_or_404(db=db, application_id=application.id, thread_id=thread_id)
    active_version = _get_active_version_for_thread(db=db, thread=thread)
    retrieved_examples = _retrieve_similar_question_examples(
        db=db,
        application_id=application.id,
        focus_area_id=thread.focus_area_id,
        theme_title=thread.theme_title_snapshot or "",
        theme_direction=thread.theme_direction_snapshot or "",
        question_text=active_version.question_text,
    )
    application_context_snapshot = _build_application_snapshot(final_report.content)
    prompt_messages = _build_question_regeneration_messages(
        application_snapshot=application_context_snapshot,
        thread=thread,
        current_question=active_version.question_text,
        current_why_this=active_version.why_this or "",
        retrieved_examples=retrieved_examples,
    )
    try:
        regenerated_payload = _normalize_generated_question_payload(
            generate(prompt_messages, call_label="question_regeneration")
        )
    except LLMClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    active_version.is_active = False
    next_version_index = (
        db.query(QuestionGeneratedVersion)
        .filter(QuestionGeneratedVersion.thread_id == thread.id)
        .count()
        + 1
    )
    new_version = QuestionGeneratedVersion(
        thread_id=thread.id,
        application_id=application.id,
        focus_area_id=thread.focus_area_id,
        base_question_id=thread.base_question_id,
        version_index=next_version_index,
        question_text=regenerated_payload["question_text"],
        why_this=regenerated_payload["why_this"],
        generation_source=f"{current_user.role}_regenerate",
        generated_by_user_id=current_user.id,
        parent_version_id=active_version.id,
        is_active=True,
        theme_title_snapshot=thread.theme_title_snapshot,
        theme_direction_snapshot=thread.theme_direction_snapshot,
        question_group_label_snapshot=thread.question_group_label_snapshot,
        application_context_snapshot=application_context_snapshot,
        retrieval_context_snapshot={"retrieved_examples": retrieved_examples},
    )
    db.add(new_version)
    db.flush()
    thread.current_active_version_id = new_version.id
    _upsert_question_vector_document(db=db, version=new_version)
    return thread


def _build_theme_feedback(
    *,
    db: Session,
    application_id: UUID,
    themes: list[dict[str, Any]],
    current_user: User,
) -> list[PrebuildThemeFeedbackSummary]:
    rating_map = {
        item.focus_area_id: item.rating
        for item in (
            db.query(ThemeRating)
            .filter(ThemeRating.application_id == application_id, ThemeRating.rated_by_user_id == current_user.id)
            .all()
        )
    }
    return [
        PrebuildThemeFeedbackSummary(
            focus_area_id=str(theme.get("focus_area_id") or ""),
            title=str(theme.get("title") or ""),
            my_rating=rating_map.get(str(theme.get("focus_area_id") or "")),
        )
        for theme in themes
        if theme.get("focus_area_id")
    ]


def _build_question_thread_summaries(
    *,
    db: Session,
    application_id: UUID,
    current_user: User,
) -> list[PrebuildQuestionThreadSummary]:
    threads = (
        db.query(QuestionGenerationThread)
        .filter(QuestionGenerationThread.application_id == application_id)
        .order_by(QuestionGenerationThread.created_at.asc())
        .all()
    )
    thread_ids = [thread.id for thread in threads]
    versions = (
        db.query(QuestionGeneratedVersion)
        .filter(QuestionGeneratedVersion.thread_id.in_(thread_ids))
        .order_by(QuestionGeneratedVersion.version_index.asc())
        .all()
        if thread_ids
        else []
    )
    ratings = (
        db.query(QuestionVersionRating)
        .filter(
            QuestionVersionRating.application_id == application_id,
            QuestionVersionRating.rated_by_user_id == current_user.id,
        )
        .all()
    )
    rating_map = {item.question_version_id: item.rating for item in ratings}
    versions_by_thread: dict[UUID, list[QuestionGeneratedVersion]] = {}
    for version in versions:
        versions_by_thread.setdefault(version.thread_id, []).append(version)

    summaries: list[PrebuildQuestionThreadSummary] = []
    for thread in threads:
        thread_versions = versions_by_thread.get(thread.id, [])
        active_version = next((item for item in thread_versions if item.id == thread.current_active_version_id), None)
        if active_version is None and thread_versions:
            active_version = next((item for item in thread_versions if item.is_active), None) or thread_versions[-1]
        recent_versions = thread_versions[-VISIBLE_VERSION_LIMIT:]
        if active_version is not None and active_version not in recent_versions:
            recent_versions = [*recent_versions[1:], active_version] if recent_versions else [active_version]
            recent_versions.sort(key=lambda item: item.version_index)
        recent_summaries = [
            PrebuildQuestionVersionSummary(
                id=version.id,
                version_index=version.version_index,
                question_text=version.question_text,
                why_this=version.why_this,
                generation_source=version.generation_source,
                created_at=version.created_at,
                is_active=bool(active_version and active_version.id == version.id),
                my_rating=rating_map.get(version.id),
            )
            for version in recent_versions
        ]
        if active_version is None:
            continue
        summaries.append(
            PrebuildQuestionThreadSummary(
                thread_id=thread.id,
                focus_area_id=thread.focus_area_id,
                base_question_id=thread.base_question_id,
                question_role=thread.question_role,
                active_version_id=active_version.id,
                active_question_text=active_version.question_text,
                recent_versions=recent_summaries,
            )
        )
    return summaries


def _require_prebuild_role_access(
    *,
    application: Application,
    assignment: Assignment | None,
    workspace: InterviewWorkspace | None,
    current_user: User,
    require_question_management: bool,
) -> None:
    permissions = get_prebuild_permissions(
        application=application,
        assignment=assignment,
        workspace=workspace,
        current_user=current_user,
    )
    if permissions.locked:
        raise HTTPException(status_code=409, detail="Pre-build generation is locked for this application")
    if require_question_management and not permissions.can_manage_questions:
        raise HTTPException(status_code=403, detail="Not authorized to manage pre-build questions for this application")
    if not require_question_management and not permissions.can_rate_themes:
        raise HTTPException(status_code=403, detail="Not authorized to rate pre-build themes for this application")


def _get_thread_or_404(*, db: Session, application_id: UUID, thread_id: UUID) -> QuestionGenerationThread:
    thread = (
        db.query(QuestionGenerationThread)
        .filter(
            QuestionGenerationThread.id == thread_id,
            QuestionGenerationThread.application_id == application_id,
        )
        .first()
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Question generation thread not found")
    return thread


def _get_thread_version_or_404(
    *,
    db: Session,
    application_id: UUID,
    thread_id: UUID,
    version_id: UUID,
) -> QuestionGeneratedVersion:
    version = (
        db.query(QuestionGeneratedVersion)
        .filter(
            QuestionGeneratedVersion.id == version_id,
            QuestionGeneratedVersion.thread_id == thread_id,
            QuestionGeneratedVersion.application_id == application_id,
        )
        .first()
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Question version not found")
    return version


def _get_active_version_for_thread(*, db: Session, thread: QuestionGenerationThread) -> QuestionGeneratedVersion:
    active_version = (
        db.query(QuestionGeneratedVersion)
        .filter(
            QuestionGeneratedVersion.thread_id == thread.id,
            QuestionGeneratedVersion.id == thread.current_active_version_id,
        )
        .first()
    )
    if active_version is not None:
        return active_version
    active_version = (
        db.query(QuestionGeneratedVersion)
        .filter(QuestionGeneratedVersion.thread_id == thread.id, QuestionGeneratedVersion.is_active.is_(True))
        .order_by(QuestionGeneratedVersion.version_index.desc())
        .first()
    )
    if active_version is None:
        raise HTTPException(status_code=409, detail="No generated question version is available for this thread")
    return active_version


def _validate_rating_value(rating: int) -> None:
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Ratings must be between 1 and 5 stars")


def _extract_focus_areas(content: dict[str, Any]) -> list[dict[str, Any]]:
    page_4 = content.get("page_4_focus_areas")
    if isinstance(page_4, dict) and isinstance(page_4.get("focus_areas"), list):
        return [item for item in page_4.get("focus_areas", []) if isinstance(item, dict)]
    return []


def _extract_question_groups(content: dict[str, Any]) -> list[dict[str, Any]]:
    page_5 = content.get("page_5_question_groups")
    if isinstance(page_5, dict) and isinstance(page_5.get("question_groups"), list):
        return [item for item in page_5.get("question_groups", []) if isinstance(item, dict)]
    return []


def _build_application_snapshot(content: dict[str, Any]) -> dict[str, Any]:
    return {
        "page_1_background_profile": content.get("page_1_background_profile", {}),
        "page_2_academic_and_engagement": content.get("page_2_academic_and_engagement", {}),
        "page_3_essays": content.get("page_3_essays", {}),
    }


def _build_question_regeneration_messages(
    *,
    application_snapshot: dict[str, Any],
    thread: QuestionGenerationThread,
    current_question: str,
    current_why_this: str,
    retrieved_examples: list[dict[str, Any]],
) -> list[dict[str, str]]:
    system_prompt = (
        "You regenerate one interview question for an admissions interview brief. "
        "Preserve the exact question role while varying the wording, entry point, framing style, or conversational angle. "
        "Do not broaden or change what the question family is trying to elicit. "
        "Keep the language natural, human, and easy to ask in a real interview."
        "Return only valid JSON with keys question_text and why_this."
    )
    user_prompt = (
        f"Focus area title: {thread.theme_title_snapshot or 'Unknown'}\n"
        f"Line of inquiry: {thread.theme_direction_snapshot or 'Unknown'}\n"
        f"Question role: {thread.question_role or 'Unknown'}\n"
        f"Question set label: {thread.question_group_label_snapshot or 'Question set'}\n"
        f"Current question: {current_question}\n\n"
        f"Current why_this: {current_why_this or 'None'}\n\n"
        f"Applicant context:\n{json.dumps(application_snapshot, default=str)}\n\n"
        f"Retrieved prior generated examples:\n{json.dumps(retrieved_examples, default=str)}\n\n"
        "Create another version of the same question role. "
        "Keep the same role within the set and the same evidence target. "
        "Do not replace a debugging probe with a motivation probe, and do not replace a bottleneck probe with an aspiration probe. "
        "Return JSON like {\"question_text\": \"...\", \"why_this\": \"...\"}. "
        "why_this must be one short plain-English sentence explaining why this wording works, not the broader territory."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _normalize_generated_question_payload(value: str) -> dict[str, str]:
    raw_text = str(value or "").strip()
    parsed: Any = None
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                parsed = None
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail="Question regeneration returned invalid JSON")

    question_text = _normalize_generated_question_text(parsed.get("question_text"))
    why_this = _normalize_optional_why_this(parsed.get("why_this"))
    if not why_this:
        raise HTTPException(status_code=502, detail="Question regeneration returned an empty why_this")
    return {"question_text": question_text, "why_this": why_this}


def _normalize_generated_question_text(value: Any) -> str:
    cleaned = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split()).strip()
    cleaned = cleaned.strip("\"' ")
    if not cleaned:
        raise HTTPException(status_code=502, detail="Question regeneration returned an empty response")
    if len(cleaned) > QUESTION_REGEN_MAX_OUTPUT_CHARS:
        cleaned = cleaned[:QUESTION_REGEN_MAX_OUTPUT_CHARS].rstrip()
    return cleaned


def _normalize_optional_why_this(value: Any) -> str | None:
    cleaned = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split()).strip()
    cleaned = cleaned.strip("\"' ")
    return cleaned or None


def _vectorize_text(text: str) -> dict[str, float]:
    tokens = TOKEN_PATTERN.findall(text.lower())
    if not tokens:
        return {}
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0:
        return {}
    return {key: value / norm for key, value in counts.items()}


def _cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(key, 0.0) for key, value in left.items())


def _retrieve_similar_question_examples(
    *,
    db: Session,
    application_id: UUID,
    focus_area_id: str,
    theme_title: str,
    theme_direction: str,
    question_text: str,
) -> list[dict[str, Any]]:
    query_text = " ".join(part for part in [theme_title, theme_direction, question_text] if part).strip()
    query_vector = _vectorize_text(query_text)
    if not query_vector:
        return []

    documents = (
        db.query(VectorCorpusDocument)
        .filter(VectorCorpusDocument.entity_type == "question_version")
        .all()
    )
    scored: list[tuple[float, VectorCorpusDocument]] = []
    for document in documents:
        metadata = document.document_metadata if isinstance(document.document_metadata, dict) else {}
        if str(metadata.get("application_id")) == str(application_id):
            continue
        similarity = _cosine_similarity(query_vector, _coerce_vector_map(document.token_vector))
        if similarity <= 0:
            continue
        rating_bonus = float(metadata.get("rating_avg") or 0.0) / 10.0
        same_focus_bonus = 0.05 if str(metadata.get("focus_area_id")) == focus_area_id else 0.0
        scored.append((similarity + rating_bonus + same_focus_bonus, document))

    scored.sort(key=lambda item: item[0], reverse=True)
    examples: list[dict[str, Any]] = []
    for _, document in scored[:3]:
        metadata = document.document_metadata if isinstance(document.document_metadata, dict) else {}
        examples.append(
            {
                "question_text": document.document_text,
                "theme_title": metadata.get("theme_title"),
                "theme_direction": metadata.get("theme_direction"),
                "question_role": metadata.get("question_role"),
                "why_this": metadata.get("why_this"),
                "rating_avg": metadata.get("rating_avg"),
            }
        )
    return examples


def _coerce_vector_map(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, float] = {}
    for key, item in value.items():
        try:
            result[str(key)] = float(item)
        except (TypeError, ValueError):
            continue
    return result


def _upsert_theme_vector_document(
    *,
    db: Session,
    application_id: UUID,
    focus_area: dict[str, Any],
    theme_direction: str,
) -> None:
    focus_area_id = str(focus_area.get("focus_area_id") or "")
    if not focus_area_id:
        return
    text = " ".join(
        part
        for part in [
            str(focus_area.get("title") or ""),
            theme_direction,
            str(focus_area.get("territory") or ""),
            str(focus_area.get("what_makes_it_worth_time") or ""),
        ]
        if part
    ).strip()
    rating_values = [
        item.rating
        for item in db.query(ThemeRating)
        .filter(ThemeRating.application_id == application_id, ThemeRating.focus_area_id == focus_area_id)
        .all()
    ]
    metadata = {
        "application_id": str(application_id),
        "focus_area_id": focus_area_id,
        "theme_title": str(focus_area.get("title") or ""),
        "theme_direction": theme_direction,
        "rating_avg": round(sum(rating_values) / len(rating_values), 2) if rating_values else None,
    }
    _upsert_vector_document(
        db=db,
        entity_type="theme",
        entity_id=f"{application_id}:{focus_area_id}",
        document_text=text or str(focus_area.get("title") or ""),
        metadata=metadata,
    )


def _upsert_question_vector_document(*, db: Session, version: QuestionGeneratedVersion) -> None:
    question_role = (
        db.query(QuestionGenerationThread.question_role)
        .filter(QuestionGenerationThread.id == version.thread_id)
        .scalar()
    )
    rating_values = [
        item.rating
        for item in db.query(QuestionVersionRating)
        .filter(QuestionVersionRating.question_version_id == version.id)
        .all()
    ]
    metadata = {
        "application_id": str(version.application_id),
        "focus_area_id": version.focus_area_id,
        "theme_title": version.theme_title_snapshot,
        "theme_direction": version.theme_direction_snapshot,
        "question_role": question_role,
        "question_group_label": version.question_group_label_snapshot,
        "version_index": version.version_index,
        "generation_source": version.generation_source,
        "why_this": version.why_this,
        "rating_avg": round(sum(rating_values) / len(rating_values), 2) if rating_values else None,
    }
    _upsert_vector_document(
        db=db,
        entity_type="question_version",
        entity_id=str(version.id),
        document_text=" ".join(part for part in [version.question_text, version.why_this or ""] if part).strip(),
        metadata=metadata,
    )


def _derive_question_role(
    *,
    focus_area_title: str,
    line_of_inquiry: str,
    question_text: str,
    framing_note: str,
    explicit_question_role: str,
) -> str:
    explicit = _normalize_optional_why_this(explicit_question_role)
    if explicit:
        return explicit
    question_core = _normalize_generated_question_text(question_text).rstrip("?")
    framing_core = _normalize_optional_why_this(framing_note)
    line_core = _normalize_optional_why_this(line_of_inquiry)
    title_core = _normalize_optional_why_this(focus_area_title)
    parts = [f"Question family: {question_core}."]
    if framing_core:
        parts.append(f"Framing goal: {framing_core}")
    elif line_core:
        parts.append(f"Line of inquiry anchor: {line_core}")
    elif title_core:
        parts.append(f"Focus area anchor: {title_core}")
    return " ".join(parts)[:2000].rstrip()


def _upsert_vector_document(
    *,
    db: Session,
    entity_type: str,
    entity_id: str,
    document_text: str,
    metadata: dict[str, Any],
) -> None:
    document = (
        db.query(VectorCorpusDocument)
        .filter(VectorCorpusDocument.entity_type == entity_type, VectorCorpusDocument.entity_id == entity_id)
        .first()
    )
    token_vector = _vectorize_text(document_text)
    if document is None:
        document = VectorCorpusDocument(
            entity_type=entity_type,
            entity_id=entity_id,
            document_text=document_text,
            token_vector=token_vector,
            document_metadata=metadata,
        )
        db.add(document)
        return
    document.document_text = document_text
    document.token_vector = token_vector
    document.document_metadata = metadata
