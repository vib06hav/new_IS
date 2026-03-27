import secrets
from hmac import compare_digest
from urllib.parse import urlsplit

from fastapi import HTTPException, Request, Response, status

from app.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
EXEMPT_PATHS = {"/auth/login"}


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.APP_ENV == "production",
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        secure=settings.APP_ENV == "production",
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )


def request_uses_session_cookie(request: Request) -> bool:
    if request.method in SAFE_METHODS or request.url.path in EXEMPT_PATHS:
        return False

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return False

    return bool(request.cookies.get(settings.SESSION_COOKIE_NAME))


def ensure_csrf_protection(request: Request) -> None:
    if not request_uses_session_cookie(request):
        return

    allowed_origins = _allowed_origins(request)
    request_origin = request.headers.get("origin")
    if request_origin:
        if request_origin not in allowed_origins and not _is_allowed_loopback_origin(request_origin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin")
    else:
        referer = request.headers.get("referer")
        if not referer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing trusted request origin")
        referer_origin = _origin_from_url(referer)
        if referer_origin not in allowed_origins and not _is_allowed_loopback_origin(referer_origin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin")

    csrf_cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
    csrf_header = request.headers.get(settings.CSRF_HEADER_NAME)
    if not csrf_cookie or not csrf_header or not compare_digest(csrf_cookie, csrf_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def _origin_from_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _allowed_origins(request: Request) -> set[str]:
    return {
        _origin_from_url(str(request.base_url)),
        *settings.CSRF_TRUSTED_ORIGINS,
    }


def _is_allowed_loopback_origin(origin: str) -> bool:
    if settings.APP_ENV != "development":
        return False
    parsed = urlsplit(origin)
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
