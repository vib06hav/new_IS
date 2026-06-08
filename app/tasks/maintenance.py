from __future__ import annotations

import logging

from app.database import SessionLocal
from app.processing import recover_stale_processing_jobs
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.maintenance.recover_stale_processing_jobs_task")
def recover_stale_processing_jobs_task() -> int:
    db = SessionLocal()
    try:
        recovered = recover_stale_processing_jobs(db)
        logger.info("processing_stale_recovery completed recovered=%s", recovered)
        return recovered
    finally:
        db.close()
