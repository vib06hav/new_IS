from io import BytesIO
import tempfile
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User
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


def _headers(email: str, role: str) -> dict[str, str]:
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_upload_rejects_invalid_pdf_content():
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = tempfile.gettempdir()
        get_storage_service.cache_clear()

        db.query(User).delete()
        admin = User(
            id=uuid.uuid4(),
            name="Upload Admin",
            email="upload-admin@example.com",
            password_hash="x",
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_email = admin.email
        admin_role = admin.role
        db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        response = client.post(
            "/applications/upload",
            headers=_headers(admin_email, admin_role),
            files={"file": ("not-a-real.pdf", BytesIO(b"this is not a pdf"), "application/pdf")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Uploaded file is not a valid PDF"
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()


def test_upload_rejects_oversized_file():
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    original_limit = settings.MAX_UPLOAD_SIZE_MB
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = tempfile.gettempdir()
        get_storage_service.cache_clear()

        db.query(User).delete()
        admin = User(
            id=uuid.uuid4(),
            name="Upload Admin",
            email="upload-admin-oversized@example.com",
            password_hash="x",
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_email = admin.email
        admin_role = admin.role
        db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        settings.MAX_UPLOAD_SIZE_MB = 1
        response = client.post(
            "/applications/upload",
            headers=_headers(admin_email, admin_role),
            files={"file": ("oversized.pdf", BytesIO(b"0" * (2 * 1024 * 1024)), "application/pdf")},
        )
    finally:
        settings.MAX_UPLOAD_SIZE_MB = original_limit
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()

    assert response.status_code == 413
    assert response.json()["detail"] == "Uploaded file exceeds the 1 MB limit"


def test_upload_rate_limit_returns_429():
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    db = TestingSessionLocal()
    try:
        settings.STORAGE_BACKEND = "local"
        settings.UPLOAD_DIRECTORY = tempfile.gettempdir()
        get_storage_service.cache_clear()

        db.query(User).delete()
        admin = User(
            id=uuid.uuid4(),
            name="Upload Admin Rate Limit",
            email="upload-admin-rate@example.com",
            password_hash="x",
            role="admin",
        )
        db.add(admin)
        db.commit()
        admin_email = admin.email
        admin_role = admin.role
        db.close()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)

        for _ in range(10):
            response = client.post(
                "/applications/upload",
                headers=_headers(admin_email, admin_role),
                files={"file": ("invalid.pdf", BytesIO(b"not-a-real-pdf"), "application/pdf")},
            )
            assert response.status_code == 400

        throttled = client.post(
            "/applications/upload",
            headers=_headers(admin_email, admin_role),
            files={"file": ("invalid.pdf", BytesIO(b"not-a-real-pdf"), "application/pdf")},
        )
        assert throttled.status_code == 429
    finally:
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()
