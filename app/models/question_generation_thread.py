import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class QuestionGenerationThread(Base):
    __tablename__ = "question_generation_threads"
    __table_args__ = (
        UniqueConstraint(
            "application_id",
            "focus_area_id",
            "base_question_id",
            name="uq_question_generation_thread_identity",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    focus_area_id = Column(String(255), nullable=False, index=True)
    base_question_id = Column(String(255), nullable=False)
    question_role = Column(String(2000), nullable=False)
    question_group_label_snapshot = Column(String(255), nullable=True)
    theme_title_snapshot = Column(String(255), nullable=True)
    theme_direction_snapshot = Column(String(2000), nullable=True)
    current_active_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
