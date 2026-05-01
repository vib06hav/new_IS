from __future__ import annotations

import base64
import inspect
import json
import secrets
from urllib.parse import urlencode, urljoin
from functools import lru_cache
from typing import Literal

from fastapi import HTTPException, status
from workos.session import seal_session_from_auth_response
from workos import WorkOSClient
from workos.types.user_management import User as WorkOSUser

from app.config import settings

PortalRole = Literal["admin", "interviewer"]
OAUTH_STATE_COOKIE_NAME = "agis_oauth_state"


@lru_cache(maxsize=1)
def get_workos_client() -> WorkOSClient:
    return WorkOSClient(api_key=settings.WORKOS_API_KEY, client_id=settings.WORKOS_CLIENT_ID)


def build_state(role: PortalRole, nonce: str) -> str:
    payload = {"portal": role, "nonce": nonce}
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("utf-8")


def generate_oauth_state(role: PortalRole) -> str:
    return build_state(role, secrets.token_urlsafe(32))


def parse_state(value: str | None) -> tuple[PortalRole, str]:
    if not value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing login state")
    try:
        decoded = base64.urlsafe_b64decode(value.encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as exc:  # pragma: no cover - defensive input guard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login state") from exc
    portal = payload.get("portal")
    nonce = payload.get("nonce")
    if portal not in {"admin", "interviewer"} or not isinstance(nonce, str) or not nonce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid login state")
    return portal, nonce


def get_authorization_url(role: PortalRole, state: str) -> str:
    client = get_workos_client()
    return client.user_management.get_authorization_url(
        provider="authkit",
        redirect_uri=settings.WORKOS_REDIRECT_URI,
        state=state,
    )


def authenticate_with_code_and_seal(code: str) -> tuple[WorkOSUser, str]:
    client = get_workos_client()
    authenticate = client.user_management.authenticate_with_code
    params = inspect.signature(authenticate).parameters

    # Backward-compatible path used by local tests/fakes that model the older SDK call shape.
    if "session" in params:
        response = authenticate(
            code=code,
            session={"seal_session": True, "cookie_password": settings.WORKOS_COOKIE_PASSWORD},
        )
        return response.user, response.sealed_session

    response = client.request_raw(
        method="post",
        path="user_management/authenticate",
        body={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.WORKOS_CLIENT_ID,
            "client_secret": settings.WORKOS_API_KEY,
            "session": {
                "seal_session": True,
                "cookie_password": settings.WORKOS_COOKIE_PASSWORD,
            },
        },
    )
    sealed_session = response.get("sealed_session")
    if not sealed_session:
        sealed_session = seal_session_from_auth_response(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            user=response["user"],
            impersonator=response.get("impersonator"),
            cookie_password=settings.WORKOS_COOKIE_PASSWORD,
        )
    return WorkOSUser.from_dict(response["user"]), str(sealed_session)


def build_error_redirect(role: PortalRole, error: str) -> str:
    path = "/admin/login" if role == "admin" else "/interviewer/login"
    return build_frontend_url(path, error=error)


def build_frontend_url(path: str, **query: str) -> str:
    base = settings.WORKOS_LOGOUT_REDIRECT_URI.rstrip("/") + "/"
    target = urljoin(base, path.lstrip("/"))
    if query:
        return f"{target}?{urlencode(query)}"
    return target
