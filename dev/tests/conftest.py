import os

import pytest

os.environ.setdefault("JWT_SECRET", "test-jwt-secret-with-adequate-entropy-1234567890")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("LLM_DISABLE_LIVE_CALLS", "true")
os.environ.setdefault("SESSION_COOKIE_NAME", "agis_session")
os.environ.setdefault("SESSION_COOKIE_SAMESITE", "lax")
os.environ.setdefault("CSRF_COOKIE_NAME", "agis_csrf")
os.environ.setdefault("CSRF_HEADER_NAME", "X-CSRF-Token")
os.environ.setdefault("DEV_BOOTSTRAP_ADMIN", "false")
os.environ.setdefault("WORKOS_API_KEY", "sk_test_workos")
os.environ.setdefault("WORKOS_CLIENT_ID", "client_test_workos")
os.environ.setdefault("WORKOS_COOKIE_PASSWORD", "test-workos-cookie-password-1234567890")
os.environ.setdefault("WORKOS_REDIRECT_URI", "http://testserver/auth/callback")
os.environ.setdefault("WORKOS_LOGOUT_REDIRECT_URI", "http://testserver/")
os.environ.setdefault("FOUNDER_ADMIN_EMAIL", "founder@example.com")

from app.security.rate_limit import limiter


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    limiter.clear()
    yield
    limiter.clear()
