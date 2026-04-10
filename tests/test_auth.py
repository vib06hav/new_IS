from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token, get_password_hash
from app.auth.service import bootstrap_admin_user, ensure_dev_admin_user
from app.config import settings
from app.database import Base, get_db
from app.main import app
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
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def auth_headers(email: str, role: str) -> dict[str, str]:
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


app.dependency_overrides[get_db] = override_get_db


def make_client() -> TestClient:
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def session_csrf_headers(client: TestClient, *, origin: str = "http://testserver") -> dict[str, str]:
    token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    assert token
    return {
        settings.CSRF_HEADER_NAME: token,
        "Origin": origin,
    }


def test_register_requires_admin():
    client = make_client()
    response = client.post(
        "/auth/register",
        json={
            "name": "Blocked User",
            "email": "blocked@example.com",
            "password": "securepassword123",
            "role": "interviewer",
        },
    )
    assert response.status_code == 401


def test_admin_can_create_interviewer():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-create@example.com",
        password_hash=get_password_hash("securepassword123"),
        role="admin",
    )
    db.add(admin)
    db.commit()

    response = client.post(
        "/users/interviewers",
        json={
            "name": "Test Interviewer",
            "email": "testinterviewer@example.com",
            "password": "securepassword123",
        },
        headers=auth_headers(admin.email, admin.role),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Interviewer"
    assert data["email"] == "testinterviewer@example.com"
    assert data["role"] == "interviewer"


def test_create_interviewer_rejects_existing_email():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-existing@example.com",
        password_hash=get_password_hash("securepassword123"),
        role="admin",
    )
    existing = User(
        name="Existing",
        email="existing@example.com",
        password_hash=get_password_hash("securepassword123"),
        role="interviewer",
    )
    db.add_all([admin, existing])
    db.commit()

    response = client.post(
        "/users/interviewers",
        json={
            "name": "Another User",
            "email": "existing@example.com",
            "password": "securepassword123",
        },
        headers=auth_headers(admin.email, admin.role),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_admin_register_endpoint_blocks_admin_role_creation():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-role-block@example.com",
        password_hash=get_password_hash("securepassword123"),
        role="admin",
    )
    db.add(admin)
    db.commit()

    response = client.post(
        "/auth/register",
        json={
            "name": "Another Admin",
            "email": "another-admin@example.com",
            "password": "securepassword123",
            "role": "admin",
        },
        headers=auth_headers(admin.email, admin.role),
    )
    assert response.status_code == 403


def test_login_user():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Login User",
            email="testuser@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="admin",
        )
    )
    db.commit()

    response = client.post(
        "/auth/login",
        data={"username": "testuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "testuser@example.com"
    assert response.cookies.get(settings.SESSION_COOKIE_NAME)
    assert response.cookies.get(settings.CSRF_COOKIE_NAME)

    session_response = client.get("/auth/session")
    assert session_response.status_code == 200
    assert session_response.json()["user"]["role"] == "admin"


def test_login_invalid_password():
    client = make_client()
    response = client.post(
        "/auth/login",
        data={"username": "testuser@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_logout_clears_session_cookie():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Logout User",
            email="logout@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="admin",
        )
    )
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={"username": "logout@example.com", "password": "securepassword123"},
    )
    assert login_response.status_code == 200
    assert client.get("/auth/session").status_code == 200

    logout_response = client.post("/auth/logout", headers=session_csrf_headers(client))
    assert logout_response.status_code == 204
    assert client.get("/auth/session").status_code == 401


def test_cookie_session_requires_csrf_header_for_mutations():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Cookie Admin",
            email="cookie-admin@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="admin",
        )
    )
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={"username": "cookie-admin@example.com", "password": "securepassword123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/users/interviewers",
        json={
            "name": "Blocked Interviewer",
            "email": "blocked-csrf@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Missing trusted request origin"


def test_cookie_session_mutation_succeeds_with_matching_csrf_header():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Cookie Admin",
            email="cookie-admin-success@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="admin",
        )
    )
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={"username": "cookie-admin-success@example.com", "password": "securepassword123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/users/interviewers",
        json={
            "name": "Allowed Interviewer",
            "email": "allowed-csrf@example.com",
            "password": "securepassword123",
        },
        headers=session_csrf_headers(client),
    )
    assert response.status_code == 201


def test_cookie_session_can_update_own_profile_name():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Original Interviewer",
            email="profile-update@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="interviewer",
        )
    )
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={"username": "profile-update@example.com", "password": "securepassword123"},
    )
    assert login_response.status_code == 200

    response = client.put(
        "/auth/profile",
        json={"name": "Updated Interviewer"},
        headers=session_csrf_headers(client),
    )
    assert response.status_code == 200
    assert response.json()["user"]["name"] == "Updated Interviewer"
    assert client.get("/auth/session").json()["user"]["name"] == "Updated Interviewer"


def test_cookie_session_rejects_cross_site_origin_even_with_csrf_token():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(
        User(
            name="Origin Admin",
            email="origin-admin@example.com",
            password_hash=get_password_hash("securepassword123"),
            role="admin",
        )
    )
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={"username": "origin-admin@example.com", "password": "securepassword123"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/users/interviewers",
        json={
            "name": "Cross Site Interviewer",
            "email": "cross-site@example.com",
            "password": "securepassword123",
        },
        headers=session_csrf_headers(client, origin="https://evil.example"),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid request origin"


def test_login_rate_limit_returns_429():
    client = make_client()
    for _ in range(5):
        response = client.post(
            "/auth/login",
            data={"username": "missing@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    throttled_response = client.post(
        "/auth/login",
        data={"username": "missing@example.com", "password": "wrongpassword"},
    )
    assert throttled_response.status_code == 429


def test_ensure_dev_admin_user_is_idempotent():
    db = TestingSessionLocal()
    try:
        original_bootstrap = settings.DEV_BOOTSTRAP_ADMIN
        original_email = settings.DEV_ADMIN_EMAIL
        original_password = settings.DEV_ADMIN_PASSWORD
        original_name = settings.DEV_ADMIN_NAME
        settings.DEV_BOOTSTRAP_ADMIN = True
        settings.DEV_ADMIN_EMAIL = "bootstrap@example.com"
        settings.DEV_ADMIN_PASSWORD = "BootstrapSecret123!"
        settings.DEV_ADMIN_NAME = "Bootstrap Admin"
        first = ensure_dev_admin_user(db)
        second = ensure_dev_admin_user(db)
        assert first is not None
        assert second is not None
        assert first.email == second.email
        assert first.id == second.id
    finally:
        settings.DEV_BOOTSTRAP_ADMIN = original_bootstrap
        settings.DEV_ADMIN_EMAIL = original_email
        settings.DEV_ADMIN_PASSWORD = original_password
        settings.DEV_ADMIN_NAME = original_name
        db.close()


def test_bootstrap_admin_user_creates_admin():
    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        user, action = bootstrap_admin_user(
            db,
            name="Bootstrap Admin",
            email="bootstrap-admin@example.com",
            password="BootstrapSecret123!",
        )
        assert action == "created"
        assert user.role == "admin"
    finally:
        db.close()


def test_bootstrap_admin_user_can_promote_existing_user():
    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        existing = User(
            name="Existing Interviewer",
            email="promote-me@example.com",
            password_hash=get_password_hash("InitialPassword123!"),
            role="interviewer",
        )
        db.add(existing)
        db.commit()

        user, action = bootstrap_admin_user(
            db,
            name="Promoted Admin",
            email="promote-me@example.com",
            password="NewPassword123!",
            promote_existing=True,
            reset_password=True,
        )
        assert action == "promoted"
        assert user.role == "admin"
        assert user.name == "Promoted Admin"
    finally:
        db.close()


def test_security_headers_are_present():
    client = make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert "content-security-policy" in response.headers
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_production_security_headers_tighten_csp_and_enable_hsts():
    client = make_client()
    original_env = settings.APP_ENV
    try:
        settings.APP_ENV = "production"
        response = client.get("/health")
        assert response.status_code == 200
        csp = response.headers["content-security-policy"]
        assert "script-src 'self'" in csp
        assert "'unsafe-eval'" not in csp
        assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
    finally:
        settings.APP_ENV = original_env
