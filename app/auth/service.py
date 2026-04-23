from __future__ import annotations

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    if expected_role and user.role != expected_role:
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
) -> User:
    try:
        if sealed_session.startswith("dev_sealed_session_"):
            role = sealed_session.split("_")[-1]
            email = "admin@example.com" if role == "admin" else "interviewer@example.com"
            user = db.query(User).filter(User.email == email).first()
            if user:
                return user
            from app.auth.service import create_user
            return create_user(db, name=f"Local {role.capitalize()}", email=email, role=role)

        session = get_workos_client().user_management.load_sealed_session(
            session_data=sealed_session,
            cookie_password=settings.WORKOS_COOKIE_PASSWORD,
        )
        auth_response = session.authenticate()
        if auth_response.authenticated:
            return sync_user_from_workos_identity(db, auth_response.user)

        refresh_response = session.refresh()
        if not refresh_response.authenticated:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=refresh_response.sealed_session,
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite=settings.SESSION_COOKIE_SAMESITE,
            path="/",
        )
        return sync_user_from_workos_identity(db, refresh_response.user)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated") from exc


def get_logout_url(sealed_session: str | None) -> str | None:
    if not sealed_session:
        return None
    try:
        if sealed_session.startswith("dev_sealed_session_"):
            return settings.WORKOS_LOGOUT_REDIRECT_URI

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
