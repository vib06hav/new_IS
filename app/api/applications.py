import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_deterministic_pipeline
from app.api.helpers import (
    build_admin_detail,
    build_interviewer_detail,
    get_application_or_404,
    get_assignment_for_application,
    get_canonical_summary,
    get_latest_draft,
    get_published_draft,
)
from app.api.schemas import (
    ApplicationDetailAdmin,
    ApplicationDetailInterviewer,
    ApplicationUploadResponse,
)
from app.auth.dependencies import get_current_user, require_admin
from app.config import settings
from app.database import get_db
from app.models.application import Application
from app.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/upload", response_model=ApplicationUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_application(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    application_id = uuid.uuid4()
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, f"{application_id}.pdf")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_app = Application(
        id=application_id,
        uploaded_by=current_user.id,
        file_path=file_path,
        status="UPLOADED",
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)

    try:
        db_app.status = "PROCESSING"
        db.commit()
        run_deterministic_pipeline(str(application_id), file_path, db)
        db.refresh(db_app)
        logger.info(f"Upload pipeline completed for {application_id} with status {db_app.status}")
        return ApplicationUploadResponse(id=db_app.id, status=db_app.status, created_at=db_app.created_at)
    except Exception:
        db.rollback()
        db_app.status = "FAILED"
        db.commit()
        raise


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

    canonical = get_canonical_summary(db, application_id)

    if current_user.role == "admin":
        published_draft = get_published_draft(db, application_id)
        return build_admin_detail(application, assigned_user, canonical, published_draft)

    if not assignment or assignment.interviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this application")

    latest_draft = get_latest_draft(db, application_id)
    return build_interviewer_detail(application, assigned_user, canonical, latest_draft)
