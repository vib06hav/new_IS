from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Theme(BaseModel):
    theme_id: str
    title: str
    unifying_axis: str
    interview_direction: str
    supporting_signal_ids: list[str]
    referenced_entity_ids: list[str]


class Signal(BaseModel):
    signal_id: str
    theme_id: str
    title: str
    evidence_anchor: str
    direct_read: str
    depth_opening: str
    why_it_matters: str
    referenced_entity_ids: list[str]


class QuestionGroup(BaseModel):
    theme_id: str
    group_title: str
    questions: list[str]


class Page4FocusAreas(BaseModel):
    themes: list[Theme]
    signals: list[Signal]


class Page5QuestionGroups(BaseModel):
    question_groups: list[QuestionGroup]


class SynthesisOutput(BaseModel):
    report_metadata: Dict[str, Any]
    page_1_background_profile: Dict[str, Any]
    page_2_academic_and_engagement: Dict[str, Any]
    page_3_essays: Dict[str, Any]
    page_4_focus_areas: Page4FocusAreas
    page_5_question_groups: Page5QuestionGroups


class UserSummary(BaseModel):
    id: UUID
    name: str
    email: str


class DraftSummary(BaseModel):
    id: UUID
    version: int
    is_published: bool
    created_at: datetime
    content: Dict[str, Any]


class CanonicalSummary(BaseModel):
    canonical_version: str
    canonical_data: Dict[str, Any]


class ReviewPages123(BaseModel):
    page_1_background_profile: Dict[str, Any]
    page_2_academic_and_engagement: Dict[str, Any]
    page_3_essays: Dict[str, Any]


class ReviewPackageSummary(BaseModel):
    canonical_version: str
    pdf_url: str
    pages_1_3: ReviewPages123


class ApplicationUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: str
    status: str
    created_at: datetime


class ApplicationListItem(BaseModel):
    id: UUID
    display_id: str
    status: str
    is_hidden: bool = False
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None


class ApplicationDetailAdmin(BaseModel):
    id: UUID
    display_id: str
    status: str
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None
    review_package: Optional[ReviewPackageSummary] = None
    published_draft: Optional[DraftSummary] = None


class ApplicationDetailInterviewer(BaseModel):
    id: UUID
    display_id: str
    status: str
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None
    review_package: Optional[ReviewPackageSummary] = None
    latest_draft: Optional[DraftSummary] = None


class AssignmentUpsertRequest(BaseModel):
    interviewer_id: UUID


class ApplicationDisplayIdUpdateRequest(BaseModel):
    display_id: str


class AssignmentListItem(BaseModel):
    application_id: UUID
    application_display_id: str
    status: str
    assigned_at: datetime
    interviewer: UserSummary


class InterviewerListItem(BaseModel):
    id: UUID
    name: str
    email: str
    active_assignment_count: int


class DraftMutationResponse(BaseModel):
    application_id: UUID
    status: str
    draft: DraftSummary


class InterviewerAssignmentSummaryItem(BaseModel):
    application_id: UUID
    application_display_id: str
    status: str
    current_interviewer: Optional[UserSummary] = None


class InterviewerAssignmentSummary(BaseModel):
    interviewer_id: UUID
    active_assignment_count: int
    currently_assigned: list[InterviewerAssignmentSummaryItem]
    available_to_assign: list[InterviewerAssignmentSummaryItem]
    available_to_reassign: list[InterviewerAssignmentSummaryItem]


class InterviewerAssignmentSaveRequest(BaseModel):
    assigned_application_ids: list[UUID]
