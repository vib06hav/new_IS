import type { ReportChatResult, ReportChatSectionKey, ReportChatTargetTab } from "@/lib/types";

const SECTION_META: Record<ReportChatSectionKey, { pageLabel: string; sectionLabel: string }> = {
  page1_overview: { pageLabel: "Page 1", sectionLabel: "Overview" },
  page2_academics: { pageLabel: "Page 2", sectionLabel: "Academics" },
  page2_tests: { pageLabel: "Page 2", sectionLabel: "Tests" },
  page2_activities: { pageLabel: "Page 2", sectionLabel: "Activities" },
  page2_leadership: { pageLabel: "Page 2", sectionLabel: "Leadership" },
  page3_essays: { pageLabel: "Page 3", sectionLabel: "Writing" },
  page4_focus_areas: { pageLabel: "Page 4", sectionLabel: "Focus Areas" },
  page5_question_groups: { pageLabel: "Page 5", sectionLabel: "Questions" },
};

export function getReportChatSourceLabel(result: ReportChatResult) {
  const meta = SECTION_META[result.section_key];
  return `${meta.pageLabel} · ${meta.sectionLabel}`;
}

export async function navigateToReportResult(
  result: Pick<ReportChatResult, "anchor_id" | "target_tab">,
  setActiveTab: (tab: ReportChatTargetTab) => void,
) {
  setActiveTab(result.target_tab);

  for (let attempt = 0; attempt < 8; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, attempt === 0 ? 30 : 80));
    const element = document.getElementById(result.anchor_id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
  }
}
