from datetime import datetime
from types import SimpleNamespace

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
from app.security.rate_limit import limiter


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


class FakeWorkOSUser:
    def __init__(self, *, user_id: str, email: str, first_name: str = "Test", last_name: str = "User"):
        self.id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.profile_picture_url = f"https://images.example/{user_id}.png"


class FakeLoadedSession:
    def __init__(self, user, sealed_session: str, refresh_counter: dict[str, int]):
        self.user = user
        self.sealed_session = sealed_session
        self._refresh_counter = refresh_counter

    def authenticate(self):
        return SimpleNamespace(authenticated=True, user=self.user)

    def refresh(self):
        self._refresh_counter[self.sealed_session] = self._refresh_counter.get(self.sealed_session, 0) + 1
        return SimpleNamespace(authenticated=True, user=self.user, sealed_session=f"{self.sealed_session}-refreshed")

    def get_logout_url(self, return_to=None):
        return return_to or "http://testserver/"


class FakeUserManagement:
    def __init__(self, codes_to_users: dict[str, FakeWorkOSUser]):
        self.codes_to_users = codes_to_users
        self.sessions: dict[str, FakeWorkOSUser] = {}
        self.sent_invitations: list[dict[str, str | None]] = []
        self.refresh_counts: dict[str, int] = {}

    def authenticate_with_code(self, *, code, session):
        del session
        user = self.codes_to_users[code]
        sealed_session = f"sealed-{code}"
        self.sessions[sealed_session] = user
        return SimpleNamespace(user=user, sealed_session=sealed_session)

    def load_sealed_session(self, *, session_data, cookie_password):
        del cookie_password
        user = self.sessions[session_data]
        return FakeLoadedSession(user, session_data, self.refresh_counts)

    def send_invitation(self, *, email, organization_id=None, role_slug=None, expires_in_days=None, inviter_user_id=None, locale=None, request_options=None):
        del organization_id, role_slug, expires_in_days, locale, request_options
        self.sent_invitations.append({"email": email, "inviter_user_id": inviter_user_id})
        return SimpleNamespace(email=email, inviter_user_id=inviter_user_id)


class FakeWorkOSClient:
    def __init__(self, codes_to_users: dict[str, FakeWorkOSUser]):
        self.user_management = FakeUserManagement(codes_to_users)


def install_fake_workos(monkeypatch, codes_to_users: dict[str, FakeWorkOSUser]):
    fake_client = FakeWorkOSClient(codes_to_users)
    monkeypatch.setattr("app.auth.workos.get_workos_client", lambda: fake_client)
    monkeypatch.setattr("app.auth.service.get_workos_client", lambda: fake_client)
    return fake_client


def test_admin_can_invite_interviewer():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-invite@example.com",
        password_hash="x",
        role="admin",
        access_status="active",
    )
    db.add(admin)
    db.commit()

    from app.api import users as users_api

    sent_invites: list[tuple[str, str | None]] = []

    def fake_send_invitation_email(*, email: str, inviter: User | None = None):
        sent_invites.append((email, inviter.workos_user_id if inviter else None))

    original_send = users_api.send_interviewer_invitation_email
    users_api.send_interviewer_invitation_email = fake_send_invitation_email
    try:
        response = client.post(
        "/users/interviewers",
        json={"name": "Invited Interviewer", "email": "invitee@example.com"},
        headers=auth_headers(admin.email, admin.role),
        )
    finally:
        users_api.send_interviewer_invitation_email = original_send

    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "interviewer"
    assert data["access_status"] == "invited"
    assert sent_invites == [("invitee@example.com", None)]


def test_admin_invite_uses_workos_inviter_when_available():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-workos@example.com",
        password_hash="x",
        role="admin",
        access_status="active",
        workos_user_id="workos-admin-1",
    )
    db.add(admin)
    db.commit()

    from app.api import users as users_api

    sent_invites: list[tuple[str, str | None]] = []

    def fake_send_invitation_email(*, email: str, inviter: User | None = None):
        sent_invites.append((email, inviter.workos_user_id if inviter else None))

    original_send = users_api.send_interviewer_invitation_email
    users_api.send_interviewer_invitation_email = fake_send_invitation_email
    try:
        response = client.post(
            "/users/interviewers",
            json={"name": "Invited Interviewer", "email": "invitee-workos@example.com"},
            headers=auth_headers(admin.email, admin.role),
        )
    finally:
        users_api.send_interviewer_invitation_email = original_send

    assert response.status_code == 201
    assert sent_invites == [("invitee-workos@example.com", "workos-admin-1")]


def test_admin_can_reactivate_interviewer():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-reactivate@example.com",
        password_hash="x",
        role="admin",
        access_status="active",
    )
    interviewer = User(
        name="Dormant Interviewer",
        email="dormant@example.com",
        password_hash="x",
        role="interviewer",
        access_status="deactivated",
    )
    db.add(admin)
    db.add(interviewer)
    db.commit()

    response = client.post(
        f"/users/interviewers/{interviewer.id}/reactivate",
        headers=auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 200
    assert response.json()["access_status"] == "invited"


def test_admin_reactivation_restores_active_for_previously_signed_in_interviewer():
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    admin = User(
        name="Admin",
        email="admin-reactivate-active@example.com",
        password_hash="x",
        role="admin",
        access_status="active",
    )
    interviewer = User(
        name="Signed In Interviewer",
        email="signed-in@example.com",
        password_hash="x",
        role="interviewer",
        access_status="deactivated",
        last_sign_in_at=datetime.utcnow(),
    )
    db.add(admin)
    db.add(interviewer)
    db.commit()

    response = client.post(
        f"/users/interviewers/{interviewer.id}/reactivate",
        headers=auth_headers(admin.email, admin.role),
    )

    assert response.status_code == 200
    assert response.json()["access_status"] == "active"


def test_founder_callback_bootstraps_admin(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"founder-code": FakeWorkOSUser(user_id="founder-1", email=settings.FOUNDER_ADMIN_EMAIL, first_name="Founder", last_name="Admin")},
    )

    response = client.get(
        "/auth/callback",
        params={"code": "founder-code", "state": "eyJwb3J0YWwiOiJhZG1pbiJ9"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin/reports")
    assert response.cookies.get(settings.SESSION_COOKIE_NAME)

    db = TestingSessionLocal()
    founder = db.query(User).filter(User.email == settings.FOUNDER_ADMIN_EMAIL).first()
    assert founder is not None
    assert founder.role == "admin"
    assert founder.access_status == "active"
    assert founder.workos_user_id == "founder-1"
    db.close()


def test_invited_interviewer_activates_on_first_login(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    invited = User(
        name="Invited Interviewer",
        email="invited@example.com",
        password_hash="x",
        role="interviewer",
        access_status="invited",
    )
    db.add(invited)
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"invite-code": FakeWorkOSUser(user_id="workos-invite", email="invited@example.com")},
    )

    response = client.get(
        "/auth/callback",
        params={"code": "invite-code", "state": "eyJwb3J0YWwiOiJpbnRlcnZpZXdlciJ9"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("/interviewer/dashboard")

    db = TestingSessionLocal()
    interviewer = db.query(User).filter(User.email == "invited@example.com").first()
    assert interviewer is not None
    assert interviewer.access_status == "active"
    assert interviewer.workos_user_id == "workos-invite"
    db.close()


def test_uninvited_identity_is_denied(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"stranger-code": FakeWorkOSUser(user_id="stranger-1", email="stranger@example.com")},
    )

    response = client.get(
        "/auth/callback",
        params={"code": "stranger-code", "state": "eyJwb3J0YWwiOiJpbnRlcnZpZXdlciJ9"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/interviewer/login?error=" in response.headers["location"]


def test_deactivated_interviewer_cannot_access_session(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    interviewer = User(
        name="Disabled Interviewer",
        email="disabled@example.com",
        password_hash="x",
        role="interviewer",
        access_status="deactivated",
    )
    db.add(interviewer)
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"disabled-code": FakeWorkOSUser(user_id="disabled-1", email="disabled@example.com")},
    )

    login_response = client.get(
        "/auth/callback",
        params={"code": "disabled-code", "state": "eyJwb3J0YWwiOiJpbnRlcnZpZXdlciJ9"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302
    assert "/interviewer/login?error=" in login_response.headers["location"]


def test_cookie_session_requires_csrf_header_for_mutations(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"founder-code": FakeWorkOSUser(user_id="founder-2", email=settings.FOUNDER_ADMIN_EMAIL)},
    )

    login_response = client.get(
        "/auth/callback",
        params={"code": "founder-code", "state": "eyJwb3J0YWwiOiJhZG1pbiJ9"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    response = client.post(
        "/users/interviewers",
        json={"name": "Blocked Invite", "email": "blocked-csrf@example.com"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing trusted request origin"


def test_cookie_session_mutation_succeeds_with_matching_csrf_header(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"founder-code": FakeWorkOSUser(user_id="founder-3", email=settings.FOUNDER_ADMIN_EMAIL)},
    )

    login_response = client.get(
        "/auth/callback",
        params={"code": "founder-code", "state": "eyJwb3J0YWwiOiJhZG1pbiJ9"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    response = client.post(
        "/users/interviewers",
        json={"name": "Allowed Invite", "email": "allowed-csrf@example.com"},
        headers=session_csrf_headers(client),
    )

    assert response.status_code == 201
    assert response.json()["access_status"] == "invited"


def test_session_endpoint_can_proactively_refresh_cookie(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    fake_client = install_fake_workos(
        monkeypatch,
        {"founder-code": FakeWorkOSUser(user_id="founder-5", email=settings.FOUNDER_ADMIN_EMAIL)},
    )

    login_response = client.get(
        "/auth/callback",
        params={"code": "founder-code", "state": "eyJwb3J0YWwiOiJhZG1pbiJ9"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302

    original_cookie = client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert original_cookie == "sealed-founder-code"

    response = client.get("/auth/session", params={"refresh": "true"})

    assert response.status_code == 200
    assert client.cookies.get(settings.SESSION_COOKIE_NAME) == "sealed-founder-code-refreshed"
    assert fake_client.user_management.refresh_counts[original_cookie] == 1


def test_logout_clears_session_cookie_and_returns_logout_url(monkeypatch):
    client = make_client()
    db = TestingSessionLocal()
    db.query(User).delete()
    db.commit()
    db.close()

    install_fake_workos(
        monkeypatch,
        {"founder-code": FakeWorkOSUser(user_id="founder-4", email=settings.FOUNDER_ADMIN_EMAIL)},
    )

    login_response = client.get(
        "/auth/callback",
        params={"code": "founder-code", "state": "eyJwb3J0YWwiOiJhZG1pbiJ9"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302
    assert client.cookies.get(settings.SESSION_COOKIE_NAME)

    response = client.post("/auth/logout", headers=session_csrf_headers(client))

    assert response.status_code == 200
    assert response.json()["logout_url"] == settings.WORKOS_LOGOUT_REDIRECT_URI


def test_ensure_dev_admin_user_is_idempotent():
    from app.auth.service import ensure_dev_admin_user

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


def test_bootstrap_admin_user_can_promote_existing_user():
    from app.auth.service import bootstrap_admin_user

    db = TestingSessionLocal()
    try:
        db.query(User).delete()
        existing = User(
            name="Existing Interviewer",
            email="promote-me@example.com",
            password_hash="x",
            role="interviewer",
            access_status="active",
        )
        db.add(existing)
        db.commit()

        user, action = bootstrap_admin_user(
            db,
            name="Promoted Admin",
            email="promote-me@example.com",
            password="ignored",
            promote_existing=True,
            reset_password=True,
        )
        assert action == "promoted"
        assert user.role == "admin"
        assert user.access_status == "active"
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
        limiter.clear()
