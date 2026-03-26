from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_deterministic_pipeline
from app.api.helpers import (
    build_application_list_item,
    build_assignment_list_item,
    get_application_or_404,
    get_assignment_for_application,
)
from app.api.schemas import ApplicationListItem, AssignmentListItem, AssignmentUpsertRequest
from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.draft import Draft
from app.models.user import User


router = APIRouter(tags=["Admin"])


def _get_interviewer_or_400(db: Session, interviewer_id: UUID) -> User:
    interviewer = db.query(User).filter(User.id == interviewer_id, User.role == "interviewer").first()
    if not interviewer:
        raise HTTPException(status_code=400, detail="Interviewer not found")
    return interviewer


@router.get("/applications", response_model=list[ApplicationListItem])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(Application)
    if status_filter:
        query = query.filter(Application.status == status_filter)

    applications = query.order_by(Application.created_at.desc()).all()
    items: list[ApplicationListItem] = []
    for application in applications:
        assignment = get_assignment_for_application(db, application.id)
        interviewer = None
        if assignment:
            interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()
        items.append(build_application_list_item(application, interviewer))
    return items


@router.post("/applications/{application_id}/retry", response_model=ApplicationListItem)
def retry_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status != "FAILED":
        raise HTTPException(status_code=409, detail="Only FAILED applications can be retried")

    application.status = "PROCESSING"
    db.commit()
    run_deterministic_pipeline(str(application_id), application.file_path, db)
    db.refresh(application)
    return build_application_list_item(application)


@router.post("/applications/{application_id}/assign", response_model=ApplicationListItem)
def assign_application(
    application_id: UUID,
    payload: AssignmentUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status != "READY":
        raise HTTPException(status_code=409, detail="Only READY applications can be assigned")

    interviewer = _get_interviewer_or_400(db, payload.interviewer_id)
    existing_assignment = get_assignment_for_application(db, application_id)
    if existing_assignment:
        raise HTTPException(status_code=409, detail="Application already assigned")

    assignment = Assignment(
        application_id=application.id,
        interviewer_id=interviewer.id,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    application.status = "ASSIGNED"
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer)


@router.put("/applications/{application_id}/assign", response_model=ApplicationListItem)
def reassign_application(
    application_id: UUID,
    payload: AssignmentUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status not in {"ASSIGNED", "DRAFT"}:
        raise HTTPException(status_code=409, detail="Only ASSIGNED or DRAFT applications can be reassigned")

    interviewer = _get_interviewer_or_400(db, payload.interviewer_id)
    assignment = get_assignment_for_application(db, application_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.query(Draft).filter(Draft.application_id == application_id).delete()
    assignment.interviewer_id = interviewer.id
    assignment.assigned_by = current_user.id
    assignment.assigned_at = datetime.utcnow()
    application.status = "ASSIGNED"
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer)


@router.get("/assignments", response_model=list[AssignmentListItem])
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    assignments = db.query(Assignment).order_by(Assignment.assigned_at.desc()).all()
    items: list[AssignmentListItem] = []
    for assignment in assignments:
        application = get_application_or_404(db, assignment.application_id)
        interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()
        if interviewer:
            items.append(build_assignment_list_item(assignment, application, interviewer))
    return items
