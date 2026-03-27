from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.helpers import build_interviewer_list_item
from app.api.schemas import InterviewerListItem
from app.auth.schemas import InterviewerCreate, UserResponse
from app.auth.dependencies import require_admin
from app.auth.service import create_interviewer
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.draft import Draft
from app.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


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
            .filter(Assignment.interviewer_id == interviewer.id)
            .count()
        )
        results.append(build_interviewer_list_item(interviewer, active_assignment_count))
    return results


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
