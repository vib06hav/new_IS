import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class ThemeRating(Base):
    __tablename__ = "theme_ratings"
    __table_args__ = (
        UniqueConstraint("application_id", "focus_area_id", "rated_by_user_id", name="uq_theme_rating_actor"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, index=True)
    focus_area_id = Column(String(255), nullable=False)
    surface_role = Column(String(50), nullable=False)
    surface_phase = Column(String(50), nullable=False)
    rated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
