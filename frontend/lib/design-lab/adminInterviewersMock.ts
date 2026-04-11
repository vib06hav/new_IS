import type {
  InterviewerAssignmentSummary,
  InterviewerListItem,
  UserSummary,
} from "@/lib/types";

type AdminInterviewerSandboxState = {
  interviewers: InterviewerListItem[];
  metrics: {
    interviewers: number;
    activeAssignments: number;
    readyPool: number;
  };
  selectedInterviewer: InterviewerListItem;
  assignmentInterviewer: InterviewerListItem;
  assignmentSummary: InterviewerAssignmentSummary;
  createDraft: {
    name: string;
    email: string;
    password: string;
    confirmPassword: string;
  };
};

const interviewerA: UserSummary = {
  id: "intr-001",
  name: "Rhea Kapoor",
  email: "rhea.kapoor@example.com",
};

const interviewerB: UserSummary = {
  id: "intr-002",
  name: "Aanya Sen",
  email: "aanya.sen@example.com",
};

const interviewerC: UserSummary = {
  id: "intr-003",
  name: "Kabir Mehta",
  email: "kabir.mehta@example.com",
};

export const adminInterviewersSandboxState: AdminInterviewerSandboxState = {
  interviewers: [
    {
      id: interviewerA.id,
      name: interviewerA.name,
      email: interviewerA.email,
      active_assignment_count: 6,
    },
    {
      id: interviewerB.id,
      name: interviewerB.name,
      email: interviewerB.email,
      active_assignment_count: 4,
    },
    {
      id: interviewerC.id,
      name: interviewerC.name,
      email: interviewerC.email,
      active_assignment_count: 3,
    },
    {
      id: "intr-004",
      name: "Nisha Rao",
      email: "nisha.rao@example.com",
      active_assignment_count: 2,
    },
    {
      id: "intr-005",
      name: "Arjun Malhotra",
      email: "arjun.malhotra@example.com",
      active_assignment_count: 1,
    },
  ],
  metrics: {
    interviewers: 5,
    activeAssignments: 16,
    readyPool: 11,
  },
  selectedInterviewer: {
    id: interviewerA.id,
    name: interviewerA.name,
    email: interviewerA.email,
    active_assignment_count: 6,
  },
  assignmentInterviewer: {
    id: interviewerA.id,
    name: interviewerA.name,
    email: interviewerA.email,
    active_assignment_count: 6,
  },
  assignmentSummary: {
    interviewer_id: interviewerA.id,
    active_assignment_count: 6,
    currently_assigned: [
      {
        application_id: "app-001",
        application_display_id: "PLK-2026-0142",
        status: "COMPLETE",
        current_interviewer: interviewerA,
      },
      {
        application_id: "app-002",
        application_display_id: "PLK-2026-0148",
        status: "ASSIGNED",
        current_interviewer: interviewerA,
      },
      {
        application_id: "app-003",
        application_display_id: "PLK-2026-0157",
        status: "ASSIGNED",
        current_interviewer: interviewerA,
      },
      {
        application_id: "app-004",
        application_display_id: "PLK-2026-0163",
        status: "COMPLETE",
        current_interviewer: interviewerA,
      },
    ],
    available_to_assign: [
      {
        application_id: "app-005",
        application_display_id: "PLK-2026-0169",
        status: "COMPLETE",
      },
      {
        application_id: "app-006",
        application_display_id: "PLK-2026-0171",
        status: "COMPLETE",
      },
      {
        application_id: "app-007",
        application_display_id: "PLK-2026-0178",
        status: "ASSIGNED",
      },
    ],
    available_to_reassign: [
      {
        application_id: "app-008",
        application_display_id: "PLK-2026-0184",
        status: "ASSIGNED",
        current_interviewer: interviewerB,
      },
      {
        application_id: "app-009",
        application_display_id: "PLK-2026-0189",
        status: "ASSIGNED",
        current_interviewer: interviewerC,
      },
      {
        application_id: "app-010",
        application_display_id: "PLK-2026-0193",
        status: "ASSIGNED",
        current_interviewer: interviewerB,
      },
    ],
  },
  createDraft: {
    name: "Aarav Desai",
    email: "aarav.desai@example.com",
    password: "••••••••",
    confirmPassword: "••••••••",
  },
};
