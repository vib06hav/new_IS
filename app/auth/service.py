from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.auth.schemas import (
    AdminPasswordChange,
    InterviewerCreate,
    InterviewerUpdate,
    SelfPasswordChange,
    SelfProfileUpdate,
    UserCreate,
    UserLogin,
)
from app.auth.security import get_password_hash, verify_password, create_access_token
from app.config import settings

def create_user(db: Session, *, name: str, email: str, password: str, role: str) -> User:
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)
    db_user = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def register_user(db: Session, user_data: UserCreate):
    return create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
    )


def create_interviewer(db: Session, user_data: InterviewerCreate) -> User:
    return create_user(
        db,
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role="interviewer",
    )


def update_interviewer(db: Session, interviewer: User, user_data: InterviewerUpdate) -> User:
    existing_user = db.query(User).filter(User.email == user_data.email, User.id != interviewer.id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    interviewer.name = user_data.name
    interviewer.email = user_data.email
    db.commit()
    db.refresh(interviewer)
    return interviewer


def admin_set_user_password(db: Session, user: User, password_data: AdminPasswordChange) -> User:
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, password_data: SelfPasswordChange) -> User:
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if verify_password(password_data.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    db.refresh(user)
    return user


def update_self_profile(db: Session, user: User, profile_data: SelfProfileUpdate) -> User:
    user.name = profile_data.name.strip()
    db.commit()
    db.refresh(user)
    return user


def create_admin(db: Session, *, name: str, email: str, password: str) -> User:
    return create_user(
        db,
        name=name,
        email=email,
        password=password,
        role="admin",
    )


def bootstrap_admin_user(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    promote_existing: bool = False,
    reset_password: bool = False,
) -> tuple[User, str]:
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user is None:
        return create_admin(db, name=name, email=email, password=password), "created"

    if existing_user.role == "admin":
        changed = False
        if existing_user.name != name:
            existing_user.name = name
            changed = True
        if reset_password:
            existing_user.password_hash = get_password_hash(password)
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
    if reset_password:
        existing_user.password_hash = get_password_hash(password)
    db.commit()
    db.refresh(existing_user)
    return existing_user, "promoted"

def authenticate_user(db: Session, user_data: UserLogin) -> User:
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return user


def build_session_token(user: User) -> str:
    token_data = {"sub": user.email, "role": user.role}
    return create_access_token(data=token_data)

def get_current_user_from_token(token: str, db: Session):
    from app.auth.security import decode_access_token # Avoid circular dependency if added later
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
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def ensure_dev_admin_user(db: Session) -> User | None:
    if settings.APP_ENV != "development" or not settings.DEV_BOOTSTRAP_ADMIN:
        return None

    existing_user = db.query(User).filter(User.email == settings.DEV_ADMIN_EMAIL).first()
    if existing_user:
        return existing_user

    admin_user = User(
        name=settings.DEV_ADMIN_NAME,
        email=settings.DEV_ADMIN_EMAIL,
        password_hash=get_password_hash(settings.DEV_ADMIN_PASSWORD),
        role="admin",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user
