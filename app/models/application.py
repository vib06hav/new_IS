import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String(512), nullable=False)
    pipeline_status = Column(String(50), nullable=False)
    pipeline_confidence = Column(Numeric(5, 4), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
