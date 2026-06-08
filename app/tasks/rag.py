from __future__ import annotations

import logging
from uuid import UUID

from app.database import SessionLocal
from app.models.question_generated_version import QuestionGeneratedVersion
from app.rag.indexing import index_question_version
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.rag.index_question_version_task")
def index_question_version_task(self, version_id: str) -> dict:
    logger.info(
        "rag_index_task_started version_id=%s celery_task_id=%s",
        version_id,
        self.request.id,
    )
    db = SessionLocal()
    try:
        result = index_question_version(db, UUID(version_id))
        logger.info(
            "rag_index_task_finished version_id=%s celery_task_id=%s status=%s",
            version_id,
            self.request.id,
            result.get("status"),
        )
        return result
    finally:
        db.close()


@celery_app.task(name="app.tasks.rag.backfill_question_vectors_task")
def backfill_question_vectors_task(limit: int | None = None) -> dict:
    db = SessionLocal()
    try:
        query = db.query(QuestionGeneratedVersion.id).order_by(QuestionGeneratedVersion.created_at.asc())
        if limit is not None:
            query = query.limit(limit)
        version_ids = [str(row[0]) for row in query.all()]
    finally:
        db.close()

    queued = 0
    for version_id in version_ids:
        index_question_version_task.apply_async(args=[version_id])
        queued += 1
    logger.info("rag_backfill_queued count=%s", queued)
    return {"queued": queued}
