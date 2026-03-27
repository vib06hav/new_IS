import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class CanonicalRecord(Base):
    __tablename__ = "canonical_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, unique=True)
    canonical_version = Column(String(20), nullable=False)
    canonical_data = Column(JSONB, nullable=False)
    deterministic_signals = Column(JSONB, nullable=True)
    pages_1_3 = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
