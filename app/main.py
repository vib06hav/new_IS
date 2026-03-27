from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response
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
from app.security.csrf import ensure_csrf_protection

app = FastAPI(title="Interview Standardiser API", version="0.1.0")


@app.middleware("http")
async def enforce_csrf(request: Request, call_next):
    try:
        ensure_csrf_protection(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    script_sources = ["'self'"]
    style_sources = ["'self'", "'unsafe-inline'"]
    if settings.APP_ENV == "development":
        script_sources.extend(["'unsafe-inline'", "'unsafe-eval'"])
    csp = [
        "default-src 'self'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        f"style-src {' '.join(style_sources)}",
        f"script-src {' '.join(script_sources)}",
        "connect-src 'self' http: https: ws: wss:",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "base-uri 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response

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
