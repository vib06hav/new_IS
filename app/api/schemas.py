from datetime import datetime
from typing import Any, Dict, Literal, Optional
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
    profile_image_url: Optional[str] = None


class FinalReportSummary(BaseModel):
    id: UUID
    report_version: str
    created_at: datetime
    content: Dict[str, Any]
    export_url: Optional[str] = None


InterviewWorkspaceStatus = Literal["draft", "launched", "postgame", "completed"]
InterviewQuestionStatus = Literal["unasked", "satisfactory", "mixed", "unsatisfactory"]


class InterviewWorkspaceQuestion(BaseModel):
    id: str
    text: str
    source: Literal["generated", "custom"]
    status: InterviewQuestionStatus = "unasked"
    note: str = ""
    order: int = 0


class InterviewWorkspaceTheme(BaseModel):
    id: str
    source: Literal["generated", "custom"]
    title: str
    unifying_axis: str
    interview_direction: str
    question_group_title: str
    questions: list[InterviewWorkspaceQuestion]


class InterviewWorkspaceContent(BaseModel):
    themes: list[InterviewWorkspaceTheme]
    final_summary: str = ""


class InterviewWorkspaceSummary(BaseModel):
    id: UUID
    application_id: UUID
    interviewer_id: UUID
    status: InterviewWorkspaceStatus
    content: InterviewWorkspaceContent
    created_at: datetime
    updated_at: datetime
    launched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


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
    is_hidden_for_interviewer: bool = False
    created_at: datetime
    last_activity_at: datetime
    assigned_interviewer: Optional[UserSummary] = None


class ApplicationDetailAdmin(BaseModel):
    id: UUID
    display_id: str
    status: str
    created_at: datetime
    last_activity_at: datetime
    assigned_interviewer: Optional[UserSummary] = None
    review_package: Optional[ReviewPackageSummary] = None
    final_report: Optional[FinalReportSummary] = None
    interview_workspace: Optional[InterviewWorkspaceSummary] = None


class ApplicationDetailInterviewer(BaseModel):
    id: UUID
    display_id: str
    status: str
    created_at: datetime
    last_activity_at: datetime
    is_hidden_for_interviewer: bool = False
    assigned_interviewer: Optional[UserSummary] = None
    review_package: Optional[ReviewPackageSummary] = None
    final_report: Optional[FinalReportSummary] = None
    interview_workspace: Optional[InterviewWorkspaceSummary] = None


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
    profile_image_url: Optional[str] = None


class FinalReportMutationResponse(BaseModel):
    application_id: UUID
    status: str
    final_report: FinalReportSummary


class CapacityStatus(BaseModel):
    active: int
    limit: int


class LLMCapacityStatusResponse(BaseModel):
    generation: CapacityStatus
    report_chat: CapacityStatus


ReportChatTargetTab = Literal["page1", "page2", "page3", "page4", "page5"]
ReportChatSectionKey = Literal[
    "page1_overview",
    "page2_academics",
    "page2_tests",
    "page2_activities",
    "page2_leadership",
    "page3_essays",
    "page4_focus_areas",
    "page5_question_groups",
]
ReportChatResponseState = Literal["clean", "repaired", "retried", "degraded"]


class ReportChatRequest(BaseModel):
    question: str


class ReportChatResult(BaseModel):
    label: str
    value: str
    target_tab: ReportChatTargetTab
    section_key: ReportChatSectionKey
    anchor_id: str


class ReportChatResponse(BaseModel):
    answer_summary: str
    results: list[ReportChatResult]
    not_found: bool
    response_state: ReportChatResponseState = "clean"


class InterviewWorkspaceUpsertRequest(BaseModel):
    content: InterviewWorkspaceContent


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
