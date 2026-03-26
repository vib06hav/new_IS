from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_synthesis_pipeline
from app.api.helpers import (
    build_application_list_item,
    build_draft_summary,
    get_application_or_404,
    get_assignment_for_application,
    get_canonical_summary,
    get_latest_draft,
)
from app.api.schemas import ApplicationListItem, DraftMutationResponse
from app.auth.dependencies import get_current_user, require_interviewer
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.draft import Draft
from app.models.user import User


router = APIRouter(tags=["Interviewer"])


def _require_assigned_application(db: Session, application_id: UUID, current_user: User) -> Application:
    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)
    if not assignment or assignment.interviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to this application")
    return application


@router.get("/me/applications", response_model=list[ApplicationListItem])
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    applications = (
        db.query(Application)
        .join(Assignment, Application.id == Assignment.application_id)
        .filter(Assignment.interviewer_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return [build_application_list_item(application, current_user) for application in applications]


@router.post("/applications/{application_id}/generate", response_model=DraftMutationResponse)
def generate_draft(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    application = _require_assigned_application(db, application_id, current_user)
    if application.status == "PUBLISHED":
        raise HTTPException(status_code=409, detail="Published applications cannot be regenerated")
    if application.status not in {"ASSIGNED", "DRAFT"}:
        raise HTTPException(status_code=409, detail="Application is not ready for draft generation")

    canonical = get_canonical_summary(db, application_id)
    if not canonical:
        raise HTTPException(status_code=409, detail="Canonical data not available")

    latest_draft = get_latest_draft(db, application_id)
    next_version = 1 if not latest_draft else latest_draft.version + 1

    synthesis_result = run_synthesis_pipeline(str(application_id), canonical.canonical_data, db=None)
    draft = Draft(
        application_id=application_id,
        version=next_version,
        content=synthesis_result["ros_v1"],
        generated_by=current_user.id,
        is_published=False,
    )
    db.add(draft)
    application.status = "DRAFT"
    db.commit()
    db.refresh(draft)
    return DraftMutationResponse(
        application_id=application_id,
        status=application.status,
        draft=build_draft_summary(draft),
    )


@router.post("/applications/{application_id}/publish", response_model=DraftMutationResponse)
def publish_draft(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    application = _require_assigned_application(db, application_id, current_user)
    if application.status != "DRAFT":
        raise HTTPException(status_code=409, detail="Only DRAFT applications can be published")

    latest_draft = get_latest_draft(db, application_id)
    if not latest_draft:
        raise HTTPException(status_code=409, detail="No draft available to publish")

    db.query(Draft).filter(Draft.application_id == application_id).update({"is_published": False})
    latest_draft.is_published = True
    application.status = "PUBLISHED"
    db.commit()
    db.refresh(latest_draft)
    return DraftMutationResponse(
        application_id=application_id,
        status=application.status,
        draft=build_draft_summary(latest_draft),
    )
