import uuid

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


def test_admin_assignments_and_interviewer_listing():
    db = TestingSessionLocal()
    db.query(Assignment).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-api@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-api@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-ADM-001",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="READY",
    )
    db.add_all([admin, interviewer, application])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    interviewer_id = interviewer.id
    interviewer_email = interviewer.email
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    list_response = client.get("/applications", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["status"] == "READY"

    assign_response = client.post(
        f"/applications/{application_id}/assign",
        json={"interviewer_id": str(interviewer_id)},
        headers=headers,
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "ASSIGNED"
    assert assign_response.json()["assigned_interviewer"]["email"] == interviewer_email
    assert assign_response.json()["is_hidden_for_interviewer"] is False
    assert "last_activity_at" in assign_response.json()

    assignments_response = client.get("/assignments", headers=headers)
    assert assignments_response.status_code == 200
    assert len(assignments_response.json()) == 1
    assert assignments_response.json()[0]["interviewer"]["email"] == interviewer_email

    interviewer_response = client.get("/users/interviewers", headers=headers)
    assert interviewer_response.status_code == 200
    assert interviewer_response.json()[0]["active_assignment_count"] == 1


def test_delete_interviewer_blocks_when_user_uploaded_applications():
    db = TestingSessionLocal()
    db.query(Assignment).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-delete@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Uploader Interviewer",
        email="uploader-interviewer@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-ADM-002",
        uploaded_by=interviewer.id,
        file_path="uploaded-by-interviewer.pdf",
        status="READY",
    )
    db.add_all([admin, interviewer, application])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    interviewer_id = interviewer.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    delete_response = client.delete(f"/users/{interviewer_id}", headers=headers)
    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == (
        "Cannot remove interviewer because they are referenced as the uploader for existing applications"
    )


def test_delete_interviewer_blocks_when_active_assignments_exist():
    db = TestingSessionLocal()
    db.query(Assignment).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-assigned@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Assigned Interviewer",
        email="assigned-interviewer@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-ADM-003",
        uploaded_by=admin.id,
        file_path="assigned.pdf",
        status="ASSIGNED",
    )
    assignment = Assignment(
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
    )
    db.add_all([admin, interviewer, application, assignment])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    interviewer_id = interviewer.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    delete_response = client.delete(f"/users/{interviewer_id}", headers=headers)
    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == "Cannot remove interviewer while they still have active assignments"


def test_admin_hide_sets_global_flag_without_affecting_personal_flag():
    db = TestingSessionLocal()
    db.query(Assignment).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-hide-flag@example.com", password_hash="x", role="admin")
    interviewer = User(
        id=uuid.uuid4(),
        name="Interviewer",
        email="interviewer-hide-flag@example.com",
        password_hash="x",
        role="interviewer",
    )
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-ADM-004",
        uploaded_by=admin.id,
        file_path="demo.pdf",
        status="ASSIGNED",
    )
    assignment = Assignment(
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=admin.id,
        is_hidden_for_interviewer=True,
    )
    db.add_all([admin, interviewer, application, assignment])
    db.commit()
    admin_email = admin.email
    admin_role = admin.role
    application_id = application.id
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_token_for(admin_email, admin_role)}"}

    hide_response = client.post(f"/applications/{application_id}/hide", headers=headers)
    assert hide_response.status_code == 200
    assert hide_response.json()["is_hidden"] is True
    assert hide_response.json()["is_hidden_for_interviewer"] is True


def test_application_insert_populates_last_activity_at_by_default():
    db = TestingSessionLocal()
    db.query(Assignment).delete()
    db.query(Application).delete()
    db.query(User).delete()

    admin = User(id=uuid.uuid4(), name="Admin", email="admin-default@example.com", password_hash="x", role="admin")
    application = Application(
        id=uuid.uuid4(),
        display_id="APP-ADM-005",
        uploaded_by=admin.id,
        file_path="default-last-activity.pdf",
        status="PROCESSING",
    )
    db.add_all([admin, application])
    db.commit()
    db.refresh(application)

    assert application.last_activity_at is not None

    db.close()
