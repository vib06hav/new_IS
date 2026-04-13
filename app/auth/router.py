import imghdr
import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import SelfPasswordChange, SelfProfileUpdate, SessionResponse, SessionUser, UserCreate, UserLogin, UserResponse
from app.auth.service import (
    authenticate_user,
    build_profile_image_url,
    build_session_token,
    change_password,
    register_user,
    update_self_profile,
)
from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.models.user import User
from app.security.csrf import clear_csrf_cookie, generate_csrf_token, set_csrf_cookie
from app.security.rate_limit import client_ip, limiter
from app.storage import get_storage_service, storage_key_for_profile_image

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_PROFILE_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _build_session_response(user: User) -> SessionResponse:
    return SessionResponse(
        user=SessionUser(
            id=str(user.id),
            name=user.name,
            email=user.email,
            role=user.role,
            profile_image_url=build_profile_image_url(user),
        )
    )

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
        "role": user.role,
        "profile_image_url": build_profile_image_url(user),
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
    return _build_session_response(user)


@router.get("/session", response_model=SessionResponse)
def get_session(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
):
    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    return _build_session_response(current_user)


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
    return _build_session_response(user)


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
    return _build_session_response(user)


@router.get("/profile/image")
def get_my_profile_image(
    current_user: User = Depends(get_current_user),
):
    if not current_user.profile_image_key or not current_user.profile_image_content_type:
        raise HTTPException(status_code=404, detail="Profile image not found")

    storage = get_storage_service()
    if not storage.exists(current_user.profile_image_key):
        raise HTTPException(status_code=404, detail="Profile image not found")

    handle_context = storage.open_stream(current_user.profile_image_key)
    handle = handle_context.__enter__()

    def iterator():
        try:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            handle_context.__exit__(None, None, None)

    return StreamingResponse(iterator(), media_type=current_user.profile_image_content_type)


@router.post("/profile/image", response_model=SessionResponse)
def upload_my_profile_image(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_PROFILE_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WEBP profile images are supported")

    max_bytes = settings.MAX_PROFILE_IMAGE_SIZE_MB * 1024 * 1024
    bytes_written = 0
    temp_dir = Path(settings.UPLOAD_DIRECTORY)
    temp_dir.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_PROFILE_IMAGE_TYPES[content_type]
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}", dir=temp_dir) as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded image exceeds the {settings.MAX_PROFILE_IMAGE_SIZE_MB} MB limit",
                    )
                temp_file.write(chunk)
    finally:
        file.file.close()

    try:
        detected_kind = imghdr.what(temp_path)
        expected_kind = "jpeg" if content_type == "image/jpeg" else extension
        if detected_kind != expected_kind:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid supported image")

        storage = get_storage_service()
        new_key = storage_key_for_profile_image(current_user.id, extension)
        previous_key = current_user.profile_image_key
        storage.put_file(temp_path, new_key, content_type)

        try:
            current_user.profile_image_key = new_key
            current_user.profile_image_content_type = content_type
            current_user.profile_image_updated_at = datetime.utcnow()
            db.commit()
            db.refresh(current_user)
        except Exception:
            db.rollback()
            storage.delete(new_key)
            raise

        if previous_key and previous_key != new_key:
            storage.delete(previous_key)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    if not request.cookies.get(settings.CSRF_COOKIE_NAME):
        set_csrf_cookie(response, generate_csrf_token())
    return _build_session_response(current_user)
