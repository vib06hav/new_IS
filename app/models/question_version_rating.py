import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class QuestionVersionRating(Base):
    __tablename__ = "question_version_ratings"
    __table_args__ = (
        UniqueConstraint("question_version_id", "rated_by_user_id", name="uq_question_version_rating_actor"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_version_id = Column(UUID(as_uuid=True), ForeignKey("question_generated_versions.id"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    rated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    surface_role = Column(String(50), nullable=False)
    surface_phase = Column(String(50), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
