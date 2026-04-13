from datetime import datetime, timedelta
import uuid
from unittest.mock import patch

import fitz
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base
from app.models.application import Application
from app.models.processing_job import ProcessingJob
from app.models.user import User
from app.processing import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    enqueue_processing_job,
    process_next_processing_job,
    recover_stale_processing_jobs,
)
from app.storage import get_storage_service, storage_key_for_source_pdf


@compiles(JSONB, "sqlite")
def compile_jsonb(element, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid(element, compiler, **kw):
    return "CHAR(32)"


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def test_enqueue_processing_job_deduplicates_active_jobs():
    db = TestingSessionLocal()
    try:
        application_id = uuid.uuid4()
        first_job = enqueue_processing_job(db, application_id)
        second_job = enqueue_processing_job(db, application_id)
        db.commit()

        assert first_job.id == second_job.id
        jobs = db.query(ProcessingJob).filter(ProcessingJob.application_id == application_id).all()
        assert len(jobs) == 1
        assert jobs[0].status == JOB_STATUS_QUEUED
    finally:
        db.close()


def test_process_next_processing_job_fetches_pdf_from_storage_and_updates_status(tmp_path):
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = str(tmp_path)
        get_storage_service.cache_clear()

        db.query(ProcessingJob).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Worker Admin", email="worker-admin@example.com", password_hash="x", role="admin")
        application_id = uuid.uuid4()
        storage_key = storage_key_for_source_pdf(application_id)

        pdf_path = tmp_path / "worker-source.pdf"
        document = fitz.open()
        document.new_page()
        document.save(str(pdf_path))
        document.close()
        get_storage_service().put_file(str(pdf_path), storage_key, "application/pdf")

        application = Application(
            id=application_id,
            display_id="WORKER-001",
            uploaded_by=admin.id,
            storage_key=storage_key,
            status="PROCESSING",
        )
        db.add_all([admin, application])
        enqueue_processing_job(db, application_id)
        db.commit()

        with patch("app.processing.SessionLocal", TestingSessionLocal), patch("app.processing.run_deterministic_pipeline") as mocked_pipeline:
            processed = process_next_processing_job()

        assert processed is True
        mocked_pipeline.assert_called_once()
        called_application_id, called_pdf_path = mocked_pipeline.call_args.args[:2]
        assert called_application_id == str(application_id)
        assert called_pdf_path.endswith(".pdf")

        db.refresh(application)
        job = db.query(ProcessingJob).filter(ProcessingJob.application_id == application_id).first()
        assert job is not None
        assert job.status == JOB_STATUS_COMPLETED
        assert job.finished_at is not None
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()
        db.close()


def test_process_next_processing_job_marks_failure_when_pipeline_raises(tmp_path):
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = str(tmp_path)
        get_storage_service.cache_clear()

        db.query(ProcessingJob).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Worker Admin", email="worker-admin-fail@example.com", password_hash="x", role="admin")
        application_id = uuid.uuid4()
        storage_key = storage_key_for_source_pdf(application_id)

        pdf_path = tmp_path / "worker-source-fail.pdf"
        document = fitz.open()
        document.new_page()
        document.save(str(pdf_path))
        document.close()
        get_storage_service().put_file(str(pdf_path), storage_key, "application/pdf")

        application = Application(
            id=application_id,
            display_id="WORKER-FAIL-001",
            uploaded_by=admin.id,
            storage_key=storage_key,
            status="PROCESSING",
        )
        db.add_all([admin, application])
        enqueue_processing_job(db, application_id)
        db.commit()

        with patch("app.processing.SessionLocal", TestingSessionLocal), patch(
            "app.processing.run_deterministic_pipeline", side_effect=RuntimeError("pipeline boom")
        ):
            processed = process_next_processing_job()

        assert processed is True
        db.refresh(application)
        job = db.query(ProcessingJob).filter(ProcessingJob.application_id == application_id).first()
        assert application.status == "PROCESSING"
        assert job is not None
        assert job.status == JOB_STATUS_QUEUED
        assert job.last_error == "pipeline boom"
        assert job.available_at is not None
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()
        db.close()


def test_process_next_processing_job_fails_permanently_after_max_attempts(tmp_path):
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    original_max_attempts = settings.PROCESSING_JOB_MAX_ATTEMPTS
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = str(tmp_path)
        settings.PROCESSING_JOB_MAX_ATTEMPTS = 1
        get_storage_service.cache_clear()

        db.query(ProcessingJob).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Worker Admin", email="worker-admin-max@example.com", password_hash="x", role="admin")
        application_id = uuid.uuid4()
        storage_key = storage_key_for_source_pdf(application_id)

        pdf_path = tmp_path / "worker-source-max.pdf"
        document = fitz.open()
        document.new_page()
        document.save(str(pdf_path))
        document.close()
        get_storage_service().put_file(str(pdf_path), storage_key, "application/pdf")

        application = Application(
            id=application_id,
            display_id="WORKER-MAX-001",
            uploaded_by=admin.id,
            storage_key=storage_key,
            status="PROCESSING",
        )
        db.add_all([admin, application])
        enqueue_processing_job(db, application_id)
        db.commit()

        with patch("app.processing.SessionLocal", TestingSessionLocal), patch(
            "app.processing.run_deterministic_pipeline", side_effect=RuntimeError("fatal boom")
        ):
            processed = process_next_processing_job()

        assert processed is True
        db.refresh(application)
        job = db.query(ProcessingJob).filter(ProcessingJob.application_id == application_id).first()
        assert application.status == "FAILED"
        assert job is not None
        assert job.status == JOB_STATUS_FAILED
        assert job.last_error == "fatal boom"
        assert job.available_at is None
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        settings.PROCESSING_JOB_MAX_ATTEMPTS = original_max_attempts
        get_storage_service.cache_clear()
        db.close()


def test_recover_stale_processing_jobs_requeues_running_job():
    original_stale_after_seconds = settings.PROCESSING_JOB_STALE_AFTER_SECONDS
    original_max_attempts = settings.PROCESSING_JOB_MAX_ATTEMPTS
    db = TestingSessionLocal()
    try:
        settings.PROCESSING_JOB_STALE_AFTER_SECONDS = 60
        settings.PROCESSING_JOB_MAX_ATTEMPTS = 3
        db.query(ProcessingJob).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Recover Admin", email="recover-admin@example.com", password_hash="x", role="admin")
        application = Application(
            id=uuid.uuid4(),
            display_id="RECOVER-001",
            uploaded_by=admin.id,
            storage_key="applications/recover/source.pdf",
            status="PROCESSING",
        )
        job = ProcessingJob(
            application_id=application.id,
            job_type="deterministic_pipeline",
            status="running",
            attempts=1,
            started_at=None,
        )
        db.add_all([admin, application, job])
        db.commit()
        job.started_at = datetime.utcnow() - timedelta(seconds=120)
        db.commit()

        recovered = recover_stale_processing_jobs(db)

        assert recovered == 1
        db.refresh(application)
        db.refresh(job)
        assert application.status == "PROCESSING"
        assert job.status == JOB_STATUS_QUEUED
        assert job.available_at is not None
        assert job.last_error == "Recovered stale running job"
    finally:
        settings.PROCESSING_JOB_STALE_AFTER_SECONDS = original_stale_after_seconds
        settings.PROCESSING_JOB_MAX_ATTEMPTS = original_max_attempts
        db.close()
