from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import SelfPasswordChange, SelfProfileUpdate, SessionResponse, SessionUser, UserCreate, UserLogin, UserResponse
from app.auth.service import authenticate_user, build_session_token, change_password, register_user, update_self_profile
from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.models.user import User
from app.security.csrf import clear_csrf_cookie, generate_csrf_token, set_csrf_cookie
from app.security.rate_limit import client_ip, limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_data.role != "interviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only interviewer accounts can be created through this endpoint",
        )
    user = register_user(db, user_data)
    # The Pydantic model response expects ID as str, which works since UUID auto-converts
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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


@router.post("/login", response_model=SessionResponse)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ip = client_ip(request)
    identifier = form_data.username.strip().lower()
    limiter.check(
        f"login:ip:{ip}",
        limit=10,
        window_seconds=60,
        detail="Too many login attempts from this IP. Please retry shortly.",
    )
    limiter.check(
        f"login:user:{identifier}",
        limit=5,
        window_seconds=60,
        detail="Too many login attempts for this account. Please retry shortly.",
    )
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    user = authenticate_user(db, user_data)
    session_token = build_session_token(user)
    csrf_token = generate_csrf_token()
    _set_session_cookie(response, session_token)
    set_csrf_cookie(response, csrf_token)
    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
    }


@router.get("/session", response_model=SessionResponse)
def get_session(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    return {
        "user": SessionUser(
            id=str(current_user.id),
            name=current_user.name,
            email=current_user.email,
            role=current_user.role,
        )
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    _clear_session_cookie(response)
    clear_csrf_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.put("/change-password", response_model=SessionResponse)
def update_my_password(
    payload: SelfPasswordChange,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = change_password(db, current_user, payload)
    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    return {
        "user": SessionUser(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
        )
    }


@router.put("/profile", response_model=SessionResponse)
def update_my_profile(
    payload: SelfProfileUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = update_self_profile(db, current_user, payload)
    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    return {
        "user": SessionUser(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
        )
    }
