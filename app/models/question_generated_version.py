import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class QuestionGeneratedVersion(Base):
    __tablename__ = "question_generated_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("question_generation_threads.id"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    focus_area_id = Column(String(255), nullable=False, index=True)
    base_question_id = Column(String(255), nullable=False, index=True)
    version_index = Column(Integer, nullable=False)
    question_text = Column(String(4000), nullable=False)
    why_this = Column(String(2000), nullable=True)
    generation_source = Column(String(50), nullable=False)
    generated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    parent_version_id = Column(UUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False, server_default="false")
    theme_title_snapshot = Column(String(255), nullable=True)
    theme_direction_snapshot = Column(String(2000), nullable=True)
    question_group_label_snapshot = Column(String(255), nullable=True)
    application_context_snapshot = Column(JSONB, nullable=True)
    retrieval_context_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
