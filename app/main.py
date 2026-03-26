from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import logging

from app.config import settings
logging.getLogger().setLevel(settings.LOG_LEVEL)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.info("Application startup success")

import app.models
from app.database import get_db
from app.database import SessionLocal
from app.auth.router import router as auth_router
from app.auth.service import ensure_dev_admin_user
from app.api.admin import router as admin_router
from app.api.applications import router as applications_router
from app.api.interviewer import router as interviewer_router
from app.api.users import router as users_router

app = FastAPI(title="Interview Standardiser API", version="0.1.0")

app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(admin_router)
app.include_router(interviewer_router)
app.include_router(users_router)

from sqlalchemy import text


@app.on_event("startup")
def bootstrap_dev_admin():
    db = SessionLocal()
    try:
        user = ensure_dev_admin_user(db)
        if user:
            logger.info("Development admin available at %s", user.email)
    finally:
        db.close()

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Simply running a query to verify db connection is alive
    db.execute(text("SELECT 1"))
    return {"status": "ok", "message": "Service is healthy and database is reachable."}
