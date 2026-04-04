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

export type DraftSummary = {
  id: string;
  version: number;
  is_published: boolean;
  created_at: string;
  content: Record<string, unknown>;
};

export type ApplicationListItem = {
  id: string;
  status: string;
  is_hidden: boolean;
  created_at: string;
  assigned_interviewer?: UserSummary | null;
};

export type ApplicationUploadResponse = {
  id: string;
  status: string;
  created_at: string;
};

export type ApplicationDetailAdmin = {
  id: string;
  status: string;
  created_at: string;
  assigned_interviewer?: UserSummary | null;
  review_package?: ReviewPackageSummary | null;
  published_draft?: DraftSummary | null;
};

export type ApplicationDetailInterviewer = {
  id: string;
  status: string;
  created_at: string;
  assigned_interviewer?: UserSummary | null;
  review_package?: ReviewPackageSummary | null;
  latest_draft?: DraftSummary | null;
};

export type InterviewerListItem = {
  id: string;
  name: string;
  email: string;
  active_assignment_count: number;
};

export type InterviewerAssignmentSummaryItem = {
  application_id: string;
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

export type AssignmentListItem = {
  application_id: string;
  status: string;
  assigned_at: string;
  interviewer: UserSummary;
};

export type DraftMutationResponse = {
  application_id: string;
  status: string;
  draft: DraftSummary;
};
