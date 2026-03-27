import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.database import Base, get_db
from app.main import app
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.canonical_record import CanonicalRecord
from app.models.draft import Draft
from app.models.user import User


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

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _token_for(email: str, role: str) -> str:
    return create_access_token({"sub": email, "role": role})


def test_generate_publish_and_admin_visibility():
    db = TestingSessionLocal()
    db.query(Draft).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-flow@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-flow@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="ASSIGNED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, canonical, assignment])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    interviewer_headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}
    admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    fake_ros = {
        "report_metadata": {"report_version": "ROS_v1"},
        "page_1_background_profile": {},
        "page_2_academic_and_engagement": {},
        "page_3_essays": {},
        "page_4_focus_areas": {"themes": [], "signals": []},
        "page_5_question_groups": {"question_groups": []},
    }

    with patch("app.api.interviewer.run_synthesis_pipeline", return_value={"ros_v1": fake_ros, "confidence": 0.9}):
        generate_response = client.post(
            f"/applications/{application_id}/generate",
            headers=interviewer_headers,
        )
    assert generate_response.status_code == 200
    assert generate_response.json()["status"] == "DRAFT"
    assert generate_response.json()["draft"]["version"] == 1

    admin_before_publish = client.get(f"/applications/{application_id}", headers=admin_headers)
    assert admin_before_publish.status_code == 200
    assert admin_before_publish.json()["published_draft"] is None
    assert admin_before_publish.json()["review_package"]["canonical_version"] == "1.0"

    publish_response = client.post(
        f"/applications/{application_id}/publish",
        headers=interviewer_headers,
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "PUBLISHED"
    assert publish_response.json()["draft"]["is_published"] is True

    admin_after_publish = client.get(f"/applications/{application_id}", headers=admin_headers)
    assert admin_after_publish.status_code == 200
    assert admin_after_publish.json()["published_draft"]["is_published"] is True


def test_generate_rate_limit_returns_429():
    db = TestingSessionLocal()
    db.query(Draft).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-rate@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-rate@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="ASSIGNED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, canonical, assignment])
    db.commit()
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    interviewer_headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}

    with patch("app.api.interviewer.run_synthesis_pipeline", return_value={"ros_v1": {}, "confidence": 0.9}):
        for _ in range(5):
            response = client.post(
                f"/applications/{application_id}/generate",
                headers=interviewer_headers,
            )
            assert response.status_code == 200

        throttled = client.post(
            f"/applications/{application_id}/generate",
            headers=interviewer_headers,
        )

    assert throttled.status_code == 429
