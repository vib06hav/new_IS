import type { ReportChatSectionKey, ReportChatSource, ReportChatTargetTab } from "@/lib/types";

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

export function getReportChatSourceLabel(source: ReportChatSource) {
  if (source.label?.trim()) {
    return source.label;
  }

  const meta = SECTION_META[source.section_key];
  return `${meta.pageLabel} · ${meta.sectionLabel}`;
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
