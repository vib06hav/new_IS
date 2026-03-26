from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.auth.service import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = register_user(db, user_data)
    # The Pydantic model response expects ID as str, which works since UUID auto-converts
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_data = UserLogin(email=form_data.username, password=form_data.password)
    token = authenticate_user(db, user_data)
    return {"access_token": token, "token_type": "bearer"}
