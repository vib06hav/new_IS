from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApplicationDetailAdmin,
    ApplicationDetailInterviewer,
    ApplicationListItem,
    AssignmentListItem,
    CanonicalSummary,
    FinalReportSummary,
    InterviewWorkspaceContent,
    InterviewWorkspaceSummary,
    InterviewerListItem,
    ReviewPackageSummary,
    ReviewPages123,
    UserSummary,
)
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.canonical_record import CanonicalRecord
from app.models.final_report import FinalReport
from app.models.interview_workspace import InterviewWorkspace
from app.models.user import User
from app.projection.ros_projector import project_ros
from app.interview_workspace import normalize_workspace_content


def get_application_or_404(db: Session, application_id: UUID) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def get_assignment_for_application(db: Session, application_id: UUID) -> Optional[Assignment]:
    return db.query(Assignment).filter(Assignment.application_id == application_id).first()


def get_final_report(db: Session, application_id: UUID) -> Optional[FinalReport]:
    final_report = (
        db.query(FinalReport)
        .filter(FinalReport.application_id == application_id)
        .first()
    )
    if final_report and isinstance(final_report.content, dict):
        return final_report
    return None


def get_interview_workspace(db: Session, application_id: UUID) -> Optional[InterviewWorkspace]:
    workspace = db.query(InterviewWorkspace).filter(InterviewWorkspace.application_id == application_id).first()
    if workspace and isinstance(workspace.content, dict):
        return workspace
    return None


def get_canonical_summary(db: Session, application_id: UUID) -> Optional[CanonicalSummary]:
    canonical = get_canonical_record(db, application_id)
    if not canonical:
        return None
    return CanonicalSummary(
        canonical_version=canonical.canonical_version,
        canonical_data=canonical.canonical_data,
    )


def get_canonical_record(db: Session, application_id: UUID) -> Optional[CanonicalRecord]:
    return (
        db.query(CanonicalRecord)
        .filter(CanonicalRecord.application_id == application_id)
        .first()
    )


def _derive_pages_1_3(canonical_data: dict[str, Any]) -> dict[str, Any]:
    page_1, page_2, page_3, _, _ = project_ros(canonical_data)
    return {
        "page_1_background_profile": page_1,
        "page_2_academic_and_engagement": page_2,
        "page_3_essays": page_3,
    }


def build_review_package_summary(
    application: Application,
    canonical_record: Optional[CanonicalRecord],
) -> Optional[ReviewPackageSummary]:
    if not canonical_record:
        return None

    pages_1_3 = canonical_record.pages_1_3 or _derive_pages_1_3(canonical_record.canonical_data)
    return ReviewPackageSummary(
        canonical_version=canonical_record.canonical_version,
        pdf_url=f"/api/applications/{application.id}/source-pdf",
        pages_1_3=ReviewPages123(**pages_1_3),
    )


def build_user_summary(user: Optional[User]) -> Optional[UserSummary]:
    if not user:
        return None
    return UserSummary(id=user.id, name=user.name, email=user.email)


def build_final_report_summary(final_report: Optional[FinalReport]) -> Optional[FinalReportSummary]:
    if not final_report or not isinstance(final_report.content, dict):
        return None
    return FinalReportSummary(
        id=final_report.id,
        report_version=final_report.report_version,
        created_at=final_report.created_at,
        content=final_report.content,
        export_url=f"/api/applications/{final_report.application_id}/final-report/export",
    )


def build_interview_workspace_summary(workspace: Optional[InterviewWorkspace]) -> Optional[InterviewWorkspaceSummary]:
    if not workspace or not isinstance(workspace.content, dict):
        return None
    normalized_content = normalize_workspace_content(workspace.content)
    return InterviewWorkspaceSummary(
        id=workspace.id,
        application_id=workspace.application_id,
        interviewer_id=workspace.interviewer_id,
        status=workspace.status,
        content=InterviewWorkspaceContent.model_validate(normalized_content),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        launched_at=workspace.launched_at,
        completed_at=workspace.completed_at,
    )


def build_application_list_item(
    application: Application,
    interviewer: Optional[User] = None,
    assignment: Optional[Assignment] = None,
) -> ApplicationListItem:
    return ApplicationListItem(
        id=application.id,
        display_id=application.display_id,
        status=application.status,
        is_hidden=application.is_hidden,
        is_hidden_for_interviewer=assignment.is_hidden_for_interviewer if assignment else False,
        created_at=application.created_at,
        last_activity_at=application.last_activity_at,
        assigned_interviewer=build_user_summary(interviewer),
    )


def build_admin_detail(
    application: Application,
    interviewer: Optional[User],
    review_package: Optional[ReviewPackageSummary],
    final_report: Optional[FinalReport],
    interview_workspace: Optional[InterviewWorkspace] = None,
) -> ApplicationDetailAdmin:
    return ApplicationDetailAdmin(
        id=application.id,
        display_id=application.display_id,
        status=application.status,
        created_at=application.created_at,
        last_activity_at=application.last_activity_at,
        assigned_interviewer=build_user_summary(interviewer),
        review_package=review_package,
        final_report=build_final_report_summary(final_report),
        interview_workspace=build_interview_workspace_summary(interview_workspace),
    )


def build_interviewer_detail(
    application: Application,
    assignment: Optional[Assignment],
    interviewer: Optional[User],
    review_package: Optional[ReviewPackageSummary],
    final_report: Optional[FinalReport],
    interview_workspace: Optional[InterviewWorkspace] = None,
) -> ApplicationDetailInterviewer:
    return ApplicationDetailInterviewer(
        id=application.id,
        display_id=application.display_id,
        status=application.status,
        created_at=application.created_at,
        last_activity_at=application.last_activity_at,
        is_hidden_for_interviewer=assignment.is_hidden_for_interviewer if assignment else False,
        assigned_interviewer=build_user_summary(interviewer),
        review_package=review_package,
        final_report=build_final_report_summary(final_report),
        interview_workspace=build_interview_workspace_summary(interview_workspace),
    )


def build_assignment_list_item(
    assignment: Assignment,
    application: Application,
    interviewer: User,
) -> AssignmentListItem:
    return AssignmentListItem(
        application_id=assignment.application_id,
        application_display_id=application.display_id,
        status=application.status,
        assigned_at=assignment.assigned_at,
        interviewer=UserSummary(id=interviewer.id, name=interviewer.name, email=interviewer.email),
    )


def build_interviewer_list_item(user: User, active_assignment_count: int) -> InterviewerListItem:
    return InterviewerListItem(
        id=user.id,
        name=user.name,
        email=user.email,
        active_assignment_count=active_assignment_count,
    )
