from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_synthesis_pipeline
from app.api.helpers import (
    build_application_list_item,
    build_draft_summary,
    get_canonical_record,
    get_application_or_404,
    get_assignment_for_application,
    get_latest_draft,
)
from app.api.schemas import ApplicationListItem, DraftMutationResponse
from app.auth.dependencies import get_current_user, require_interviewer
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.draft import Draft
from app.models.user import User
from app.security.rate_limit import limiter


router = APIRouter(tags=["Interviewer"])


def _build_generation_error_detail(synthesis_result: dict) -> str:
    validation_result = synthesis_result.get("validation_result") or {}
    violations = validation_result.get("violations_log") or []
    if violations:
        first = violations[0]
        violation_type = first.get("type") or "generation_error"
        context = first.get("context") or "Draft generation failed before a report was produced."
        return f"{violation_type}: {context}"
    return "Draft generation failed before a report was produced."


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
    limiter.check(
        f"generate:{current_user.id}:{application_id}",
        limit=5,
        window_seconds=60,
        detail="Draft generation rate limit exceeded. Please retry shortly.",
    )
    application = _require_assigned_application(db, application_id, current_user)
    if application.status == "PUBLISHED":
        raise HTTPException(status_code=409, detail="Published applications cannot be regenerated")
    if application.status not in {"ASSIGNED", "DRAFT"}:
        raise HTTPException(status_code=409, detail="Application is not ready for draft generation")

    canonical_record = get_canonical_record(db, application_id)
    if not canonical_record:
        raise HTTPException(status_code=409, detail="Canonical data not available")

    latest_draft = get_latest_draft(db, application_id)
    next_version = 1 if not latest_draft else latest_draft.version + 1

    synthesis_result = run_synthesis_pipeline(
        str(application_id),
        canonical_record.canonical_data,
        db=None,
        persisted_review=canonical_record,
    )
    ros_output = synthesis_result.get("ros_v1")
    if not isinstance(ros_output, dict):
        raise HTTPException(status_code=502, detail=_build_generation_error_detail(synthesis_result))

    draft = Draft(
        application_id=application_id,
        version=next_version,
        content=ros_output,
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
    limiter.check(
        f"publish:{current_user.id}:{application_id}",
        limit=5,
        window_seconds=60,
        detail="Publish rate limit exceeded. Please retry shortly.",
    )
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
