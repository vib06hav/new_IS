from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # noqa: F401


@compiles(JSONB, "sqlite")
def compile_jsonb(element, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid(element, compiler, **kw):
    return "CHAR(32)"


def test_schema():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)

    tables = set(inspector.get_table_names())
    required = {"users", "applications", "canonical_records", "assignments", "drafts"}
    assert required.issubset(tables), f"Found tables: {tables}"
    assert "synthesis_records" not in tables

    users_cols = {col["name"]: col for col in inspector.get_columns("users")}
    assert "name" in users_cols

    app_cols = {col["name"]: col for col in inspector.get_columns("applications")}
    assert "status" in app_cols
    assert "pipeline_status" not in app_cols
    assert "pipeline_confidence" not in app_cols

    assignment_fks = inspector.get_foreign_keys("assignments")
    assert len(assignment_fks) == 3

    drafts_cols = {col["name"]: col for col in inspector.get_columns("drafts")}
    assert {"application_id", "version", "content", "generated_by", "is_published"}.issubset(drafts_cols.keys())
