import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.user import User
from app.auth.dependencies import require_admin, require_interviewer, require_assigned_interviewer


@compiles(JSONB, "sqlite")
def compile_jsonb(element, compiler, **kw):
    return "JSON"


@compiles(UUID, "sqlite")
def compile_uuid(element, compiler, **kw):
    return "CHAR(32)"


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_require_admin_allows_admin():
    admin = User(name="Admin", email="admin@example.com", password_hash="x", role="admin")
    assert require_admin(admin) is admin


def test_require_admin_blocks_interviewer():
    interviewer = User(name="Interviewer", email="int@example.com", password_hash="x", role="interviewer")
    with pytest.raises(HTTPException) as exc_info:
        require_admin(interviewer)
    assert exc_info.value.status_code == 403


def test_require_interviewer_blocks_admin():
    admin = User(name="Admin", email="admin2@example.com", password_hash="x", role="admin")
    with pytest.raises(HTTPException) as exc_info:
        require_interviewer(admin)
    assert exc_info.value.status_code == 403


def test_require_assigned_interviewer_allows_assignee(db):
    interviewer = User(id=uuid.uuid4(), name="Interviewer", email="assigned@example.com", password_hash="x", role="interviewer")
    admin = User(id=uuid.uuid4(), name="Admin", email="owner@example.com", password_hash="x", role="admin")
    application = Application(id=uuid.uuid4(), display_id="APP-001", uploaded_by=admin.id, file_path="demo.pdf", status="ASSIGNED")
    assignment = Assignment(
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )

    db.add_all([admin, interviewer, application, assignment])
    db.commit()

    assert require_assigned_interviewer(application.id, interviewer, db) is interviewer


def test_require_assigned_interviewer_blocks_other_interviewer(db):
    interviewer = User(id=uuid.uuid4(), name="Interviewer", email="assigned2@example.com", password_hash="x", role="interviewer")
    other = User(id=uuid.uuid4(), name="Other", email="other@example.com", password_hash="x", role="interviewer")
    admin = User(id=uuid.uuid4(), name="Admin", email="owner2@example.com", password_hash="x", role="admin")
    application = Application(id=uuid.uuid4(), display_id="APP-002", uploaded_by=admin.id, file_path="demo.pdf", status="ASSIGNED")
    assignment = Assignment(
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )

    db.add_all([admin, interviewer, other, application, assignment])
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        require_assigned_interviewer(application.id, other, db)
    assert exc_info.value.status_code == 403
