from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.helpers import (
    build_application_list_item,
    build_interview_workspace_summary,
    get_application_or_404,
    get_assignment_for_application,
    get_final_report,
    get_interview_workspace,
)
from app.api.schemas import (
    ApplicationListItem,
    InterviewWorkspaceRefinementRequest,
    InterviewWorkspaceRefinementResponse,
    InterviewWorkspaceSummary,
    InterviewWorkspaceUpsertRequest,
)
from app.auth.dependencies import require_interviewer
from app.database import get_db
from app.interview_refinement import InterviewRefinementError, refine_interview_text
from app.interview_workspace import build_workspace_seed, normalize_workspace_content
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.interview_workspace import InterviewWorkspace
from app.models.user import User
from app.security.rate_limit import limiter
from app.config import settings


router = APIRouter(tags=["Interviewer"])


def _require_assigned_application(db: Session, application_id: UUID, current_user: User) -> Application:
    application = get_application_or_404(db, application_id)
    assignment = get_assignment_for_application(db, application_id)
    if not assignment or assignment.interviewer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not assigned to this application")
    return application


def _require_workspace(
    db: Session,
    application_id: UUID,
    current_user: User,
) -> InterviewWorkspace:
    _require_assigned_application(db, application_id, current_user)
    workspace = get_interview_workspace(db, application_id)
    if not workspace or workspace.interviewer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Interview workspace not found")
    return workspace


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


@router.post("/me/applications/{application_id}/workspace", response_model=InterviewWorkspaceSummary)
def create_interview_workspace(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    _require_assigned_application(db, application_id, current_user)

    existing_workspace = get_interview_workspace(db, application_id)
    if existing_workspace:
        if existing_workspace.interviewer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to use this interview workspace")
        return build_interview_workspace_summary(existing_workspace)

    final_report = get_final_report(db, application_id)
    if not final_report or not isinstance(final_report.content, dict):
        raise HTTPException(status_code=409, detail="Final report is required before configuring interview prep")

    workspace = InterviewWorkspace(
        application_id=application_id,
        interviewer_id=current_user.id,
        status="draft",
        content=build_workspace_seed(final_report.content),
    )
    db.add(workspace)

    application = get_application_or_404(db, application_id)
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return build_interview_workspace_summary(workspace)


@router.get("/me/applications/{application_id}/workspace", response_model=InterviewWorkspaceSummary)
def get_my_interview_workspace(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    workspace = _require_workspace(db, application_id, current_user)
    return build_interview_workspace_summary(workspace)


@router.put("/me/applications/{application_id}/workspace", response_model=InterviewWorkspaceSummary)
def update_my_interview_workspace(
    application_id: UUID,
    payload: InterviewWorkspaceUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    workspace = _require_workspace(db, application_id, current_user)
    workspace.content = normalize_workspace_content(payload.content.model_dump())
    workspace.updated_at = datetime.utcnow()

    application = get_application_or_404(db, application_id)
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return build_interview_workspace_summary(workspace)


@router.post("/me/applications/{application_id}/workspace/launch", response_model=InterviewWorkspaceSummary)
def launch_my_interview_workspace(
    application_id: UUID,
    payload: InterviewWorkspaceUpsertRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    workspace = _require_workspace(db, application_id, current_user)
    if payload is not None:
        workspace.content = normalize_workspace_content(payload.content.model_dump())
    workspace.status = "launched"
    if not workspace.launched_at:
        workspace.launched_at = datetime.utcnow()
    workspace.updated_at = datetime.utcnow()

    application = get_application_or_404(db, application_id)
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return build_interview_workspace_summary(workspace)


@router.post("/me/applications/{application_id}/workspace/finish", response_model=InterviewWorkspaceSummary)
def finish_my_interview_workspace(
    application_id: UUID,
    payload: InterviewWorkspaceUpsertRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    workspace = _require_workspace(db, application_id, current_user)
    if payload is not None:
        workspace.content = normalize_workspace_content(payload.content.model_dump())
    if not workspace.launched_at:
        workspace.launched_at = datetime.utcnow()
    workspace.status = "postgame"
    workspace.updated_at = datetime.utcnow()

    application = get_application_or_404(db, application_id)
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return build_interview_workspace_summary(workspace)


@router.post("/me/applications/{application_id}/workspace/complete", response_model=InterviewWorkspaceSummary)
def complete_my_interview_workspace(
    application_id: UUID,
    payload: InterviewWorkspaceUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    workspace = _require_workspace(db, application_id, current_user)
    workspace.content = normalize_workspace_content(payload.content.model_dump())
    if not workspace.launched_at:
        workspace.launched_at = datetime.utcnow()
    workspace.status = "completed"
    workspace.completed_at = datetime.utcnow()
    workspace.updated_at = datetime.utcnow()

    application = get_application_or_404(db, application_id)
    application.status = "COMPLETE"
    application.last_activity_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return build_interview_workspace_summary(workspace)


@router.post(
    "/me/applications/{application_id}/workspace/refine",
    response_model=InterviewWorkspaceRefinementResponse,
)
def refine_my_interview_workspace_text(
    application_id: UUID,
    payload: InterviewWorkspaceRefinementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_interviewer),
):
    _require_workspace(db, application_id, current_user)

    limiter.check(
        f"interview-refinement:{current_user.id}",
        limit=settings.AICREDITS_INTERVIEW_REFINEMENT_PER_USER_LIMIT,
        window_seconds=settings.AICREDITS_INTERVIEW_REFINEMENT_WINDOW_SECONDS,
        detail="Interview refinement limit reached for your account. Please wait a moment and try again.",
    )

    try:
        refined_text = refine_interview_text(
            mode=payload.mode,
            text=payload.text,
            instruction=payload.instruction,
            content=payload.content,
            theme_id=payload.theme_id,
            question_id=payload.question_id,
            follow_up_id=payload.follow_up_id,
        )
    except InterviewRefinementError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return InterviewWorkspaceRefinementResponse(refined_text=refined_text)
