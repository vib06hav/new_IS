from __future__ import annotations

import logging
import time
from uuid import UUID

from app.database import SessionLocal
from app.models.question_generated_version import QuestionGeneratedVersion
from app.rag.indexing import index_question_version
from app.tasks.celery_app import celery_app
from app.telemetry.observability import increment_counter, record_histogram, start_span

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.rag.index_question_version_task")
def index_question_version_task(self, version_id: str) -> dict:
    started_at = time.perf_counter()
    status = "error"
    logger.info(
        "rag_index_task_started version_id=%s celery_task_id=%s",
        version_id,
        self.request.id,
    )
    with start_span(
        "celery.task",
        {
            "celery.task_name": "app.tasks.rag.index_question_version_task",
            "celery.task_id": self.request.id,
            "rag.version_id": version_id,
            "queue": "generation",
        },
    ):
        db = SessionLocal()
        try:
            result = index_question_version(db, UUID(version_id))
            status = str(result.get("status") or "unknown")
            logger.info(
                "rag_index_task_finished version_id=%s celery_task_id=%s status=%s",
                version_id,
                self.request.id,
                result.get("status"),
            )
            return result
        finally:
            db.close()
            attributes = {
                "task_name": "app.tasks.rag.index_question_version_task",
                "queue": "generation",
                "status": status,
            }
            increment_counter("agis_celery_tasks_total", attributes=attributes)
            record_histogram("agis_celery_task_duration_seconds", time.perf_counter() - started_at, attributes=attributes)


@celery_app.task(name="app.tasks.rag.backfill_question_vectors_task")
def backfill_question_vectors_task(limit: int | None = None) -> dict:
    started_at = time.perf_counter()
    with start_span(
        "celery.task",
        {
            "celery.task_name": "app.tasks.rag.backfill_question_vectors_task",
            "queue": "generation",
            "limit": limit or 0,
        },
    ):
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
        increment_counter(
            "agis_celery_tasks_total",
            attributes={"task_name": "app.tasks.rag.backfill_question_vectors_task", "queue": "generation", "status": "success"},
        )
        record_histogram(
            "agis_celery_task_duration_seconds",
            time.perf_counter() - started_at,
            attributes={"task_name": "app.tasks.rag.backfill_question_vectors_task", "queue": "generation", "status": "success"},
        )
        return {"queued": queued}
