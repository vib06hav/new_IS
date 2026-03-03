import uuid
from sqlalchemy import Column, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base

class SynthesisRecord(Base):
    __tablename__ = "synthesis_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False, unique=True)
    synthesis_output = Column(JSONB, nullable=False)
    policy_passed = Column(Boolean, nullable=False)
    policy_violations_log = Column(JSONB(none_as_null=True), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
