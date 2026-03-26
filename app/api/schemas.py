from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Theme(BaseModel):
    theme_id: str
    title: str
    framing: str
    what_this_theme_must_resolve: str
    supporting_signal_ids: list[str]
    referenced_entity_ids: list[str]


class Signal(BaseModel):
    signal_id: str
    theme_id: str
    title: str
    evidence_anchor: str
    direct_read: str
    what_remains_open: str
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


class ApplicationUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    created_at: datetime


class ApplicationListItem(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None


class ApplicationDetailAdmin(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None
    canonical: Optional[CanonicalSummary] = None
    published_draft: Optional[DraftSummary] = None


class ApplicationDetailInterviewer(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    assigned_interviewer: Optional[UserSummary] = None
    canonical: Optional[CanonicalSummary] = None
    latest_draft: Optional[DraftSummary] = None


class AssignmentUpsertRequest(BaseModel):
    interviewer_id: UUID


class AssignmentListItem(BaseModel):
    application_id: UUID
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
