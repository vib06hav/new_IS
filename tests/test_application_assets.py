import uuid

import fitz
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
from app.models.application import Application
from app.models.user import User
from app.storage import get_storage_service, storage_key_for_source_pdf


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


def auth_headers(email: str, role: str) -> dict[str, str]:
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


def test_source_pdf_is_served_from_storage_backend(tmp_path):
    original_storage_backend = settings.STORAGE_BACKEND
    original_upload_directory = settings.UPLOAD_DIRECTORY
    settings.STORAGE_BACKEND = "local"
    settings.UPLOAD_DIRECTORY = str(tmp_path)
    get_storage_service.cache_clear()

    db = TestingSessionLocal()
    try:
        db.query(Application).delete()
        db.query(User).delete()

        admin = User(
            id=uuid.uuid4(),
            name="Asset Admin",
            email="asset-admin@example.com",
            password_hash="x",
            role="admin",
        )
        application_id = uuid.uuid4()
        storage_key = storage_key_for_source_pdf(application_id)

        pdf_path = tmp_path / "source.pdf"
        document = fitz.open()
        document.new_page()
        document.save(str(pdf_path))
        document.close()

        get_storage_service().put_file(str(pdf_path), storage_key, "application/pdf")

        application = Application(
            id=application_id,
            display_id="ASSET-1",
            uploaded_by=admin.id,
            storage_key=storage_key,
            status="READY",
        )
        db.add_all([admin, application])
        db.commit()

        app.dependency_overrides[get_db] = override_get_db
        client = TestClient(app)
        response = client.get(
            f"/applications/{application_id}/source-pdf",
            headers=auth_headers(admin.email, admin.role),
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
    finally:
        app.dependency_overrides[get_db] = override_get_db
        db.close()
        settings.STORAGE_BACKEND = original_storage_backend
        settings.UPLOAD_DIRECTORY = original_upload_directory
        get_storage_service.cache_clear()
