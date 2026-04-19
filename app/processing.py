from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.orchestrator import run_deterministic_pipeline
from app.coordination import LockNotAcquiredError, get_coordination_manager
from app.config import settings
from app.database import SessionLocal
from app.models.application import Application
from app.models.processing_job import ProcessingJob
from app.storage import get_storage_service

import logging

logger = logging.getLogger(__name__)

JOB_TYPE_DETERMINISTIC_PIPELINE = "deterministic_pipeline"
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

CLAIM_LOCK_TIMEOUT_SECONDS = 15.0


def enqueue_processing_job(db: Session, application_id: UUID, *, job_type: str = JOB_TYPE_DETERMINISTIC_PIPELINE) -> ProcessingJob:
    existing_job = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.application_id == application_id,
            ProcessingJob.job_type == job_type,
            ProcessingJob.status.in_([JOB_STATUS_QUEUED, JOB_STATUS_RUNNING]),
        )
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if existing_job is not None:
        return existing_job

    job = ProcessingJob(
        application_id=application_id,
        job_type=job_type,
        status=JOB_STATUS_QUEUED,
        attempts=0,
        available_at=datetime.utcnow(),
    )
    db.add(job)
    db.flush()
    return job


def _retry_backoff_seconds(attempt_number: int) -> float:
    base = settings.PROCESSING_JOB_BACKOFF_SECONDS
    multiplier = max(0, attempt_number - 1)
    return base * (2 ** multiplier)


def recover_stale_processing_jobs(db: Session) -> int:
    stale_before = datetime.utcnow() - timedelta(seconds=settings.PROCESSING_JOB_STALE_AFTER_SECONDS)
    stale_jobs = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.job_type == JOB_TYPE_DETERMINISTIC_PIPELINE, ProcessingJob.status == JOB_STATUS_RUNNING)
        .filter(ProcessingJob.started_at.isnot(None))
        .filter(ProcessingJob.started_at < stale_before)
        .all()
    )
    recovered = 0
    for job in stale_jobs:
        application = db.query(Application).filter(Application.id == job.application_id).first()
        if (job.attempts or 0) < settings.PROCESSING_JOB_MAX_ATTEMPTS:
            job.status = JOB_STATUS_QUEUED
            job.available_at = datetime.utcnow()
            job.last_error = "Recovered stale running job"
            job.started_at = None
            job.finished_at = None
            if application is not None:
                application.status = "PROCESSING"
                application.last_activity_at = datetime.utcnow()
        else:
            job.status = JOB_STATUS_FAILED
            job.available_at = None
            job.finished_at = datetime.utcnow()
            job.last_error = "Stale running job exceeded max attempts"
            if application is not None:
                application.status = "FAILED"
                application.last_activity_at = datetime.utcnow()
        recovered += 1
    if recovered:
        db.commit()
        logger.warning("Recovered %s stale processing job(s)", recovered)
    return recovered


def _claim_next_processing_job(db: Session) -> ProcessingJob | None:
    recover_stale_processing_jobs(db)
    now = datetime.utcnow()
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.job_type == JOB_TYPE_DETERMINISTIC_PIPELINE, ProcessingJob.status == JOB_STATUS_QUEUED)
        .filter((ProcessingJob.available_at.is_(None)) | (ProcessingJob.available_at <= now))
        .order_by(ProcessingJob.created_at.asc())
        .first()
    )
    if job is None:
        return None

    coordination = get_coordination_manager()
    try:
        with coordination.acquire(
            f"processing:claim:{job.id}",
            timeout_seconds=CLAIM_LOCK_TIMEOUT_SECONDS,
            blocking_timeout=0.0,
        ):
            db.refresh(job)
            if job.status != JOB_STATUS_QUEUED:
                return None
            if job.available_at is not None and job.available_at > now:
                return None

            job.status = JOB_STATUS_RUNNING
            job.attempts = (job.attempts or 0) + 1
            job.started_at = datetime.utcnow()
            job.last_error = None
            job.available_at = None
            db.commit()
            db.refresh(job)
            return job
    except LockNotAcquiredError:
        return None


def process_next_processing_job() -> bool:
    db = SessionLocal()
    try:
        job = _claim_next_processing_job(db)
        if job is None:
            return False

        application = db.query(Application).filter(Application.id == job.application_id).first()
        if application is None or not application.storage_key:
            _mark_job_failed_permanently(
                db,
                job,
                application,
                "Application or source asset not found",
            )
            db.commit()
            return True

        coordination = get_coordination_manager()
        try:
            with coordination.acquire(
                f"processing:run:{application.id}",
                timeout_seconds=max(settings.PROCESSING_JOB_STALE_AFTER_SECONDS + 60, 60),
                blocking_timeout=0.0,
            ):
                with get_storage_service().materialize_to_tempfile(application.storage_key, suffix=".pdf") as local_pdf_path:
                    run_deterministic_pipeline(str(application.id), local_pdf_path, db)
            job.status = JOB_STATUS_COMPLETED
            job.finished_at = datetime.utcnow()
            job.last_error = None
            db.commit()
        except LockNotAcquiredError:
            db.rollback()
            application = db.query(Application).filter(Application.id == job.application_id).first()
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job.id).first()
            if job is not None:
                job.status = JOB_STATUS_QUEUED
                job.available_at = datetime.utcnow() + timedelta(seconds=1)
                job.last_error = "Skipped because another worker holds the processing lock"
                job.started_at = None
                job.finished_at = None
                if application is not None:
                    application.status = "PROCESSING"
                    application.last_activity_at = datetime.utcnow()
                db.commit()
        except Exception as exc:
            db.rollback()
            application = db.query(Application).filter(Application.id == job.application_id).first()
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job.id).first()
            if job is not None:
                error_message = str(exc)[:1000]
                if (job.attempts or 0) < settings.PROCESSING_JOB_MAX_ATTEMPTS:
                    job.status = JOB_STATUS_QUEUED
                    job.available_at = datetime.utcnow() + timedelta(seconds=_retry_backoff_seconds(job.attempts or 1))
                    job.last_error = error_message
                    job.started_at = None
                    job.finished_at = None
                    if application is not None:
                        application.status = "PROCESSING"
                        application.last_activity_at = datetime.utcnow()
                else:
                    _mark_job_failed_permanently(db, job, application, error_message)
            db.commit()
            logger.exception("Background processing job failed for application %s", job.application_id if job else "unknown")
        return True
    finally:
        db.close()


class ProcessingWorker:
    def __init__(self, *, poll_seconds: float):
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="processing-worker", daemon=True)
        self._thread.start()
        logger.info("Background processing worker started")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=max(1.0, self.poll_seconds + 1.0))
        logger.info("Background processing worker stopped")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            processed = False
            try:
                processed = process_next_processing_job()
            except Exception:
                logger.exception("Background processing worker loop failed")

            if processed:
                continue
            self._stop_event.wait(self.poll_seconds)


def run_worker_forever(*, poll_seconds: float) -> None:
    while True:
        processed = False
        try:
            processed = process_next_processing_job()
        except Exception:
            logger.exception("Dedicated processing worker loop failed")

        if processed:
            continue
        threading.Event().wait(poll_seconds)


def should_start_background_workers() -> bool:
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    return False


def _mark_job_failed_permanently(
    db: Session,
    job: ProcessingJob,
    application: Application | None,
    error_message: str,
) -> None:
    if application is not None:
        application.status = "FAILED"
        application.last_activity_at = datetime.utcnow()
    job.status = JOB_STATUS_FAILED
    job.last_error = error_message[:1000]
    job.available_at = None
    job.finished_at = datetime.utcnow()
