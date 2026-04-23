import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.schemas import LogoutResponse, SessionResponse, SessionUser
from app.auth.service import build_profile_image_url, get_logout_url, sync_user_from_workos_identity
from app.auth.workos import authenticate_with_code_and_seal, build_error_redirect, build_frontend_url, get_authorization_url, parse_state
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.security.csrf import clear_csrf_cookie, generate_csrf_token, set_csrf_cookie

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _build_session_response(user: User) -> SessionResponse:
    return SessionResponse(
        user=SessionUser(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            access_status=user.access_status,
            profile_image_url=build_profile_image_url(user),
        )
    )

def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )


@router.get("/login")
def login(portal: str = Query(..., pattern="^(admin|interviewer)$")):
    return RedirectResponse(url=get_authorization_url(portal))  # type: ignore[arg-type]


@router.get("/callback")
def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    portal = parse_state(state)
    if not code:
        return RedirectResponse(url=build_error_redirect(portal, "Missing authentication code"), status_code=302)

    try:
        workos_user, sealed_session = authenticate_with_code_and_seal(code)
        user = sync_user_from_workos_identity(db, workos_user, expected_role=portal)
        redirect_target = (
            build_frontend_url("/admin/reports")
            if user.role == "admin"
            else build_frontend_url("/interviewer/dashboard")
        )
        response = RedirectResponse(url=redirect_target, status_code=302)
        _set_session_cookie(response, sealed_session)
        set_csrf_cookie(response, generate_csrf_token())
        return response
    except HTTPException as exc:
        logger.warning("AuthKit login rejected for portal=%s: %s", portal, exc.detail)
        return RedirectResponse(url=build_error_redirect(portal, str(exc.detail)), status_code=302)
    except Exception:
        logger.exception("AuthKit callback failed for portal=%s", portal)
        return RedirectResponse(url=build_error_redirect(portal, "Unable to complete sign in"), status_code=302)


@router.get("/session", response_model=SessionResponse)
def get_session(
    request: Request,
    response: Response,
    portal: str | None = Query(default=None, pattern="^(admin|interviewer)$"),
    current_user: User = Depends(get_current_user),
):
    if current_user.access_status == "deactivated":
        logger.warning("auth.session.deactivated user_id=%s", current_user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    if portal and current_user.role != portal:
        logger.warning("auth.session.role_mismatch user_id=%s portal=%s role=%s", current_user.id, portal, current_user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account does not belong in the {portal} portal.",
        )

    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    logger.info("auth.session.success user_id=%s portal=%s", current_user.id, portal)
    return _build_session_response(current_user)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response):
    logout_url = get_logout_url(request.cookies.get(settings.SESSION_COOKIE_NAME))
    _clear_session_cookie(response)
    clear_csrf_cookie(response)
    return LogoutResponse(logout_url=logout_url)
