from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Theme(BaseModel):
    theme_id: str
    title: str
    supporting_signal_ids: list[str]


class Signal(BaseModel):
    signal_id: str
    title: str
    core_observation: str
    interview_opening: str
    referenced_entity_ids: list[str]
    supporting_fragment_ids: list[str] = []
    supporting_det_signal_ids: list[str] = []


class QuestionCard(BaseModel):
    question_id: str
    question: str


class QuestionGroup(BaseModel):
    focus_area_id: str
    group_label: str
    line_of_inquiry: str
    questions: list[QuestionCard]
    source_theme_ids: list[str] = []
    source_signal_ids: list[str] = []


class FocusArea(BaseModel):
    focus_area_id: str
    title: str
    territory: str
    what_makes_it_worth_time: str
    source_theme_ids: list[str]
    source_signal_ids: list[str]


class Page4FocusAreas(BaseModel):
    focus_areas: list[FocusArea]


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


class InterviewWorkspaceFollowUp(BaseModel):
    id: str
    text: str
    source: Literal["custom"] = "custom"
    status: InterviewQuestionStatus = "unasked"
    note: str = ""
    order: int = 0


class InterviewWorkspaceQuestion(BaseModel):
    id: str
    text: str
    source: Literal["generated", "custom"]
    status: InterviewQuestionStatus = "unasked"
    note: str = ""
    order: int = 0
    follow_ups: list[InterviewWorkspaceFollowUp] = Field(default_factory=list)


class InterviewWorkspaceTheme(BaseModel):
    id: str
    source: Literal["generated", "custom"]
    title: str
    interview_direction: str
    territory: str = ""
    what_makes_it_worth_time: str = ""
    question_group_title: str
    questions: list[InterviewWorkspaceQuestion] = Field(default_factory=list)


class InterviewWorkspaceContent(BaseModel):
    themes: list[InterviewWorkspaceTheme]
    final_summary: str = ""


OpeningCard = QuestionCard
OpeningGroup = QuestionGroup
Page5InterviewOpenings = Page5QuestionGroups
InterviewWorkspaceOpening = InterviewWorkspaceQuestion


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
    access_status: str
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
ReportChatSurfaceType = Literal["report_viewer", "configure", "overlay", "postgame", "final_report"]
ReportChatWorkflowStage = Literal["prep", "live_interview", "postgame", "completed"]
ReportChatCurrentPage = Literal["page1", "page2", "page3", "page4", "page5", "page6", "configure", "overlay", "postgame"]
ReportChatSectionKey = Literal[
    "page1_overview",
    "page2_academics",
    "page2_tests",
    "page2_activities",
    "page2_leadership",
    "page3_essays",
    "page4_focus_areas",
    "page5_interview_openings",
]
ReportChatResponseState = Literal["clean", "repaired", "retried", "degraded"]
ReportChatResponseKind = Literal["content", "workflow", "action", "mixed", "degraded"]
InterviewRefinementMode = Literal["question_note", "follow_up_note", "final_summary"]


class ReportChatRequest(BaseModel):
    question: str
    surface_type: ReportChatSurfaceType = "report_viewer"
    current_page: Optional[ReportChatCurrentPage] = None
    workflow_stage: Optional[ReportChatWorkflowStage] = None
    available_actions: list[str] = Field(default_factory=list)


class ReportChatSource(BaseModel):
    label: str
    target_tab: ReportChatTargetTab
    section_key: ReportChatSectionKey
    anchor_id: str
    entity_id: Optional[str] = None
    fragment_id: Optional[str] = None


class ReportChatResponse(BaseModel):
    answer_summary: str
    response_kind: ReportChatResponseKind = "content"
    sources: list[ReportChatSource]
    not_found: bool
    response_state: ReportChatResponseState = "clean"
    suggested_followups: list[str] = Field(default_factory=list)


class InterviewWorkspaceUpsertRequest(BaseModel):
    content: InterviewWorkspaceContent


class InterviewWorkspaceRefinementRequest(BaseModel):
    mode: InterviewRefinementMode
    text: str
    instruction: str = ""
    content: InterviewWorkspaceContent
    theme_id: Optional[str] = None
    question_id: Optional[str] = None
    follow_up_id: Optional[str] = None


class InterviewWorkspaceRefinementResponse(BaseModel):
    refined_text: str


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
