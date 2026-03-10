import os
import uuid
import shutil
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

from app.database import get_db
from app.models.user import User
from app.models.application import Application
from app.models.canonical_record import CanonicalRecord
from app.models.synthesis_record import SynthesisRecord
from app.auth.service import get_current_user_from_token

from app.api.schemas import ApplicationResponse, SynthesisOutput
from app.config import settings

from app.agents.orchestrator import run_pipeline
from app.canonical.version import CANONICAL_VERSION

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Applications"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_current_user_from_token(token, db)

@router.post("/upload", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def upload_application(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    application_id = uuid.uuid4()
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, f"{application_id}.pdf")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    logger.info(f"Application upload received (application_id: {application_id}, file size: {file_size} bytes)")
    logger.info(f"Pipeline execution started (application_id: {application_id})")
        
    # Create application record
    db_app = Application(
        id=application_id,
        uploaded_by=current_user.id,
        file_path=file_path,
        pipeline_status="processing"
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    try:
        # Phase 5-7: Pipeline Orchestration & Synthesis Integration
        pipeline_results = run_pipeline(str(application_id), file_path)
        
        canonical_data = pipeline_results["canonical_data"]
        confidence = pipeline_results.get("confidence", 0.0)
        validation_result = pipeline_results["validation_result"]
        ros_document = pipeline_results["ros_v1"]
        
        # Store canonical record
        from app.utils.sanitizer import sanitize_for_json
        db_canonical = CanonicalRecord(
            application_id=application_id,
            canonical_version=CANONICAL_VERSION,
            canonical_data=sanitize_for_json(canonical_data)
        )
        db.add(db_canonical)
        logger.info(f"Canonical persistence completed (application_id: {application_id})")
        
        if not validation_result.get("passed", False) or not ros_document:
            logger.error(f"Pipeline validation failed (application_id: {application_id})")
            db.rollback()
            db_app.pipeline_status = "failed"
            db.commit()
            raise HTTPException(status_code=400, detail="Policy validation failed: Output rejected.")
            
        # Store synthesis record (ROS Document)
        db_synthesis = SynthesisRecord(
            application_id=application_id,
            synthesis_output=sanitize_for_json(ros_document),
            policy_passed=True,
            policy_violations_log=None
        )
        db.add(db_synthesis)
        
        # Update App state
        db_app.pipeline_status = "complete"
        db_app.pipeline_confidence = confidence
        db.commit()
        db.refresh(db_app)
        db.refresh(db_synthesis)

        logger.info(f"Pipeline completion (application_id: {application_id}, final status: complete)")

        return ApplicationResponse(
            id=db_app.id,
            status=db_app.pipeline_status,
            confidence_score=float(db_app.pipeline_confidence) if db_app.pipeline_confidence is not None else None,
            created_at=db_app.created_at,
            synthesis=SynthesisOutput(**db_synthesis.synthesis_output)
        )
        
    except ValueError as e: # Catch critical pipeline errors
        db.rollback()
        db_app.pipeline_status = "failed"
        db.commit()
        logger.error(f"Pipeline failure (application_id: {application_id}, reason: {str(e)})")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        db.rollback()
        db_app.pipeline_status = "failed"
        db.commit()
        logger.error(f"Pipeline failure (application_id: {application_id}, reason: Internal error)")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}\n\nTraceback: {tb}")


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_app = db.query(Application).filter(Application.id == application_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if db_app.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this application")
        
    db_synthesis = db.query(SynthesisRecord).filter(SynthesisRecord.application_id == application_id).first()
    
    synthesis_output = None
    if db_synthesis:
        synthesis_output = SynthesisOutput(**db_synthesis.synthesis_output)
        
    return ApplicationResponse(
        id=db_app.id,
        status=db_app.pipeline_status,
        confidence_score=float(db_app.pipeline_confidence) if db_app.pipeline_confidence is not None else None,
        created_at=db_app.created_at,
        synthesis=synthesis_output
    )
