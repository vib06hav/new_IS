from datetime import datetime
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_deterministic_pipeline, run_synthesis_pipeline
from app.api.helpers import (
    build_application_list_item,
    build_assignment_list_item,
    build_final_report_summary,
    get_canonical_record,
    get_application_or_404,
    get_assignment_for_application,
    get_final_report,
)
from app.api.schemas import (
    ApplicationDisplayIdUpdateRequest,
    ApplicationListItem,
    AssignmentListItem,
    AssignmentUpsertRequest,
    FinalReportMutationResponse,
)
from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.canonical_record import CanonicalRecord
from app.models.final_report import FinalReport
from app.models.user import User


router = APIRouter(tags=["Admin"])


def _get_interviewer_or_400(db: Session, interviewer_id: UUID) -> User:
    interviewer = db.query(User).filter(User.id == interviewer_id, User.role == "interviewer").first()
    if not interviewer:
        raise HTTPException(status_code=400, detail="Interviewer not found")
    return interviewer


def _delete_application_with_related_data(db: Session, application: Application) -> None:
    db.query(FinalReport).filter(FinalReport.application_id == application.id).delete()
    db.query(CanonicalRecord).filter(CanonicalRecord.application_id == application.id).delete()
    db.query(Assignment).filter(Assignment.application_id == application.id).delete()
    db.delete(application)


@router.get("/applications", response_model=list[ApplicationListItem])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    query = db.query(Application)
    if status_filter == "HIDDEN":
        query = query.filter(Application.is_hidden.is_(True))
    else:
        query = query.filter(Application.is_hidden.is_(False))
    if status_filter and status_filter != "HIDDEN":
        query = query.filter(Application.status == status_filter)

    applications = query.order_by(Application.last_activity_at.desc(), Application.created_at.desc()).all()
    items: list[ApplicationListItem] = []
    for application in applications:
        assignment = get_assignment_for_application(db, application.id)
        interviewer = None
        if assignment:
            interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()
        items.append(build_application_list_item(application, interviewer, assignment))
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

    canonical_record = get_canonical_record(db, application_id)
    final_report = get_final_report(db, application_id)

    try:
        if canonical_record and not final_report:
            synthesis_result = run_synthesis_pipeline(
                str(application_id),
                canonical_record.canonical_data,
                db=db,
                persisted_review=canonical_record,
            )
            ros_output = synthesis_result.get("ros_v1")
            if not isinstance(ros_output, dict):
                raise HTTPException(status_code=502, detail="Final report generation failed before a report was produced.")

            report_version = str((ros_output.get("report_metadata") or {}).get("report_version") or "ROS_v1")
            db.add(
                FinalReport(
                    application_id=application_id,
                    content=ros_output,
                    generated_by=current_user.id,
                    report_version=report_version,
                )
            )
            application.status = "COMPLETE"
            application.last_activity_at = datetime.utcnow()
            db.commit()
        else:
            application.status = "PROCESSING"
            application.last_activity_at = datetime.utcnow()
            db.commit()
            run_deterministic_pipeline(str(application_id), application.file_path, db)

        db.refresh(application)
        return build_application_list_item(application)
    except HTTPException:
        db.rollback()
        application.status = "FAILED"
        application.last_activity_at = datetime.utcnow()
        db.commit()
        raise
    except Exception:
        db.rollback()
        application.status = "FAILED"
        application.last_activity_at = datetime.utcnow()
        db.commit()
        raise


@router.post("/applications/{application_id}/generate-report", response_model=FinalReportMutationResponse)
def generate_final_report(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status != "READY":
        raise HTTPException(status_code=409, detail="Only READY applications can generate a final report")

    canonical_record = get_canonical_record(db, application_id)
    if not canonical_record:
        raise HTTPException(status_code=409, detail="Canonical data not available")

    if get_final_report(db, application_id):
        raise HTTPException(status_code=409, detail="Final report already exists")

    try:
        synthesis_result = run_synthesis_pipeline(
            str(application_id),
            canonical_record.canonical_data,
            db=db,
            persisted_review=canonical_record,
        )
        ros_output = synthesis_result.get("ros_v1")
        if not isinstance(ros_output, dict):
            raise HTTPException(status_code=502, detail="Final report generation failed before a report was produced.")

        report_version = str((ros_output.get("report_metadata") or {}).get("report_version") or "ROS_v1")
        final_report = FinalReport(
            application_id=application_id,
            content=ros_output,
            generated_by=current_user.id,
            report_version=report_version,
        )
        db.add(final_report)
        application.status = "COMPLETE"
        application.last_activity_at = datetime.utcnow()
        db.commit()
        db.refresh(final_report)
        return FinalReportMutationResponse(
            application_id=application_id,
            status=application.status,
            final_report=build_final_report_summary(final_report),
        )
    except HTTPException:
        db.rollback()
        application.status = "FAILED"
        application.last_activity_at = datetime.utcnow()
        db.commit()
        raise
    except Exception:
        db.rollback()
        application.status = "FAILED"
        application.last_activity_at = datetime.utcnow()
        db.commit()
        raise


@router.post("/applications/{application_id}/assign", response_model=ApplicationListItem)
def assign_application(
    application_id: UUID,
    payload: AssignmentUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status != "COMPLETE":
        raise HTTPException(status_code=409, detail="Only COMPLETE applications can be assigned")

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
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer, assignment)


@router.post("/applications/{application_id}/hide", response_model=ApplicationListItem)
def hide_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)

    assignment = get_assignment_for_application(db, application_id)
    interviewer = None
    if assignment:
        interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()

    application.is_hidden = True
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer, assignment)


@router.post("/applications/{application_id}/unhide", response_model=ApplicationListItem)
def unhide_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)

    assignment = get_assignment_for_application(db, application_id)
    interviewer = None
    if assignment:
        interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()

    application.is_hidden = False
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer, assignment)


@router.delete("/applications/{application_id}/queue", status_code=status.HTTP_204_NO_CONTENT)
def remove_application_from_queue(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status not in {"UPLOADED", "FAILED"}:
        raise HTTPException(status_code=409, detail="Only UPLOADED or FAILED queue items can be removed")

    file_path = application.file_path
    _delete_application_with_related_data(db, application)
    db.commit()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return None


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    file_path = application.file_path

    _delete_application_with_related_data(db, application)
    db.commit()

    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    return None


@router.put("/applications/{application_id}/assign", response_model=ApplicationListItem)
def reassign_application(
    application_id: UUID,
    payload: AssignmentUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if application.status != "ASSIGNED":
        raise HTTPException(status_code=409, detail="Only ASSIGNED applications can be reassigned")

    interviewer = _get_interviewer_or_400(db, payload.interviewer_id)
    assignment = get_assignment_for_application(db, application_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.interviewer_id = interviewer.id
    assignment.assigned_by = current_user.id
    assignment.assigned_at = datetime.utcnow()
    assignment.is_hidden_for_interviewer = False
    application.status = "ASSIGNED"
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return build_application_list_item(application, interviewer, assignment)


@router.put("/applications/{application_id}/display-id", response_model=ApplicationListItem)
def update_application_display_id(
    application_id: UUID,
    payload: ApplicationDisplayIdUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    application = get_application_or_404(db, application_id)
    if not payload.display_id:
        raise HTTPException(status_code=400, detail="Display ID cannot be empty")

    existing_application = (
        db.query(Application)
        .filter(Application.display_id == payload.display_id, Application.id != application_id)
        .first()
    )
    if existing_application:
        raise HTTPException(status_code=409, detail="Application display ID already exists")

    application.display_id = payload.display_id

    assignment = get_assignment_for_application(db, application_id)
    interviewer = None
    if assignment:
        interviewer = db.query(User).filter(User.id == assignment.interviewer_id).first()

    try:
        application.last_activity_at = datetime.utcnow()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Application display ID already exists") from exc

    db.refresh(application)
    return build_application_list_item(application, interviewer, assignment)


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
