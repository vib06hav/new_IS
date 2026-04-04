from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.helpers import build_interviewer_list_item, build_user_summary
from app.api.schemas import (
    InterviewerAssignmentSaveRequest,
    InterviewerAssignmentSummary,
    InterviewerAssignmentSummaryItem,
    InterviewerListItem,
)
from app.auth.schemas import AdminPasswordChange, InterviewerCreate, InterviewerUpdate, UserResponse
from app.auth.dependencies import require_admin
from app.auth.service import admin_set_user_password, create_interviewer, update_interviewer
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.draft import Draft
from app.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


ACTIVE_ASSIGNMENT_STATUSES = {"ASSIGNED", "DRAFT"}


def _get_interviewer_or_404(db: Session, user_id: UUID) -> User:
    interviewer = db.query(User).filter(User.id == user_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="User not found")
    if interviewer.role != "interviewer":
        raise HTTPException(status_code=409, detail="Only interviewer accounts can be updated here")
    return interviewer


def _build_assignment_summary(db: Session, interviewer: User) -> InterviewerAssignmentSummary:
    applications = (
        db.query(Application)
        .filter(Application.status.in_(["READY", "ASSIGNED", "DRAFT"]))
        .order_by(Application.created_at.desc())
        .all()
    )
    assignments = db.query(Assignment).all()
    assignments_by_application = {assignment.application_id: assignment for assignment in assignments}
    interviewer_ids = {assignment.interviewer_id for assignment in assignments}
    interviewers_by_id = {
        user.id: user
        for user in db.query(User).filter(User.id.in_(interviewer_ids)).all()
    } if interviewer_ids else {}

    currently_assigned: list[InterviewerAssignmentSummaryItem] = []
    available_to_assign: list[InterviewerAssignmentSummaryItem] = []
    available_to_reassign: list[InterviewerAssignmentSummaryItem] = []

    for application in applications:
        assignment = assignments_by_application.get(application.id)
        if application.status == "READY" and not assignment:
            available_to_assign.append(
                InterviewerAssignmentSummaryItem(
                    application_id=application.id,
                    status=application.status,
                )
            )
            continue

        if application.status not in ACTIVE_ASSIGNMENT_STATUSES or not assignment:
            continue

        if assignment.interviewer_id == interviewer.id:
            currently_assigned.append(
                InterviewerAssignmentSummaryItem(
                    application_id=application.id,
                    status=application.status,
                )
            )
            continue

        current_owner = interviewers_by_id.get(assignment.interviewer_id)
        available_to_reassign.append(
            InterviewerAssignmentSummaryItem(
                application_id=application.id,
                status=application.status,
                current_interviewer=build_user_summary(current_owner),
            )
        )

    return InterviewerAssignmentSummary(
        interviewer_id=interviewer.id,
        active_assignment_count=len(currently_assigned),
        currently_assigned=currently_assigned,
        available_to_assign=available_to_assign,
        available_to_reassign=available_to_reassign,
    )


@router.post("/interviewers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_interviewer_account(
    payload: InterviewerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = create_interviewer(db, payload)
    return {
        "id": str(interviewer.id),
        "name": interviewer.name,
        "email": interviewer.email,
        "role": interviewer.role,
    }


@router.get("/interviewers", response_model=list[InterviewerListItem])
def list_interviewers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewers = db.query(User).filter(User.role == "interviewer").order_by(User.created_at.desc()).all()
    results = []
    for interviewer in interviewers:
        active_assignment_count = (
            db.query(Assignment)
            .join(Application, Assignment.application_id == Application.id)
            .filter(
                Assignment.interviewer_id == interviewer.id,
                Application.status.in_(list(ACTIVE_ASSIGNMENT_STATUSES)),
            )
            .count()
        )
        results.append(build_interviewer_list_item(interviewer, active_assignment_count))
    return results


@router.get("/interviewers/{user_id}/assignments", response_model=InterviewerAssignmentSummary)
def get_interviewer_assignment_summary(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = _get_interviewer_or_404(db, user_id)
    return _build_assignment_summary(db, interviewer)


@router.put("/interviewers/{user_id}/assignments", response_model=InterviewerAssignmentSummary)
def save_interviewer_assignments(
    user_id: UUID,
    payload: InterviewerAssignmentSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = _get_interviewer_or_404(db, user_id)

    final_ids = set(payload.assigned_application_ids)
    current_assignments = (
        db.query(Assignment)
        .join(Application, Assignment.application_id == Application.id)
        .filter(
            Assignment.interviewer_id == interviewer.id,
            Application.status.in_(list(ACTIVE_ASSIGNMENT_STATUSES)),
        )
        .all()
    )
    current_assignment_ids = {assignment.application_id for assignment in current_assignments}

    application_ids = final_ids | current_assignment_ids
    applications = (
        db.query(Application)
        .filter(Application.id.in_(application_ids))
        .all()
    ) if application_ids else []
    applications_by_id = {application.id: application for application in applications}

    all_assignments = (
        db.query(Assignment)
        .filter(Assignment.application_id.in_(application_ids))
        .all()
    ) if application_ids else []
    assignments_by_application = {assignment.application_id: assignment for assignment in all_assignments}

    for application_id in final_ids:
        application = applications_by_id.get(application_id)
        if not application:
            raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
        if application.status not in {"READY", "ASSIGNED", "DRAFT"}:
            raise HTTPException(status_code=409, detail="Only READY, ASSIGNED, or DRAFT applications can be staged")
        if application.status == "PUBLISHED":
            raise HTTPException(status_code=409, detail="Published applications cannot be assigned here")

        assignment = assignments_by_application.get(application_id)
        if not assignment:
            if application.status != "READY":
                raise HTTPException(status_code=409, detail="Only READY applications can be newly assigned")
            new_assignment = Assignment(
                application_id=application.id,
                interviewer_id=interviewer.id,
                assigned_by=current_user.id,
            )
            db.add(new_assignment)
            application.status = "ASSIGNED"
            continue

        if assignment.interviewer_id == interviewer.id:
            continue

        db.query(Draft).filter(Draft.application_id == application_id).delete()
        assignment.interviewer_id = interviewer.id
        assignment.assigned_by = current_user.id
        assignment.assigned_at = datetime.utcnow()
        application.status = "ASSIGNED"

    for assignment in current_assignments:
        if assignment.application_id in final_ids:
            continue

        application = applications_by_id.get(assignment.application_id)
        if application and application.status in ACTIVE_ASSIGNMENT_STATUSES:
            db.query(Draft).filter(Draft.application_id == assignment.application_id).delete()
            application.status = "READY"
        db.delete(assignment)

    db.commit()
    return _build_assignment_summary(db, interviewer)


@router.put("/interviewers/{user_id}", response_model=UserResponse)
def update_interviewer_account(
    user_id: UUID,
    payload: InterviewerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = _get_interviewer_or_404(db, user_id)
    interviewer = update_interviewer(db, interviewer, payload)
    return {
        "id": str(interviewer.id),
        "name": interviewer.name,
        "email": interviewer.email,
        "role": interviewer.role,
    }


@router.put("/interviewers/{user_id}/password", response_model=UserResponse)
def update_interviewer_password(
    user_id: UUID,
    payload: AdminPasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = _get_interviewer_or_404(db, user_id)
    interviewer = admin_set_user_password(db, interviewer, payload)
    return {
        "id": str(interviewer.id),
        "name": interviewer.name,
        "email": interviewer.email,
        "role": interviewer.role,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interviewer(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    interviewer = db.query(User).filter(User.id == user_id).first()
    if not interviewer:
        raise HTTPException(status_code=404, detail="User not found")
    if interviewer.role != "interviewer":
        raise HTTPException(status_code=409, detail="Only interviewer accounts can be removed here")

    uploaded_application_count = (
        db.query(Application)
        .filter(Application.uploaded_by == user_id)
        .count()
    )
    if uploaded_application_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot remove interviewer because they are referenced as the uploader for existing applications",
        )

    active_assignment_count = (
        db.query(Assignment)
        .filter(Assignment.interviewer_id == user_id)
        .count()
    )
    if active_assignment_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot remove interviewer while they still have active assignments",
        )

    assignments = db.query(Assignment).filter(Assignment.interviewer_id == user_id).all()
    for assignment in assignments:
        db.query(Draft).filter(Draft.application_id == assignment.application_id).delete()
        db.delete(assignment)

    db.delete(interviewer)
    db.commit()
    return None
