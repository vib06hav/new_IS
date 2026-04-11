"use client";

import { useEffect, useState } from "react";
import { ReviewPageOneSection, ReviewPageThreeSection, ReviewPageTwoSection } from "@/components/ReviewPackagePages";
import { SynthesisReportSection } from "@/components/SynthesisReportSection";
import type { ReviewPackageSummary } from "@/lib/types";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

export type ReviewPageTab = "page1" | "page2" | "page3" | "page4" | "page5";

export function ReviewPackageSection({
  reviewPackage,
  annotationSource,
  activeTab: controlledActiveTab,
  onActiveTabChange,
}: {
  reviewPackage: ReviewPackageSummary;
  annotationSource?: Record<string, unknown> | null;
  activeTab?: ReviewPageTab;
  onActiveTabChange?: (tab: ReviewPageTab) => void;
}) {
  const [internalActiveTab, setInternalActiveTab] = useState<ReviewPageTab>("page1");
  const annotations = extractAnnotations(annotationSource);
  const hasSynthesisContent = Boolean(annotationSource);
  const activeTab = controlledActiveTab ?? internalActiveTab;
  const setActiveTab = onActiveTabChange ?? setInternalActiveTab;
  const navOptions: Array<{ value: ReviewPageTab; label: string; meta: string }> = [
    { value: "page1", label: "Overview", meta: "Applicant profile" },
    { value: "page2", label: "Academics & Activities", meta: "Study and engagement" },
    { value: "page3", label: "Writing", meta: "Essays and excerpts" },
    ...(hasSynthesisContent
      ? [
          { value: "page4" as const, label: "Focus Areas", meta: "Themes and signals" },
          { value: "page5" as const, label: "Questions", meta: "Interview prompts" },
        ]
      : []),
  ];

  useEffect(() => {
    if (!hasSynthesisContent && (activeTab === "page4" || activeTab === "page5")) {
      setActiveTab("page1");
    }
  }, [activeTab, hasSynthesisContent]);

  return (
    <div className="space-y-5">
      {controlledActiveTab === undefined && !onActiveTabChange ? (
        <div className="flex justify-end">
          <div className="max-w-full rounded-[1.6rem] border border-[rgba(191,219,254,0.95)] bg-[linear-gradient(135deg,rgba(219,234,254,0.96),rgba(239,246,255,0.94),rgba(224,231,255,0.9))] px-3 py-3 shadow-[0_18px_36px_rgba(148,163,184,0.18),inset_0_1px_0_rgba(255,255,255,0.6)] backdrop-blur">
            <SegmentedControl value={activeTab} onChange={setActiveTab} options={navOptions} />
          </div>
        </div>
      ) : null}
      <div className="fade-rise">
        {activeTab === "page1" ? (
          <ReviewPageOneSection data={reviewPackage.pages_1_3.page_1_background_profile} />
        ) : null}
        {activeTab === "page2" ? (
          <ReviewPageTwoSection
            data={reviewPackage.pages_1_3.page_2_academic_and_engagement}
            annotations={annotations}
          />
        ) : null}
        {activeTab === "page3" ? (
          <ReviewPageThreeSection data={reviewPackage.pages_1_3.page_3_essays} annotations={annotations} />
        ) : null}
        {activeTab === "page4" && annotationSource ? (
          <SynthesisReportSection
            report={annotationSource}
            title="Focus Areas"
            description="Themes, signals, and what still needs resolution."
            initialTab="page4"
            hideInternalTabs
          />
        ) : null}
        {activeTab === "page5" && annotationSource ? (
          <SynthesisReportSection
            report={annotationSource}
            title="Interview Questions"
            description="Question groups derived from the synthesized themes."
            initialTab="page5"
            hideInternalTabs
          />
        ) : null}
      </div>
    </div>
  );
}

function extractAnnotations(source?: Record<string, unknown> | null) {
  const signalData = source?.signal_data;
  if (!signalData || typeof signalData !== "object" || Array.isArray(signalData)) {
    return null;
  }

  const annotations = (signalData as Record<string, unknown>).annotations;
  if (!annotations || typeof annotations !== "object" || Array.isArray(annotations)) {
    return null;
  }

  return annotations as {
    page_2_entities?: Record<string, { signal_ids?: string[]; theme_ids?: string[] }>;
    page_3_fragments?: Record<
      string,
      Array<{ fragment_id: string; start_char: number; end_char: number; signal_ids?: string[]; theme_ids?: string[] }>
    >;
  };
}
