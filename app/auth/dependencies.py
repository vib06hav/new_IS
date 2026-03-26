from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.service import get_current_user_from_token
from app.database import get_db
from app.models.assignment import Assignment
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
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
