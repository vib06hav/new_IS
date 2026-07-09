from __future__ import annotations

import logging
import time
from uuid import UUID

from app.processing import process_processing_job
from app.tasks.celery_app import celery_app
from app.telemetry.observability import increment_counter, record_histogram, start_span

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.processing.run_processing_job_task")
def run_processing_job_task(self, job_id: str) -> bool:
    started_at = time.perf_counter()
    status = "error"
    logger.info(
        "processing_task_started job_id=%s celery_task_id=%s",
        job_id,
        self.request.id,
    )
    with start_span(
        "celery.task",
        {
            "celery.task_name": "app.tasks.processing.run_processing_job_task",
            "celery.task_id": self.request.id,
            "processing.job_id": job_id,
            "queue": "processing",
        },
    ):
        try:
            processed = process_processing_job(UUID(job_id))
            status = "success" if processed else "skipped"
            logger.info(
                "processing_task_finished job_id=%s celery_task_id=%s processed=%s",
                job_id,
                self.request.id,
                processed,
            )
            return processed
        finally:
            attributes = {
                "task_name": "app.tasks.processing.run_processing_job_task",
                "queue": "processing",
                "status": status,
            }
            increment_counter("agis_celery_tasks_total", attributes=attributes)
            record_histogram("agis_celery_task_duration_seconds", time.perf_counter() - started_at, attributes=attributes)
