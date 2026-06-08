from __future__ import annotations

import logging
from uuid import UUID

from app.processing import process_processing_job
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.processing.run_processing_job_task")
def run_processing_job_task(self, job_id: str) -> bool:
    logger.info(
        "processing_task_started job_id=%s celery_task_id=%s",
        job_id,
        self.request.id,
    )
    processed = process_processing_job(UUID(job_id))
    logger.info(
        "processing_task_finished job_id=%s celery_task_id=%s processed=%s",
        job_id,
        self.request.id,
        processed,
    )
    return processed
