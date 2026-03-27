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

from app.security.rate_limit import limiter


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    limiter.clear()
    yield
    limiter.clear()
