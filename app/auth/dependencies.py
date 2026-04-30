import logging

from fastapi import Cookie, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.service import get_current_user_from_token, get_current_user_from_workos_session
from app.config import settings
from app.database import get_db
from app.models.assignment import Assignment
from app.models.user import User

logger = logging.getLogger(__name__)


def get_current_user(
    request: Request,
    response: Response,
    session_token: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    refresh_session: bool = Query(default=False, alias="refresh"),
    db: Session = Depends(get_db),
) -> User:
    if session_token:
        return get_current_user_from_workos_session(
            db,
            response,
            session_token,
            refresh_session=refresh_session,
        )

    token: str | None = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        if not settings.ENABLE_BEARER_TOKEN_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token authentication is disabled",
            )
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        logger.info("auth.no_session_cookie_or_bearer")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return get_current_user_from_token(token, db)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_interviewer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "interviewer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Interviewer access required")
    return current_user


def require_assigned_interviewer(
    application_id,
    current_user: User,
    db: Session,
) -> User:
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.application_id == application_id,
            Assignment.interviewer_id == current_user.id,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not assigned to this application")
    return current_user
