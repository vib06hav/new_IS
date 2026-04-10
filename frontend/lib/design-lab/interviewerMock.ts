import type { ApplicationDetailInterviewer } from "@/lib/types";
import finalRos from "../../../tests/stage17_fake_llm_output/09_final_ros.json";

type RosPayload = typeof finalRos;

const report = finalRos as RosPayload;

export const mockInterviewerApplication: ApplicationDetailInterviewer = {
  id: "design-lab-app-001",
  display_id: "PLK-2026-0142",
  status: "DRAFT",
  created_at: "2026-03-24T10:15:00.000Z",
  last_activity_at: "2026-03-26T14:45:00.000Z",
  is_hidden_for_interviewer: false,
  assigned_interviewer: {
    id: "interviewer-001",
    name: "Rhea Kapoor",
    email: "rhea.kapoor@example.com",
  },
  review_package: {
    canonical_version: report.report_metadata.canonical_version,
    pdf_url: "/design-lab/source.pdf",
    pages_1_3: {
      page_1_background_profile: report.page_1_background_profile,
      page_2_academic_and_engagement: report.page_2_academic_and_engagement,
      page_3_essays: report.page_3_essays,
    },
  },
  latest_draft: {
    id: "draft-003",
    version: 3,
    is_published: false,
    created_at: "2026-03-26T00:00:00.000Z",
    content: {
      page_4_focus_areas: report.page_4_focus_areas,
      page_5_question_groups: report.page_5_question_groups,
      signal_data: report.signal_data,
    },
  },
};

export const mockPublishedInterviewerApplication: ApplicationDetailInterviewer = {
  ...mockInterviewerApplication,
  id: "design-lab-app-published-001",
  display_id: "Dummy App (5)_v8_filled",
  status: "PUBLISHED",
  last_activity_at: "2026-04-10T17:10:18.000Z",
  assigned_interviewer: {
    id: "interviewer-vib",
    name: "vib",
    email: "vib@example.com",
  },
  latest_draft: {
    id: "draft-published-001",
    version: 4,
    is_published: true,
    created_at: "2026-04-10T17:10:18.000Z",
    content: {
      page_4_focus_areas: report.page_4_focus_areas,
      page_5_question_groups: report.page_5_question_groups,
      signal_data: report.signal_data,
    },
  },
};

export const designLabSummary = {
  title: "Interviewer Page Sandbox",
  description:
    "Current production shell versus redesigned page-level wrappers around the same report content.",
};
