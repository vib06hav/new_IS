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
from app.models.final_report import FinalReport
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


def test_admin_generate_report_and_interviewer_visibility():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
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
        display_id="APP-INT-001",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="READY",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3={
            "page_1_background_profile": {},
            "page_2_academic_and_engagement": {},
            "page_3_essays": {},
        },
    )
    db.add_all([admin, interviewer, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    interviewer_id = interviewer.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}
    interviewer_headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}

    fake_ros = {
        "report_metadata": {"report_version": "ROS_v1"},
        "page_1_background_profile": {},
        "page_2_academic_and_engagement": {},
        "page_3_essays": {},
        "page_4_focus_areas": {"themes": [], "signals": []},
        "page_5_question_groups": {"question_groups": []},
        "signal_data": {"annotations": {}},
    }

    with patch("app.api.admin.run_synthesis_pipeline", return_value={"ros_v1": fake_ros, "confidence": 0.9}):
        generate_response = client.post(f"/applications/{application_id}/generate-report", headers=admin_headers)

    assert generate_response.status_code == 200
    assert generate_response.json()["status"] == "COMPLETE"
    assert generate_response.json()["final_report"]["report_version"] == "ROS_v1"

    assign_response = client.post(
        f"/applications/{application_id}/assign",
        json={"interviewer_id": str(interviewer_id)},
        headers=admin_headers,
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "ASSIGNED"

    interviewer_detail = client.get(f"/applications/{application_id}", headers=interviewer_headers)
    assert interviewer_detail.status_code == 200
    assert interviewer_detail.json()["final_report"]["report_version"] == "ROS_v1"


def test_admin_generate_failure_moves_application_to_failed():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-fail@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-INT-FAIL",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="READY",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.api.admin.run_synthesis_pipeline", return_value={"ros_v1": None, "validation_result": {"violations_log": []}}):
        generate_response = client.post(f"/applications/{application_id}/generate-report", headers=admin_headers)

    assert generate_response.status_code == 502

    detail_response = client.get(f"/applications/{application_id}", headers=admin_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "FAILED"
    assert detail_response.json()["review_package"] is not None
    assert detail_response.json()["final_report"] is None


def test_interviewer_personal_hide_is_separate_from_admin_visibility():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-hide@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-hide@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-INT-003",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="ASSIGNED",
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={"report_metadata": {"report_version": "ROS_v1"}},
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, final_report, assignment])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    interviewer_headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}
    admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    before_hide = client.get(f"/applications/{application_id}", headers=admin_headers).json()["last_activity_at"]

    hide_response = client.post(f"/me/applications/{application_id}/hide", headers=interviewer_headers)
    assert hide_response.status_code == 200
    assert hide_response.json()["is_hidden"] is False
    assert hide_response.json()["is_hidden_for_interviewer"] is True

    my_items = client.get("/me/applications", headers=interviewer_headers)
    assert my_items.status_code == 200
    assert my_items.json()[0]["is_hidden_for_interviewer"] is True

    admin_items = client.get("/applications", headers=admin_headers)
    assert admin_items.status_code == 200
    assert admin_items.json()[0]["is_hidden"] is False
    assert admin_items.json()[0]["is_hidden_for_interviewer"] is True
    assert admin_items.json()[0]["last_activity_at"] >= before_hide

    unhide_response = client.post(f"/me/applications/{application_id}/unhide", headers=interviewer_headers)
    assert unhide_response.status_code == 200
    assert unhide_response.json()["is_hidden_for_interviewer"] is False


def test_admin_global_hide_removes_application_from_interviewer_list():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-global-hide@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-global-hide@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-INT-004",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="ASSIGNED",
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={"report_metadata": {"report_version": "ROS_v1"}},
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, final_report, assignment])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    interviewer_headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}
    admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    personal_hide = client.post(f"/me/applications/{application_id}/hide", headers=interviewer_headers)
    assert personal_hide.status_code == 200
    assert personal_hide.json()["is_hidden_for_interviewer"] is True

    global_hide = client.post(f"/applications/{application_id}/hide", headers=admin_headers)
    assert global_hide.status_code == 200
    assert global_hide.json()["is_hidden"] is True

    my_items = client.get("/me/applications", headers=interviewer_headers)
    assert my_items.status_code == 200
    assert my_items.json() == []

    blocked_unhide = client.post(f"/me/applications/{application_id}/unhide", headers=interviewer_headers)
    assert blocked_unhide.status_code == 409
    assert blocked_unhide.json()["detail"] == "Application is globally hidden"
