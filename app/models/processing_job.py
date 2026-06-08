import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default="queued")
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    celery_task_id = Column(String(255), nullable=True, index=True)
    queue_name = Column(String(100), nullable=True)
    progress = Column(Float, nullable=False, default=0.0, server_default="0")
    error_code = Column(String(100), nullable=True)
    last_error = Column(String(1000), nullable=True)
    available_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
