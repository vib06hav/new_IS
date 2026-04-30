export type UserRole = "admin" | "interviewer";

export type SessionUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  access_status: string;
  profile_image_url?: string | null;
};

export type SessionResponse = {
  user: SessionUser;
};

export type UserSummary = {
  id: string;
  name: string;
  email: string;
  profile_image_url?: string | null;
};

export type CanonicalSummary = {
  canonical_version: string;
  canonical_data: Record<string, unknown>;
};

export type ReviewPages123 = {
  page_1_background_profile: Record<string, unknown>;
  page_2_academic_and_engagement: Record<string, unknown>;
  page_3_essays: Record<string, unknown>;
};

export type ReviewPackageSummary = {
  canonical_version: string;
  pdf_url: string;
  pages_1_3: ReviewPages123;
};

export type FinalReportSummary = {
  id: string;
  report_version: string;
  created_at: string;
  content: Record<string, unknown>;
  export_url?: string | null;
};

export type InterviewWorkspaceStatus = "draft" | "launched" | "postgame" | "completed";
export type InterviewQuestionStatus = "unasked" | "satisfactory" | "mixed" | "unsatisfactory";

export type InterviewWorkspaceQuestion = {
  id: string;
  text: string;
  source: "generated" | "custom";
  status: InterviewQuestionStatus;
  note: string;
  order: number;
};

export type InterviewWorkspaceTheme = {
  id: string;
  source: "generated" | "custom";
  title: string;
  unifying_axis: string;
  interview_direction: string;
  question_group_title: string;
  questions: InterviewWorkspaceQuestion[];
};

export type InterviewWorkspaceContent = {
  themes: InterviewWorkspaceTheme[];
  final_summary: string;
};

export type InterviewWorkspaceSummary = {
  id: string;
  application_id: string;
  interviewer_id: string;
  status: InterviewWorkspaceStatus;
  content: InterviewWorkspaceContent;
  created_at: string;
  updated_at: string;
  launched_at?: string | null;
  completed_at?: string | null;
};

export type ReportChatTargetTab = "page1" | "page2" | "page3" | "page4" | "page5";

export type ReportChatSectionKey =
  | "page1_overview"
  | "page2_academics"
  | "page2_tests"
  | "page2_activities"
  | "page2_leadership"
  | "page3_essays"
  | "page4_focus_areas"
  | "page5_question_groups";

export type ReportChatRequestPayload = {
  question: string;
};

export type ReportChatSource = {
  label: string;
  target_tab: ReportChatTargetTab;
  section_key: ReportChatSectionKey;
  anchor_id: string;
  entity_id?: string | null;
  fragment_id?: string | null;
};

export type ReportChatResponse = {
  answer_summary: string;
  response_kind: "lookup" | "domain_summary" | "scope_redirect" | "degraded";
  sources: ReportChatSource[];
  not_found: boolean;
  response_state: "clean" | "repaired" | "retried" | "degraded";
};

export type ApplicationListItem = {
  id: string;
  display_id: string;
  status: string;
  is_hidden: boolean;
  is_hidden_for_interviewer: boolean;
  created_at: string;
  last_activity_at: string;
  assigned_interviewer?: UserSummary | null;
};

export type ApplicationUploadResponse = {
  id: string;
  display_id: string;
  status: string;
  created_at: string;
};

export type ApplicationDetailAdmin = {
  id: string;
  display_id: string;
  status: string;
  created_at: string;
  last_activity_at: string;
  assigned_interviewer?: UserSummary | null;
  review_package?: ReviewPackageSummary | null;
  final_report?: FinalReportSummary | null;
  interview_workspace?: InterviewWorkspaceSummary | null;
};

export type ApplicationDetailInterviewer = {
  id: string;
  display_id: string;
  status: string;
  created_at: string;
  last_activity_at: string;
  is_hidden_for_interviewer: boolean;
  assigned_interviewer?: UserSummary | null;
  review_package?: ReviewPackageSummary | null;
  final_report?: FinalReportSummary | null;
  interview_workspace?: InterviewWorkspaceSummary | null;
};

export type InterviewerListItem = {
  id: string;
  name: string;
  email: string;
  access_status: string;
  active_assignment_count: number;
  profile_image_url?: string | null;
};

export type InterviewerAssignmentSummaryItem = {
  application_id: string;
  application_display_id: string;
  status: string;
  current_interviewer?: UserSummary | null;
};

export type InterviewerAssignmentSummary = {
  interviewer_id: string;
  active_assignment_count: number;
  currently_assigned: InterviewerAssignmentSummaryItem[];
  available_to_assign: InterviewerAssignmentSummaryItem[];
  available_to_reassign: InterviewerAssignmentSummaryItem[];
};

export type InterviewerAssignmentSavePayload = {
  assigned_application_ids: string[];
};

export type LogoutResponse = {
  logout_url?: string | null;
};

export type AssignmentListItem = {
  application_id: string;
  application_display_id: string;
  status: string;
  assigned_at: string;
  interviewer: UserSummary;
};

export type ApplicationDisplayIdUpdatePayload = {
  display_id: string;
};

export type FinalReportMutationResponse = {
  application_id: string;
  status: string;
  final_report: FinalReportSummary;
};

export type CapacityStatus = {
  active: number;
  limit: number;
};

export type LLMCapacityStatusResponse = {
  generation: CapacityStatus;
  report_chat: CapacityStatus;
};
