import type {
  ReportChatCurrentPage,
  ReportChatSectionKey,
  ReportChatSource,
  ReportChatSurfaceType,
  ReportChatTargetTab,
  ReportChatWorkflowStage,
} from "@/lib/types";

const SECTION_META: Record<ReportChatSectionKey, { pageLabel: string; sectionLabel: string }> = {
  page1_overview: { pageLabel: "Page 1", sectionLabel: "Overview" },
  page2_academics: { pageLabel: "Page 2", sectionLabel: "Academics" },
  page2_tests: { pageLabel: "Page 2", sectionLabel: "Tests" },
  page2_activities: { pageLabel: "Page 2", sectionLabel: "Activities" },
  page2_leadership: { pageLabel: "Page 2", sectionLabel: "Leadership" },
  page3_essays: { pageLabel: "Page 3", sectionLabel: "Writing" },
  page4_focus_areas: { pageLabel: "Page 4", sectionLabel: "Focus Areas" },
  page5_interview_openings: { pageLabel: "Page 5", sectionLabel: "Interview Openings" },
};

const PAGE_LABELS: Record<ReportChatCurrentPage, string> = {
  page1: "Page 1 Overview",
  page2: "Page 2 Academics & Activities",
  page3: "Page 3 Writing",
  page4: "Page 4 Focus Areas",
  page5: "Page 5 Interview Openings",
  page6: "Page 6 Final Report",
  configure: "Configure Workspace",
  overlay: "Interview Overlay",
  postgame: "Postgame Review",
};

const STAGE_LABELS: Record<ReportChatWorkflowStage, string> = {
  prep: "Prep",
  live_interview: "Live Interview",
  postgame: "Postgame",
  completed: "Completed",
};

export function getReportChatSourceLabel(source: ReportChatSource) {
  if (source.label?.trim()) {
    return source.label;
  }

  const meta = SECTION_META[source.section_key];
  return `${meta.pageLabel} - ${meta.sectionLabel}`;
}

export function getReportChatPageLabel(currentPage: ReportChatCurrentPage | null | undefined) {
  if (!currentPage) return "Report";
  return PAGE_LABELS[currentPage];
}

export function getReportChatStageLabel(workflowStage: ReportChatWorkflowStage | null | undefined) {
  if (!workflowStage) return "Prep";
  return STAGE_LABELS[workflowStage];
}

export function getReportCopilotStarters({
  surfaceType,
  currentPage,
  workflowStage,
}: {
  surfaceType: ReportChatSurfaceType;
  currentPage?: ReportChatCurrentPage | null;
  workflowStage?: ReportChatWorkflowStage | null;
}) {
  if (surfaceType === "final_report" || currentPage === "page6" || workflowStage === "completed") {
    return [
      "Summarize the final interview outcome",
      "Compare the final interview report with the earlier report",
      "Which themes held up after the interview?",
    ];
  }

  if (surfaceType === "overlay" || workflowStage === "live_interview") {
    return [
      "What should I probe next?",
      "Which theme still feels unresolved?",
      "What follow-up question would be useful here?",
    ];
  }

  if (surfaceType === "postgame" || workflowStage === "postgame") {
    return [
      "What gaps remain in the interview notes?",
      "Help me tighten the final summary",
      "Which interview-opening outcomes look mixed or unresolved?",
    ];
  }

  if (surfaceType === "configure") {
    return [
      "How should I prepare from this report?",
      "Which opening groups should I refine first?",
      "What should I ask about this profile?",
    ];
  }

  if (currentPage === "page4") {
    return [
      "Explain the main focus areas",
      "Which signals matter most here?",
      "How should these themes shape the interview?",
    ];
  }

  if (currentPage === "page5") {
    return [
      "How should I use these openings in the interview?",
      "Which opening group should I prioritize first?",
      "What follow-ups would deepen one of these openings?",
    ];
  }

  return [
    "What stands out across this report?",
    "Summarize this page for me",
    "What should I ask about this student?",
  ];
}

export async function navigateToReportResult(
  result: Pick<ReportChatSource, "anchor_id" | "target_tab" | "entity_id">,
  setActiveTab: (tab: ReportChatTargetTab) => void,
) {
  setActiveTab(result.target_tab);

  for (let attempt = 0; attempt < 8; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, attempt === 0 ? 30 : 80));

    if (result.entity_id) {
      const entityButton = document.getElementById(`report-entity-${result.entity_id.toLowerCase()}`);
      if (entityButton instanceof HTMLButtonElement) {
        entityButton.click();
        entityButton.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }

    const element = document.getElementById(result.anchor_id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
  }
}
