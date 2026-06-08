from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.config import settings
from app.models.question_generated_version import QuestionGeneratedVersion
from app.models.question_generation_thread import QuestionGenerationThread
from app.models.question_version_rating import QuestionVersionRating
from app.rag.qdrant_store import upsert_question_point

logger = logging.getLogger(__name__)

_PENDING_VERSION_IDS_KEY = "rag_pending_question_version_ids"


def schedule_question_version_index(db: Session, version_id: UUID) -> None:
    pending = db.info.setdefault(_PENDING_VERSION_IDS_KEY, set())
    pending.add(str(version_id))


@event.listens_for(Session, "after_commit")
def _dispatch_pending_question_indexes(db: Session) -> None:
    pending = db.info.pop(_PENDING_VERSION_IDS_KEY, set())
    if not pending:
        return
    if not settings.QDRANT_URL or settings.QDRANT_DISABLE:
        logger.debug("rag_index_dispatch_skipped reason=qdrant_disabled count=%s", len(pending))
        return

    from app.tasks.rag import index_question_version_task

    for version_id in sorted(pending):
        try:
            index_question_version_task.apply_async(args=[version_id], queue=settings.CELERY_QUEUE_GENERATION)
        except Exception:
            logger.exception("rag_index_dispatch_failed version_id=%s", version_id)


def build_question_version_document(db: Session, version_id: UUID) -> tuple[str, dict[str, Any]] | None:
    version = db.query(QuestionGeneratedVersion).filter(QuestionGeneratedVersion.id == version_id).first()
    if version is None:
        return None

    thread = db.query(QuestionGenerationThread).filter(QuestionGenerationThread.id == version.thread_id).first()
    theme_title = version.theme_title_snapshot or (thread.theme_title_snapshot if thread else None)
    theme_direction = version.theme_direction_snapshot or (thread.theme_direction_snapshot if thread else None)
    question_group_label = version.question_group_label_snapshot or (thread.question_group_label_snapshot if thread else None)
    rating_values = [
        item.rating
        for item in db.query(QuestionVersionRating)
        .filter(QuestionVersionRating.question_version_id == version.id)
        .all()
    ]
    rating_avg = round(sum(rating_values) / len(rating_values), 2) if rating_values else None

    text = " ".join(
        part
        for part in [
            theme_title or "",
            theme_direction or "",
            thread.question_role if thread else "",
            version.question_text,
            version.why_this or "",
        ]
        if part
    ).strip()
    payload = {
        "application_id": str(version.application_id),
        "focus_area_id": version.focus_area_id,
        "thread_id": str(version.thread_id),
        "base_question_id": version.base_question_id,
        "question_role": thread.question_role if thread else None,
        "theme_title": theme_title,
        "theme_direction": theme_direction,
        "question_group_label": question_group_label,
        "question_text": version.question_text,
        "why_this": version.why_this,
        "version_index": version.version_index,
        "generation_source": version.generation_source,
        "rating_avg": rating_avg,
        "rating_count": len(rating_values),
        "embedding_model": settings.RAG_EMBEDDING_MODEL,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }
    return text, payload


def index_question_version(db: Session, version_id: UUID) -> dict[str, Any]:
    document = build_question_version_document(db, version_id)
    if document is None:
        return {"status": "skipped", "reason": "question_version_not_found", "version_id": str(version_id)}

    text, payload = document
    result = upsert_question_point(point_id=str(version_id), text=text, payload=payload)
    logger.info("rag_index_question_version version_id=%s status=%s", version_id, result.get("status"))
    return result
