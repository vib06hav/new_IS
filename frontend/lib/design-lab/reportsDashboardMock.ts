import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";

export const reportsDashboardStatuses = ["ALL", "READY", "ASSIGNED", "DRAFT", "PUBLISHED", "HIDDEN"] as const;

export const reportsDashboardInterviewers: InterviewerListItem[] = [
  {
    id: "intr-001",
    name: "Rhea Kapoor",
    email: "rhea.kapoor@example.com",
    active_assignment_count: 6,
  },
  {
    id: "intr-002",
    name: "Aanya Sen",
    email: "aanya.sen@example.com",
    active_assignment_count: 4,
  },
  {
    id: "intr-003",
    name: "Kabir Mehta",
    email: "kabir.mehta@example.com",
    active_assignment_count: 3,
  },
];

export const reportsDashboardItems: ApplicationListItem[] = [
  {
    id: "app-001",
    display_id: "PLK-2026-0142",
    status: "READY",
    is_hidden: false,
    created_at: "2026-03-24T10:15:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-24T10:15:00.000Z",
  },
  {
    id: "app-002",
    display_id: "PLK-2026-0148",
    status: "ASSIGNED",
    is_hidden: false,
    created_at: "2026-03-24T12:40:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-24T16:10:00.000Z",
    assigned_interviewer: {
      id: "intr-001",
      name: "Rhea Kapoor",
      email: "rhea.kapoor@example.com",
    },
  },
  {
    id: "app-003",
    display_id: "PLK-2026-0157",
    status: "DRAFT",
    is_hidden: false,
    created_at: "2026-03-25T09:05:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-25T15:45:00.000Z",
    assigned_interviewer: {
      id: "intr-002",
      name: "Aanya Sen",
      email: "aanya.sen@example.com",
    },
  },
  {
    id: "app-004",
    display_id: "PLK-2026-0163",
    status: "PUBLISHED",
    is_hidden: false,
    created_at: "2026-03-25T14:30:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-26T09:35:00.000Z",
    assigned_interviewer: {
      id: "intr-003",
      name: "Kabir Mehta",
      email: "kabir.mehta@example.com",
    },
  },
  {
    id: "app-005",
    display_id: "PLK-2026-0169",
    status: "PUBLISHED",
    is_hidden: true,
    created_at: "2026-03-26T11:20:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-26T11:20:00.000Z",
    assigned_interviewer: {
      id: "intr-001",
      name: "Rhea Kapoor",
      email: "rhea.kapoor@example.com",
    },
  },
  {
    id: "app-006",
    display_id: "PLK-2026-0171",
    status: "READY",
    is_hidden: false,
    created_at: "2026-03-27T08:10:00.000Z",
    is_hidden_for_interviewer: false,
    last_activity_at: "2026-03-27T08:10:00.000Z",
  },
];

export const reportsDashboardMetrics = {
  ready: reportsDashboardItems.filter((item) => item.status === "READY").length,
  assigned: reportsDashboardItems.filter((item) => item.status === "ASSIGNED").length,
  draft: reportsDashboardItems.filter((item) => item.status === "DRAFT").length,
  published: reportsDashboardItems.filter((item) => item.status === "PUBLISHED").length,
};
