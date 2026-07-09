from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
import logging
import time
import uuid

from app.config import settings
logging.getLogger().setLevel(settings.LOG_LEVEL)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.info("Application startup success")

import app.models
from app.coordination import get_coordination_manager
from app.database import get_db
from app.database import SessionLocal
from app.auth.router import router as auth_router
from app.auth.service import ensure_dev_admin_user
from app.api.admin import router as admin_router
from app.api.applications import router as applications_router
from app.api.interviewer import router as interviewer_router
from app.api.users import router as users_router
from app.security.csrf import ensure_csrf_protection
from app.telemetry.observability import configure_observability, increment_counter, record_histogram, start_span
from app.telemetry.request_context import REQUEST_ID_HEADER, get_request_id, reset_request_id, set_request_id

app = FastAPI(title="Interview Standardiser API", version="0.1.0")
configure_observability()

if settings.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)

if settings.CORS_ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", settings.CSRF_HEADER_NAME, REQUEST_ID_HEADER],
    )


@app.middleware("http")
async def request_id_and_access_log(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
    token = set_request_id(request_id)
    started_at = time.perf_counter()
    status_code = 500
    try:
        with start_span(
            "http.request",
            {
                "http.method": request.method,
                "http.route": request.url.path,
                "request.id": request_id,
            },
        ) as span:
            response: Response = await call_next(request)
            status_code = response.status_code
            if span is not None:
                span.set_attribute("http.status_code", status_code)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
    finally:
        duration_seconds = time.perf_counter() - started_at
        duration_ms = round(duration_seconds * 1000, 2)
        metric_attributes = {
            "method": request.method,
            "route": request.url.path,
            "status": str(status_code),
        }
        increment_counter("agis_http_requests_total", attributes=metric_attributes)
        record_histogram("agis_http_request_duration_seconds", duration_seconds, attributes=metric_attributes)
        logger.info(
            "http_request method=%s path=%s status_code=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )
        reset_request_id(token)


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
    request_id = get_request_id()
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    script_sources = ["'self'", "https://cdn.jsdelivr.net"]
    style_sources = ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com"]
    font_sources = ["'self'", "data:", "https://fonts.gstatic.com"]
    img_sources = ["'self'", "data:", "blob:", "https://fastapi.tiangolo.com"]
    if settings.APP_ENV == "development":
        script_sources.extend(["'unsafe-inline'", "'unsafe-eval'"])
    csp = [
        "default-src 'self'",
        f"img-src {' '.join(img_sources)}",
        f"font-src {' '.join(font_sources)}",
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
    if settings.APP_ENV == "development":
        coordination = get_coordination_manager()
        return {
            "status": "ok",
            "coordination": "redis" if coordination.uses_redis else "in-memory",
        }
    return {"status": "ok"}


@app.get("/readiness")
def readiness_check():
    checks: dict[str, dict[str, object]] = {}

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": exc.__class__.__name__}
    finally:
        db.close()

    try:
        coordination = get_coordination_manager()
        checks["coordination"] = {
            "status": "ok",
            "backend": "redis" if coordination.uses_redis else "in-memory",
        }
    except Exception as exc:
        checks["coordination"] = {"status": "error", "detail": exc.__class__.__name__}

    checks["storage"] = {
        "status": "ok",
        "backend": settings.STORAGE_BACKEND,
        "configured": _storage_configured(),
    }

    checks["llm_config"] = {
        "status": "ok" if _llm_configured() else "degraded",
        "provider": settings.LLM_PROVIDER,
        "live_calls_disabled": settings.LLM_DISABLE_LIVE_CALLS,
    }

    checks["task_queue"] = _task_queue_readiness()
    checks["observability"] = {
        "status": "ok",
        "otel_enabled": settings.OBSERVABILITY_ENABLED,
        "otel_endpoint_configured": bool(settings.OTEL_EXPORTER_OTLP_ENDPOINT),
        "langfuse_enabled": settings.LANGFUSE_ENABLED,
        "langfuse_configured": bool(settings.LANGFUSE_HOST and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY),
    }

    overall_status = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
    return {"status": overall_status, "checks": checks}


def _llm_configured() -> bool:
    if settings.LLM_DISABLE_LIVE_CALLS:
        return True
    if settings.LLM_PROVIDER == "openrouter":
        return bool(settings.LLM_ENDPOINT and settings.LLM_MODEL_NAME and settings.LLM_API_KEY)
    if settings.LLM_PROVIDER == "aicredits":
        return bool(
            settings.AICREDITS_GENERATION_API_KEY
            and settings.AICREDITS_REPORT_CHAT_API_KEY
            and settings.AICREDITS_INTERVIEW_REFINEMENT_API_KEY
            and settings.AICREDITS_QUESTION_REGEN_API_KEY
        )
    return False


def _storage_configured() -> bool:
    if settings.STORAGE_BACKEND == "local":
        return bool(settings.UPLOAD_DIRECTORY)
    if settings.STORAGE_BACKEND == "minio":
        return bool(settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY and settings.MINIO_BUCKET)
    return False


def _task_queue_readiness() -> dict[str, object]:
    if not settings.CELERY_BROKER_URL:
        return {"status": "degraded", "backend": "none", "configured": False}
    if settings.CELERY_TASK_ALWAYS_EAGER:
        return {"status": "ok", "backend": "eager", "configured": True}
    if settings.CELERY_BROKER_URL.startswith("memory://"):
        return {"status": "ok", "backend": "memory", "configured": True}
    try:
        from redis import Redis

        client = Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
        )
        client.ping()
        return {
            "status": "ok",
            "backend": "redis",
            "configured": True,
            "queues": {
                "processing": settings.CELERY_QUEUE_PROCESSING,
                "generation": settings.CELERY_QUEUE_GENERATION,
                "maintenance": settings.CELERY_QUEUE_MAINTENANCE,
            },
        }
    except Exception as exc:
        return {
            "status": "error",
            "backend": "redis",
            "configured": True,
            "detail": exc.__class__.__name__,
        }
