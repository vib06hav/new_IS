export type UserRole = "admin" | "interviewer";

export type SessionUser = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
};

export type SessionResponse = {
  user: SessionUser;
};

export type UserSummary = {
  id: string;
  name: string;
  email: string;
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
};

export type InterviewerListItem = {
  id: string;
  name: string;
  email: string;
  active_assignment_count: number;
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

export type InterviewerUpdatePayload = {
  name: string;
  email: string;
};

export type PasswordChangePayload = {
  new_password: string;
};

export type InterviewerAssignmentSavePayload = {
  assigned_application_ids: string[];
};

export type SelfPasswordChangePayload = {
  current_password: string;
  new_password: string;
};

export type SelfProfileUpdatePayload = {
  name: string;
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
