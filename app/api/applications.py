import os
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
import fitz
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.helpers import (
    build_admin_detail,
    build_interviewer_detail,
    build_review_package_summary,
    get_application_or_404,
    get_assignment_for_application,
    get_canonical_record,
    get_final_report,
    get_interview_workspace,
)
from app.api.schemas import (
    ApplicationDetailAdmin,
    ApplicationDetailInterviewer,
    ApplicationUploadResponse,
    ReportChatRequest,
    ReportChatResponse,
)
from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.final_report_exports import final_report_export_stream, FINAL_REPORT_EXPORT_CONTENT_TYPE
from app.models.application import Application
from app.models.user import User
from app.processing import enqueue_processing_job
from app.report_chat import (
    ReportChatError,
    answer_report_question,
    build_report_chat_context,
    validate_report_chat_question,
)
from app.security.rate_limit import limiter
from app.storage import get_storage_service, storage_key_for_source_pdf

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


def _handle_application_insert_integrity_error(exc: IntegrityError) -> HTTPException:
    constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    if constraint_name == "uq_applications_display_id":
        return HTTPException(status_code=409, detail="Application display ID already exists")
    logger.exception("Application insert failed due to an unexpected integrity error", exc_info=exc)
    return HTTPException(status_code=500, detail="Failed to create application record")


def derive_display_id(filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        return filename[:-4]
    return filename


def validate_uploaded_pdf(file_path: str) -> None:
    try:
        with fitz.open(file_path) as document:
            if document.page_count == 0:
                raise HTTPException(status_code=400, detail="Uploaded PDF has no pages")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF") from exc


def write_upload_with_limit(file: UploadFile, file_path: str, max_size_mb: int | None = None) -> None:
    max_bytes = (max_size_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    bytes_written = 0
    try:
        with open(file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded file exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
                    )
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    finally:
        file.file.close()


@contextmanager
def staged_upload_file(file: UploadFile, suffix: str, max_size_mb: int):
    temp_dir = Path(settings.UPLOAD_DIRECTORY)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as temp_file:
            temp_path = temp_file.name
        write_upload_with_limit(file, temp_path, max_size_mb=max_size_mb)
        yield temp_path
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/upload", response_model=ApplicationUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_application(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    display_id = derive_display_id(file.filename)
    if not display_id:
        raise HTTPException(status_code=400, detail="Uploaded PDF filename must produce a non-empty display ID")
    existing_application = db.query(Application).filter(Application.display_id == display_id).first()
    if existing_application:
        raise HTTPException(status_code=409, detail="Application display ID already exists")

    application_id = uuid.uuid4()
    storage = get_storage_service()
    storage_key = storage_key_for_source_pdf(application_id)

    limiter.check(
        f"upload:{current_user.id}",
        limit=10,
        window_seconds=60,
        detail="Upload rate limit exceeded. Please wait before uploading again.",
    )

    with staged_upload_file(file, ".pdf", settings.MAX_UPLOAD_SIZE_MB) as staged_file_path:
        validate_uploaded_pdf(staged_file_path)
        storage.put_file(staged_file_path, storage_key, "application/pdf")

    db_app = Application(
        id=application_id,
        display_id=display_id,
        uploaded_by=current_user.id,
        storage_key=storage_key,
        status="PROCESSING",
    )
    db.add(db_app)
    try:
        enqueue_processing_job(db, application_id)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        storage.delete(storage_key)
        raise _handle_application_insert_integrity_error(exc) from exc
    db.refresh(db_app)
    logger.info("Upload queued for background processing for %s", application_id)
    return ApplicationUploadResponse(
        id=db_app.id,
        display_id=db_app.display_id,
        status=db_app.status,
        created_at=db_app.created_at,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailAdmin | ApplicationDetailInterviewer,
)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)
    assigned_user = None
    if assignment:
        assigned_user = db.query(User).filter(User.id == assignment.interviewer_id).first()

    canonical_record = get_canonical_record(db, application_id)
    review_package = build_review_package_summary(application, canonical_record)
    interview_workspace = get_interview_workspace(db, application_id)

    if current_user.role == "admin":
        final_report = get_final_report(db, application_id)
        return build_admin_detail(application, assigned_user, review_package, final_report, interview_workspace)

    if not assignment or assignment.interviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this application")

    final_report = get_final_report(db, application_id)
    return build_interviewer_detail(application, assignment, assigned_user, review_package, final_report, interview_workspace)


@router.get("/{application_id}/source-pdf")
def get_application_source_pdf(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)

    if current_user.role != "admin":
        if not assignment or assignment.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this application")

    storage = get_storage_service()
    if not application.storage_key or not storage.exists(application.storage_key):
        raise HTTPException(status_code=404, detail="Source PDF not found")

    handle_context = storage.open_stream(application.storage_key)
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

    response = StreamingResponse(iterator(), media_type="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="{application.display_id}.pdf"'
    return response


@router.get("/{application_id}/final-report/export")
def get_application_final_report_export(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)

    if current_user.role != "admin":
        if not assignment or assignment.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this application")

    final_report = get_final_report(db, application_id)
    if not final_report:
        raise HTTPException(status_code=404, detail="Final report not found")

    storage = get_storage_service()
    stream_context = final_report_export_stream(storage=storage, final_report=final_report)
    stream_handle, media_type = stream_context.__enter__()

    def iterator():
        try:
            while True:
                chunk = stream_handle.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            stream_context.__exit__(None, None, None)

    response = StreamingResponse(iterator(), media_type=media_type or FINAL_REPORT_EXPORT_CONTENT_TYPE)
    response.headers["Content-Disposition"] = f'attachment; filename="{application.display_id}-final-report.json"'
    return response


@router.post("/{application_id}/report-chat", response_model=ReportChatResponse)
def ask_report_chat(
    application_id: uuid.UUID,
    payload: ReportChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        question = validate_report_chat_question(
            payload.question,
            max_chars=settings.REPORT_CHAT_MAX_QUESTION_CHARS,
            max_words=settings.REPORT_CHAT_MAX_QUESTION_WORDS,
        )
    except ReportChatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    limiter.check(
        f"report-chat:{current_user.id}",
        limit=settings.AICREDITS_REPORT_CHAT_PER_USER_LIMIT,
        window_seconds=settings.AICREDITS_REPORT_CHAT_WINDOW_SECONDS,
        detail="Report assistant limit reached for your account. Please wait a moment and try again.",
    )

    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)

    if current_user.role != "admin" and (not assignment or assignment.interviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this application")

    canonical_record = get_canonical_record(db, application_id)
    review_package = build_review_package_summary(application, canonical_record)
    if not review_package:
        raise HTTPException(status_code=409, detail="Report content is not available for this application")

    final_report = get_final_report(db, application_id)
    final_report_content = final_report.content if final_report and isinstance(final_report.content, dict) else None
    context = build_report_chat_context(question, review_package.pages_1_3.model_dump(), final_report_content)

    try:
        response = answer_report_question(question, context)
        logger.info(
            "Report chat API completed status_code=200 shape=%s operation=%s target=%s response_state=%s result_count=%s not_found=%s",
            context.get("question_shape_bucket"),
            context.get("detected_operation"),
            context.get("detected_target"),
            response.response_state,
            len(response.results),
            response.not_found,
        )
        return response
    except ReportChatError as exc:
        logger.warning(
            "Report chat API failed status_code=502 shape=%s operation=%s target=%s detail=%s",
            context.get("question_shape_bucket"),
            context.get("detected_operation"),
            context.get("detected_target"),
            str(exc),
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
