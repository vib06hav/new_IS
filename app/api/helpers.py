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
    DraftSummary,
    InterviewerListItem,
    ReviewPackageSummary,
    ReviewPages123,
    UserSummary,
)
from app.models.application import Application
from app.models.assignment import Assignment
from app.models.canonical_record import CanonicalRecord
from app.models.draft import Draft
from app.models.user import User
from app.projection.ros_projector import project_ros


def get_application_or_404(db: Session, application_id: UUID) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def get_assignment_for_application(db: Session, application_id: UUID) -> Optional[Assignment]:
    return db.query(Assignment).filter(Assignment.application_id == application_id).first()


def get_latest_draft(db: Session, application_id: UUID) -> Optional[Draft]:
    return (
        db.query(Draft)
        .filter(Draft.application_id == application_id)
        .order_by(Draft.version.desc(), Draft.created_at.desc())
        .first()
    )


def get_published_draft(db: Session, application_id: UUID) -> Optional[Draft]:
    return (
        db.query(Draft)
        .filter(Draft.application_id == application_id, Draft.is_published.is_(True))
        .order_by(Draft.version.desc(), Draft.created_at.desc())
        .first()
    )


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


def build_draft_summary(draft: Optional[Draft]) -> Optional[DraftSummary]:
    if not draft:
        return None
    return DraftSummary(
        id=draft.id,
        version=draft.version,
        is_published=draft.is_published,
        created_at=draft.created_at,
        content=draft.content,
    )


def build_application_list_item(
    application: Application,
    interviewer: Optional[User] = None,
) -> ApplicationListItem:
    return ApplicationListItem(
        id=application.id,
        status=application.status,
        is_hidden=application.is_hidden,
        created_at=application.created_at,
        assigned_interviewer=build_user_summary(interviewer),
    )


def build_admin_detail(
    application: Application,
    interviewer: Optional[User],
    review_package: Optional[ReviewPackageSummary],
    published_draft: Optional[Draft],
) -> ApplicationDetailAdmin:
    return ApplicationDetailAdmin(
        id=application.id,
        status=application.status,
        created_at=application.created_at,
        assigned_interviewer=build_user_summary(interviewer),
        review_package=review_package,
        published_draft=build_draft_summary(published_draft),
    )


def build_interviewer_detail(
    application: Application,
    interviewer: Optional[User],
    review_package: Optional[ReviewPackageSummary],
    latest_draft: Optional[Draft],
) -> ApplicationDetailInterviewer:
    return ApplicationDetailInterviewer(
        id=application.id,
        status=application.status,
        created_at=application.created_at,
        assigned_interviewer=build_user_summary(interviewer),
        review_package=review_package,
        latest_draft=build_draft_summary(latest_draft),
    )


def build_assignment_list_item(
    assignment: Assignment,
    application: Application,
    interviewer: User,
) -> AssignmentListItem:
    return AssignmentListItem(
        application_id=assignment.application_id,
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
