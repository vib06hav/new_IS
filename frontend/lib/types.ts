export type UserRole = "admin" | "interviewer";

export type TokenResponse = {
  access_token: string;
  token_type: string;
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
