from __future__ import annotations

import hashlib
import logging
import threading
import time
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from workos._errors import BadRequestError
from workos.types.user_management import User as WorkOSUser

from app.auth.schemas import InterviewerCreate
from app.auth.security import create_access_token, decode_access_token, get_password_hash
from app.auth.workos import get_workos_client
from app.config import settings
from app.models.user import User

AUTHKIT_PLACEHOLDER_PASSWORD = "authkit-disabled-local-password"
INTERVIEWER_ACCESS_STATES = {"invited", "active", "deactivated"}
logger = logging.getLogger(__name__)

# ─── Session refresh concurrency guard ────────────────────────────────────────
# WorkOS treats simultaneous use of the same refresh token as a security event
# and may revoke the session. When the access token expires and multiple
# concurrent requests all try session.refresh() at once, we serialize the
# actual WorkOS call per session and reuse the result within a short window.

_REFRESH_CACHE: dict[str, tuple[str, float]] = {}   # session_hash -> (new_sealed, monotonic_ts)
_REFRESH_LOCKS: dict[str, threading.Lock] = {}
_REFRESH_REGISTRY_LOCK = threading.Lock()
_REFRESH_CACHE_TTL = 15  # seconds


def _get_refresh_lock(session_hash: str) -> threading.Lock:
    with _REFRESH_REGISTRY_LOCK:
        if session_hash not in _REFRESH_LOCKS:
            _REFRESH_LOCKS[session_hash] = threading.Lock()
        return _REFRESH_LOCKS[session_hash]


def _get_cached_sealed(session_hash: str) -> str | None:
    with _REFRESH_REGISTRY_LOCK:
        entry = _REFRESH_CACHE.get(session_hash)
        if entry:
            new_sealed, ts = entry
            if time.monotonic() - ts < _REFRESH_CACHE_TTL:
                return new_sealed
            del _REFRESH_CACHE[session_hash]
    return None


def _cache_sealed(session_hash: str, new_sealed: str) -> None:
    with _REFRESH_REGISTRY_LOCK:
        _REFRESH_CACHE[session_hash] = (new_sealed, time.monotonic())


def build_profile_image_url(user: User) -> str | None:
    return user.provider_profile_image_url


def build_public_profile_image_url(user: User) -> str | None:
    return user.provider_profile_image_url


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _derive_display_name(workos_user: Any) -> str:
    first_name = (getattr(workos_user, "first_name", None) or "").strip()
    last_name = (getattr(workos_user, "last_name", None) or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()
    if full_name:
        return full_name
    email = _normalize_email(getattr(workos_user, "email", ""))
    return email.split("@", 1)[0] if email else "User"


def _coerce_workos_user(workos_user: Any) -> Any:
    if isinstance(workos_user, dict):
        return WorkOSUser.from_dict(workos_user)
    return workos_user


def _placeholder_password_hash() -> str:
    return get_password_hash(AUTHKIT_PLACEHOLDER_PASSWORD)


def create_user(
    db: Session,
    *,
    name: str,
    email: str,
    role: str,
    access_status: str = "active",
) -> User:
    normalized_email = _normalize_email(email)
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if access_status not in INTERVIEWER_ACCESS_STATES:
        raise HTTPException(status_code=400, detail="Invalid access status")

    db_user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=_placeholder_password_hash(),
        role=role,
        access_status=access_status,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_interviewer(db: Session, user_data: InterviewerCreate) -> User:
    return create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        role="interviewer",
        access_status="invited",
    )


def reactivate_interviewer(db: Session, interviewer: User) -> User:
    interviewer.access_status = "active" if interviewer.last_sign_in_at else "invited"
    db.commit()
    db.refresh(interviewer)
    return interviewer


def deactivate_interviewer(db: Session, interviewer: User) -> User:
    interviewer.access_status = "deactivated"
    db.commit()
    db.refresh(interviewer)
    return interviewer


def send_interviewer_invitation_email(*, email: str, inviter: User | None = None) -> None:
    inviter_user_id = inviter.workos_user_id if inviter and inviter.workos_user_id else None
    normalized_email = _normalize_email(email)
    try:
        get_workos_client().user_management.send_invitation(
            email=normalized_email,
            inviter_user_id=inviter_user_id,
        )
    except BadRequestError as exc:
        if getattr(exc, "code", None) == "user_already_exists":
            return
        raise


def create_admin_access(db: Session, *, name: str, email: str) -> User:
    return create_user(db, name=name, email=email, role="admin", access_status="active")


def bootstrap_admin_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    promote_existing: bool = False,
    reset_password: bool = False,
) -> tuple[User, str]:
    del password, reset_password
    normalized_email = _normalize_email(email)
    existing_user = db.query(User).filter(User.email == normalized_email).first()

    if existing_user is None:
        return create_admin_access(db, name=name, email=normalized_email), "created"

    if existing_user.role == "admin":
        changed = False
        if existing_user.name != name:
            existing_user.name = name
            changed = True
        if existing_user.access_status != "active":
            existing_user.access_status = "active"
            changed = True
        if changed:
            db.commit()
            db.refresh(existing_user)
            return existing_user, "updated"
        return existing_user, "unchanged"

    if not promote_existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists with a non-admin role. Re-run with promote_existing enabled.",
        )

    existing_user.role = "admin"
    existing_user.name = name
    existing_user.access_status = "active"
    db.commit()
    db.refresh(existing_user)
    return existing_user, "promoted"


def build_session_token(user: User) -> str:
    token_data = {"sub": user.email, "role": user.role}
    return create_access_token(data=token_data)


def _upsert_founder_admin(db: Session, *, workos_user: Any) -> User:
    founder_email = _normalize_email(settings.FOUNDER_ADMIN_EMAIL)
    email = _normalize_email(getattr(workos_user, "email", ""))
    if email != founder_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is not authorized for this app.")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user is None:
        user = User(
            name=_derive_display_name(workos_user),
            email=email,
            password_hash=_placeholder_password_hash(),
            role="admin",
            access_status="active",
            workos_user_id=getattr(workos_user, "id", None),
            provider_profile_image_url=getattr(workos_user, "profile_picture_url", None),
            last_sign_in_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    existing_user.role = "admin"
    existing_user.access_status = "active"
    existing_user.workos_user_id = getattr(workos_user, "id", None)
    existing_user.provider_profile_image_url = getattr(workos_user, "profile_picture_url", None)
    existing_user.last_sign_in_at = datetime.utcnow()
    if not existing_user.name:
        existing_user.name = _derive_display_name(workos_user)
    db.commit()
    db.refresh(existing_user)
    return existing_user


def sync_user_from_workos_identity(db: Session, workos_user: Any, expected_role: str | None = None) -> User:
    workos_user = _coerce_workos_user(workos_user)
    email = _normalize_email(getattr(workos_user, "email", ""))
    founder_email = _normalize_email(settings.FOUNDER_ADMIN_EMAIL)

    user = db.query(User).filter(User.email == email).first()
    if user is None and email == founder_email:
        user = _upsert_founder_admin(db, workos_user=workos_user)
    elif user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is not authorized for this app.")

    if user.access_status == "deactivated":
        logger.warning("auth.deactivated_account email=%s", email)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    if expected_role and user.role != expected_role:
        logger.warning("auth.role_mismatch email=%s expected_role=%s actual_role=%s", email, expected_role, user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account does not belong in the {expected_role} portal.",
        )

    user.workos_user_id = getattr(workos_user, "id", None)
    user.provider_profile_image_url = getattr(workos_user, "profile_picture_url", None)
    user.last_sign_in_at = datetime.utcnow()
    if user.role == "interviewer" and user.access_status == "invited":
        user.access_status = "active"
    if not user.name:
        user.name = _derive_display_name(workos_user)

    db.commit()
    db.refresh(user)
    return user


def get_current_user_from_token(token: str, db: Session) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.email == _normalize_email(email)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.role == "interviewer" and user.access_status == "deactivated":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")
    return user


def get_current_user_from_workos_session(
    db: Session,
    response: Response,
    sealed_session: str,
    *,
    refresh_session: bool = False,
) -> User:
    try:
        session = get_workos_client().user_management.load_sealed_session(
            session_data=sealed_session,
            cookie_password=settings.WORKOS_COOKIE_PASSWORD,
        )
    except Exception as exc:
        logger.warning("auth.sealed_session_load_failure error=%s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated") from exc

    try:
        auth_response = session.authenticate()
        if auth_response.authenticated:
            if refresh_session:
                try:
                    refresh_response = session.refresh()
                except Exception as exc:
                    logger.exception(
                        "auth.proactive_refresh_exception error=%s",
                        exc.__class__.__name__,
                    )
                else:
                    if refresh_response.authenticated:
                        logger.info("auth.refresh_succeeded mode=proactive")
                        response.set_cookie(
                            key=settings.SESSION_COOKIE_NAME,
                            value=refresh_response.sealed_session,
                            httponly=True,
                            secure=settings.APP_ENV == "production",
                            samesite=settings.SESSION_COOKIE_SAMESITE,
                            path="/",
                        )
                        return sync_user_from_workos_identity(db, refresh_response.user)
                    logger.warning(
                        "auth.proactive_refresh_failed reason=%s",
                        getattr(refresh_response, "reason", "unknown"),
                    )
            return sync_user_from_workos_identity(db, auth_response.user)

        # ── Token expired: refresh with concurrency guard ─────────────────
        # Concurrent requests sharing the same expired sealed session must not
        # all call session.refresh() simultaneously — WorkOS detects refresh-
        # token reuse and revokes the session as a security measure.
        session_hash = hashlib.sha256(sealed_session[:128].encode()).hexdigest()

        def _apply_sealed(sealed: str) -> User | None:
            """Load a refreshed sealed session and return the user if still valid."""
            try:
                refreshed = get_workos_client().user_management.load_sealed_session(
                    session_data=sealed,
                    cookie_password=settings.WORKOS_COOKIE_PASSWORD,
                )
                auth = refreshed.authenticate()
                if auth.authenticated:
                    response.set_cookie(
                        key=settings.SESSION_COOKIE_NAME,
                        value=sealed,
                        httponly=True,
                        secure=settings.APP_ENV == "production",
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                        path="/",
                    )
                    return sync_user_from_workos_identity(db, auth.user)
            except Exception:
                pass
            return None

        # Fast path: another request already refreshed this session.
        cached = _get_cached_sealed(session_hash)
        if cached:
            user = _apply_sealed(cached)
            if user:
                logger.info("auth.refresh_cache_hit")
                return user

        # Slow path: acquire per-session lock so only ONE WorkOS refresh call
        # is made regardless of how many concurrent requests share this session.
        refresh_lock = _get_refresh_lock(session_hash)
        with refresh_lock:
            # Double-check after acquiring the lock — another thread may have
            # already refreshed while we were waiting.
            cached = _get_cached_sealed(session_hash)
            if cached:
                user = _apply_sealed(cached)
                if user:
                    logger.info("auth.refresh_cache_hit_after_lock")
                    return user

            try:
                refresh_response = session.refresh()
            except Exception as exc:
                logger.exception("auth.provider_refresh_exception error=%s", exc.__class__.__name__)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable",
                ) from exc

            if not refresh_response.authenticated:
                logger.info("auth.refresh_failed")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

            logger.info("auth.refresh_succeeded")
            new_sealed = refresh_response.sealed_session
            _cache_sealed(session_hash, new_sealed)
            response.set_cookie(
                key=settings.SESSION_COOKIE_NAME,
                value=new_sealed,
                httponly=True,
                secure=settings.APP_ENV == "production",
                samesite=settings.SESSION_COOKIE_SAMESITE,
                path="/",
            )
            return sync_user_from_workos_identity(db, refresh_response.user)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("auth.authenticate_unexpected_failure error=%s", exc.__class__.__name__)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service unavailable") from exc


def get_logout_url(sealed_session: str | None) -> str | None:
    if not sealed_session:
        return None
    try:
        session = get_workos_client().user_management.load_sealed_session(
            session_data=sealed_session,
            cookie_password=settings.WORKOS_COOKIE_PASSWORD,
        )
        return session.get_logout_url(return_to=settings.WORKOS_LOGOUT_REDIRECT_URI)
    except Exception:
        return None


def ensure_dev_admin_user(db: Session) -> User | None:
    if settings.APP_ENV != "development" or not settings.DEV_BOOTSTRAP_ADMIN:
        return None

    existing_user = db.query(User).filter(User.email == _normalize_email(settings.DEV_ADMIN_EMAIL)).first()
    if existing_user:
        if existing_user.role != "admin":
            existing_user.role = "admin"
            existing_user.access_status = "active"
            db.commit()
            db.refresh(existing_user)
        return existing_user

    admin_user = User(
        name=settings.DEV_ADMIN_NAME,
        email=_normalize_email(settings.DEV_ADMIN_EMAIL),
        password_hash=_placeholder_password_hash(),
        role="admin",
        access_status="active",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user
