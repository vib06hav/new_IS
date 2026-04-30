import uuid
import tempfile
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
from app.models.interview_workspace import InterviewWorkspace
from app.models.user import User
from app.config import settings
from app.llm.client import LLMClientError
from app.report_chat import build_report_chat_context
from app.projection.ros_projector import project_ros
from app.storage.service import get_storage_service


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


def _pages_1_3_payload():
    return {
        "page_1_background_profile": {
            "identity": {
                "full_name": "Applicant Demo",
                "preferred_major": "Physics",
            }
        },
        "page_2_academic_and_engagement": {
            "academic_records": [
                {
                    "entity_id": "ACA-1",
                    "academic_level": "Class 10",
                    "board_name": "CBSE",
                    "score_raw": "96",
                }
            ],
            "standardized_tests": [
                {
                    "entity_id": "TEST-1",
                    "test_name": "SAT",
                    "total_score": "1520",
                }
            ],
            "extracurricular_activities": [
                {
                    "entity_id": "ACT-1",
                    "activity_name": "Robotics Club",
                    "activity_type": "extracurricular",
                }
            ],
            "leadership_roles": [
                {
                    "entity_id": "LEAD-1",
                    "position_title": "School Captain",
                }
            ],
        },
        "page_3_essays": {
            "essays": [
                {
                    "entity_id": "ESS-1",
                    "prompt": "Why this major?",
                    "full_text": "I want to study physics because I enjoy problem solving.",
                    "word_count": 11,
                }
            ]
        },
    }


def test_project_ros_adds_duration_years_for_activity_entries():
    canonical = {
        "identifiers": {"full_name": "Applicant Demo"},
        "academic_entries": [],
        "test_entries": [],
        "essay_entries": [],
        "activity_entries": [
            {
                "entry_id": "ACT-RAW-1",
                "activity_type": "extracurricular",
                "activity_name": "Music Piano",
                "level": "International",
                "duration": "5",
            }
        ],
    }

    _, page_2, _, annotated_canonical, _ = project_ros(canonical)

    assert annotated_canonical["activity_entries"][0]["duration"] == "5"
    assert page_2["extracurricular_activities"][0]["duration"] == "5"
    assert page_2["extracurricular_activities"][0]["duration_years"] == "5"


def test_admin_generate_report_and_interviewer_visibility():
    db = TestingSessionLocal()
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = tempfile.gettempdir()
        get_storage_service.cache_clear()

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
            storage_key="demo.pdf",
            status="PROCESSED",
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
        assert generate_response.json()["status"] == "READY"
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
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()


def test_generated_final_report_is_exported_to_storage_and_downloadable(tmp_path):
    db = TestingSessionLocal()
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = str(tmp_path)
        get_storage_service.cache_clear()

        db.query(FinalReport).delete()
        db.query(Assignment).delete()
        db.query(CanonicalRecord).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Admin", email="admin-export@example.com", password_hash="x", role="admin")
        application = Application(
            id=uuid.uuid4(),
            display_id="APP-EXPORT-001",
            uploaded_by=admin.id,
            storage_key="applications/demo/source.pdf",
            status="PROCESSED",
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
        db.add_all([admin, application, canonical])
        db.commit()
        admin_email = admin.email
        admin_role = admin.role
        application_id = application.id
        db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

        fake_ros = {
            "report_metadata": {"report_version": "ROS_v1"},
            "page_1_background_profile": {},
            "page_2_academic_and_engagement": {},
            "page_3_essays": {},
            "page_4_focus_areas": {"themes": [], "signals": []},
            "page_5_question_groups": {"question_groups": []},
        }

        with patch("app.api.admin.run_synthesis_pipeline", return_value={"ros_v1": fake_ros, "confidence": 0.9}):
            generate_response = client.post(f"/applications/{application_id}/generate-report", headers=admin_headers)

        assert generate_response.status_code == 200
        export_url = generate_response.json()["final_report"]["export_url"]
        assert export_url == f"/api/applications/{application_id}/final-report/export"

        export_response = client.get(f"/applications/{application_id}/final-report/export", headers=admin_headers)
        assert export_response.status_code == 200
        assert export_response.headers["content-type"] == "application/json"
        assert export_response.json()["report_metadata"]["report_version"] == "ROS_v1"

        db = TestingSessionLocal()
        final_report = db.query(FinalReport).filter(FinalReport.application_id == application_id).first()
        assert final_report is not None
        assert final_report.export_key == f"reports/{application_id}/exports/final-report.json"
        assert final_report.export_updated_at is not None
        storage = get_storage_service()
        assert storage.exists(final_report.export_key)
        db.close()
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()


def test_delete_application_removes_stored_final_report_export(tmp_path):
    db = TestingSessionLocal()
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = str(tmp_path)
        get_storage_service.cache_clear()
        storage = get_storage_service()

        db.query(FinalReport).delete()
        db.query(Assignment).delete()
        db.query(CanonicalRecord).delete()
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(id=uuid.uuid4(), name="Admin", email="admin-delete-export@example.com", password_hash="x", role="admin")
        application = Application(
            id=uuid.uuid4(),
            display_id="APP-EXPORT-DELETE",
            uploaded_by=admin.id,
            storage_key="applications/demo/source.pdf",
            status="READY",
        )
        final_report = FinalReport(
            id=uuid.uuid4(),
            application_id=application.id,
            content={"report_metadata": {"report_version": "ROS_v1"}},
            generated_by=admin.id,
            report_version="ROS_v1",
            export_key=f"reports/{application.id}/exports/final-report.json",
            export_content_type="application/json",
        )
        db.add_all([admin, application, final_report])
        db.commit()
        admin_email = admin.email
        admin_role = admin.role
        application_id = application.id
        export_key = final_report.export_key
        db.close()

        export_payload_path = tmp_path / "seed-export.json"
        export_payload_path.write_text('{"report_metadata":{"report_version":"ROS_v1"}}', encoding="utf-8")
        storage.put_file(str(export_payload_path), export_key, "application/json")
        assert storage.exists(export_key)

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        admin_headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

        delete_response = client.delete(f"/applications/{application_id}", headers=admin_headers)
        assert delete_response.status_code == 204
        assert not storage.exists(export_key)
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()


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
        storage_key="demo.pdf",
        status="PROCESSED",
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
        storage_key="demo.pdf",
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
        storage_key="demo.pdf",
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


def test_report_chat_blocks_unassigned_interviewer():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-3@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-chat-blocked@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-BLOCKED",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, interviewer, application, canonical])
    db.commit()
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}

    response = client.post(
        f"/applications/{application_id}/report-chat",
        json={"question": "What is the preferred major?"},
        headers=headers,
    )

    assert response.status_code == 403


def test_report_chat_rejects_blank_question():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-4@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-BLANK",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    response = client.post(
        f"/applications/{application_id}/report-chat",
        json={"question": "   "},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty"


def test_report_chat_rejects_oversized_question():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-oversized@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-LONG",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    response = client.post(
        f"/applications/{application_id}/report-chat",
        json={"question": "word " * 120},
        headers=headers,
    )

    assert response.status_code == 400
    assert "under" in response.json()["detail"]


def test_report_chat_lookup_returns_backend_owned_source_for_preferred_major():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-ADMIN",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What is the preferred major?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "lookup"
    assert body["not_found"] is False
    assert body["sources"][0]["anchor_id"] == "report-page1-overview"
    mocked_generate.assert_not_called()


def test_report_chat_context_routes_name_query_to_identity_lookup():
    context = build_report_chat_context("What's the applicant's name?", _pages_1_3_payload(), None)

    assert context["response_kind"] == "lookup"
    assert context["detected_operation"] == "retrieve"
    assert context["detected_target"] == "identity"
    assert context["selected_sections"] == ["page1_overview"]


def test_report_chat_lookup_can_use_final_report_focus_area():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-2@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-chat@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-INT",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="ASSIGNED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={
            "page_4_focus_areas": {"themes": [{"theme_id": "T1", "title": "Intellectual vitality"}], "signals": []},
            "page_5_question_groups": {"question_groups": [{"theme_id": "T1", "group_title": "Curiosity", "questions": ["What sparked your interest in physics?"]}]},
        },
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, canonical, final_report, assignment])
    db.commit()
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What is the main focus area?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "lookup"
    assert body["sources"][0]["target_tab"] == "page4"
    assert "Intellectual vitality" in body["answer_summary"]
    mocked_generate.assert_not_called()


def test_report_chat_question_groups_summary_uses_page_5_sources():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-redirect@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-REDIRECT",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={
            "page_4_focus_areas": {"themes": [{"theme_id": "T1", "title": "Intellectual vitality"}], "signals": []},
            "page_5_question_groups": {
                "question_groups": [{"theme_id": "T1", "group_title": "Curiosity", "questions": ["What sparked your interest in physics?"]}]
            },
        },
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    db.add_all([admin, application, canonical, final_report])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate", return_value="The report groups interview prompts around curiosity and follow-up questions."):
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What should interviewer ask?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "domain_summary"
    assert body["sources"][0]["target_tab"] == "page5"
    assert body["sources"][0]["section_key"] == "page5_question_groups"


def test_report_chat_scope_redirects_evaluative_questions():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-stands-out@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-STANDS-OUT",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={
            "page_4_focus_areas": {"themes": [{"theme_id": "T1", "title": "Intellectual vitality"}], "signals": []},
            "page_5_question_groups": {"question_groups": [{"theme_id": "T1", "group_title": "Curiosity", "questions": ["What sparked your interest in physics?"]}]},
        },
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    db.add_all([admin, application, canonical, final_report])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What stands out?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "scope_redirect"
    assert body["sources"] == []
    mocked_generate.assert_not_called()


def test_report_chat_domain_summary_of_activities_uses_compact_sources():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-list-activities@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-LIST-ACTIVITIES",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate", return_value="The activities section highlights robotics participation and extracurricular engagement."):
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Summarize the activities."},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "domain_summary"
    assert body["sources"][0]["section_key"] == "page2_activities"


def test_report_chat_lookup_lists_both_activity_buckets_for_broad_activity_query():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-activity-buckets@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-ACTIVITY-BUCKETS",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    pages = _pages_1_3_payload()
    pages["page_2_academic_and_engagement"]["extracurricular_activities"] = [
        {"entity_id": "ACT-1", "activity_name": "Music Piano", "activity_type": "extracurricular"},
    ]
    pages["page_2_academic_and_engagement"]["co_curricular_activities"] = [
        {"entity_id": "ACT-2", "activity_name": "Olympiads", "activity_type": "co_curricular"},
    ]
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=pages,
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What activities are listed?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert "Music Piano" in body["answer_summary"]
    assert "Olympiads" in body["answer_summary"]
    mocked_generate.assert_not_called()


def test_report_chat_lookup_lists_all_extracurricular_items_for_bucket_query():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-extracurriculars@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-EXTRACURRICULARS",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    pages = _pages_1_3_payload()
    pages["page_2_academic_and_engagement"]["extracurricular_activities"] = [
        {"entity_id": "ACT-1", "activity_name": "Music Piano", "activity_type": "extracurricular"},
        {"entity_id": "ACT-2", "activity_name": "Yoga", "activity_type": "extracurricular"},
    ]
    pages["page_2_academic_and_engagement"]["co_curricular_activities"] = [
        {"entity_id": "ACT-3", "activity_name": "Olympiads", "activity_type": "co_curricular"},
    ]
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=pages,
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Extracurriculars"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert "Music Piano" in body["answer_summary"]
    assert "Yoga" in body["answer_summary"]
    assert "Olympiads" not in body["answer_summary"]
    mocked_generate.assert_not_called()


def test_report_chat_page_4_request_returns_safe_not_found_without_final_report():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-no-final@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-NO-FINAL",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Why is this a concern?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["not_found"] is True
    assert "not available" in body["answer_summary"].lower()
    mocked_generate.assert_not_called()


def test_report_chat_lookup_returns_entity_level_test_source_for_entrance_performance():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-entrance@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-ENTRANCE",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "How was the entrance performance?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert "1520" in body["answer_summary"]
    assert body["sources"][0]["label"] == "SAT"
    assert body["sources"][0]["entity_id"] == "TEST-1"
    mocked_generate.assert_not_called()


def test_report_chat_lookup_returns_entity_level_academic_source_for_board_score():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-board-score@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-BOARD-SCORE",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What was the 10th board score?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert "96" in body["answer_summary"]
    assert body["sources"][0]["label"] == "Class 10"
    assert body["sources"][0]["entity_id"] == "ACA-1"
    mocked_generate.assert_not_called()


def test_report_chat_subject_specific_marks_fall_back_to_broader_academic_record():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-class11@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-CLASS11",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    pages = _pages_1_3_payload()
    pages["page_2_academic_and_engagement"]["academic_records"].append(
        {
            "entity_id": "ACA-2",
            "academic_level": "Class 11",
            "board_name": "CBSE",
            "score_raw": "95",
            "subject_entries": [
                {"subject_name": "Physics", "score_raw": "91", "max_score_raw": "100"},
                {"subject_name": "Mathematics", "score_raw": "97", "max_score_raw": "100"},
            ],
        }
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=pages,
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "What are the marks in 11th physics?"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert "Class 11 academic record" in body["answer_summary"]
    assert "91" not in body["answer_summary"]
    assert body["sources"][0]["label"] == "Class 11"
    assert body["sources"][0]["entity_id"] == "ACA-2"
    mocked_generate.assert_not_called()


def test_report_chat_redirects_whole_candidate_summary_requests():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-about@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-ABOUT",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate") as mocked_generate:
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Tell me about this candidate"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "scope_redirect"
    mocked_generate.assert_not_called()


def test_report_chat_summary_falls_back_to_degraded_when_llm_is_unavailable():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-fallback@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-FALLBACK",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    db.add_all([admin, application, canonical])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate", side_effect=LLMClientError("disabled")):
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Summarize the activities."},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "degraded"
    assert body["sources"] == []
    assert "activity" in body["answer_summary"].lower()


def test_report_chat_essay_summary_can_use_fragment_level_sources():
    db = TestingSessionLocal()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-chat-essay@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-CHAT-ESSAY",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="PROCESSED",
    )
    canonical = CanonicalRecord(
        id=uuid.uuid4(),
        application_id=application.id,
        canonical_version="1.0",
        canonical_data={"identifiers": {"full_name": "Applicant Demo"}},
        pages_1_3=_pages_1_3_payload(),
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={
            "page_4_focus_areas": {"themes": [{"theme_id": "T1", "title": "Intellectual vitality"}], "signals": []},
            "page_5_question_groups": {"question_groups": []},
            "signal_data": {
                "annotations": {
                    "page_2_entities": {},
                    "page_3_fragments": {
                        "ESS-1": [
                            {
                                "fragment_id": "FRAG-ESS-1",
                                "start_char": 0,
                                "end_char": 22,
                                "signal_ids": ["SIG-1"],
                                "theme_ids": ["THEME-1"],
                            }
                        ]
                    },
                }
            },
        },
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    db.add_all([admin, application, canonical, final_report])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    with patch("app.report_chat.generate", return_value="The writing emphasizes curiosity, physics, and problem solving."):
        response = client.post(
            f"/applications/{application_id}/report-chat",
            json={"question": "Summarize the essay."},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["response_kind"] == "domain_summary"
    assert body["sources"][0]["fragment_id"] == "FRAG-ESS-1"
    assert body["sources"][0]["anchor_id"] == "report-fragment-frag-ess-1"


def test_report_chat_comparison_question_routes_to_page_4_summary_context():
    context = build_report_chat_context(
        "Compare academics and tests for this candidate.",
        _pages_1_3_payload(),
        {
            "page_4_focus_areas": {
                "themes": [{"theme_id": "T1", "title": "Academic readiness"}],
                "signals": [],
            }
        },
    )

    assert context["question_shape_bucket"] == "comparison"
    assert context["response_kind"] == "domain_summary"
    assert context["detected_operation"] == "explain"
    assert context["detected_target"] == "signals"
    assert context["selected_sections"] == ["page4_focus_areas"]
    assert context["source_scope"] == "page4_only"


def test_interviewer_can_create_finish_and_complete_workspace():
    db = TestingSessionLocal()
    db.query(InterviewWorkspace).delete()
    db.query(FinalReport).delete()
    db.query(Assignment).delete()
    db.query(CanonicalRecord).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-workspace@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-workspace@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-WS-001",
        uploaded_by=admin.id,
        storage_key="demo.pdf",
        status="ASSIGNED",
    )
    assignment = Assignment(
        id=uuid.uuid4(),
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    final_report = FinalReport(
        id=uuid.uuid4(),
        application_id=application.id,
        content={
            "page_4_focus_areas": {
                "themes": [
                    {
                        "theme_id": "THEME-001",
                        "title": "Intellectual vitality",
                        "unifying_axis": "How the applicant thinks through ambiguous problems.",
                        "interview_direction": "Probe reasoning, not polished narrative.",
                    }
                ],
                "signals": [],
            },
            "page_5_question_groups": {
                "question_groups": [
                    {
                        "theme_id": "THEME-001",
                        "group_title": "Reasoning prompts",
                        "questions": ["Tell me about a time you changed your mind while solving something difficult."],
                    }
                ]
            },
        },
        generated_by=admin.id,
        report_version="ROS_v1",
    )
    db.add_all([admin, interviewer, application, assignment, final_report])
    db.commit()
    interviewer_email = interviewer.email
    interviewer_role = interviewer.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(interviewer_email, interviewer_role)}"}

    create_response = client.post(f"/me/applications/{application_id}/workspace", headers=headers)
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "draft"
    assert created["content"]["themes"][0]["title"] == "Intellectual vitality"
    assert created["content"]["themes"][0]["questions"][0]["text"].startswith("Tell me about a time")
    assert created["content"]["themes"][0]["questions"][0]["status"] == "unasked"

    created["content"]["themes"][0]["questions"].append(
        {
            "id": "custom-q-1",
            "text": "What would you do differently now?",
            "source": "custom",
            "status": "mixed",
            "note": "",
            "order": 1,
        }
    )
    created["content"]["final_summary"] = "Initial draft summary."

    update_response = client.put(
        f"/me/applications/{application_id}/workspace",
        json={"content": created["content"]},
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert len(updated["content"]["themes"][0]["questions"]) == 2
    assert updated["content"]["final_summary"] == "Initial draft summary."

    launch_response = client.post(
        f"/me/applications/{application_id}/workspace/launch",
        json={"content": updated["content"]},
        headers=headers,
    )
    assert launch_response.status_code == 200
    launched = launch_response.json()
    assert launched["status"] == "launched"
    assert launched["launched_at"] is not None

    launched["content"]["themes"][0]["questions"][0]["status"] = "satisfactory"
    launched["content"]["themes"][0]["questions"][0]["note"] = "Strong answer with clear reflection."

    finish_response = client.post(
        f"/me/applications/{application_id}/workspace/finish",
        json={"content": launched["content"]},
        headers=headers,
    )
    assert finish_response.status_code == 200
    postgame = finish_response.json()
    assert postgame["status"] == "postgame"
    assert postgame["content"]["themes"][0]["questions"][0]["status"] == "satisfactory"

    postgame["content"]["final_summary"] = "Published final summary."
    complete_response = client.post(
        f"/me/applications/{application_id}/workspace/complete",
        json={"content": postgame["content"]},
        headers=headers,
    )
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["status"] == "completed"
    assert completed["completed_at"] is not None

    db = TestingSessionLocal()
    refreshed_application = db.query(Application).filter(Application.id == application_id).first()
    assert refreshed_application is not None
    assert refreshed_application.status == "COMPLETE"
    db.close()
