import uuid

from sqlalchemy import Column, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class VectorCorpusDocument(Base):
    __tablename__ = "vector_corpus_documents"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="uq_vector_corpus_entity"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(255), nullable=False)
    document_text = Column(String(8000), nullable=False)
    token_vector = Column(JSONB, nullable=False)
    document_metadata = Column("metadata", JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
