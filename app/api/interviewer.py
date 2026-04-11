from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.helpers import (
    build_application_list_item,
    get_application_or_404,
    get_assignment_for_application,
)
from app.api.schemas import ApplicationListItem
from app.auth.dependencies import require_interviewer
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
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
        .filter(Application.is_hidden.is_(False))
        .order_by(Application.last_activity_at.desc(), Application.created_at.desc())
        .all()
    )
    items: list[ApplicationListItem] = []
    for application in applications:
        assignment = get_assignment_for_application(db, application.id)
        items.append(build_application_list_item(application, current_user, assignment))
    return items


@router.post("/me/applications/{application_id}/hide", response_model=ApplicationListItem)
def hide_my_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    application = _require_assigned_application(db, application_id, current_user)
    if application.is_hidden:
        raise HTTPException(status_code=409, detail="Application is globally hidden")

    assignment = get_assignment_for_application(db, application_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.is_hidden_for_interviewer = True
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, current_user, assignment)


@router.post("/me/applications/{application_id}/unhide", response_model=ApplicationListItem)
def unhide_my_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    application = _require_assigned_application(db, application_id, current_user)
    if application.is_hidden:
        raise HTTPException(status_code=409, detail="Application is globally hidden")

    assignment = get_assignment_for_application(db, application_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.is_hidden_for_interviewer = False
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, current_user, assignment)
