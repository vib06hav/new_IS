"use client";

import { useEffect, useState } from "react";
import { ReviewPageOneSection, ReviewPageThreeSection, ReviewPageTwoSection } from "@/components/ReviewPackagePages";
import { SynthesisReportSection } from "@/components/SynthesisReportSection";
import type { ReviewPackageSummary } from "@/lib/types";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

export type ReviewPageTab = "page1" | "page2" | "page3" | "page4" | "page5" | "page6";

type ThemeRecord = {
  theme_id?: string;
  title?: string;
  unifying_axis?: string;
  interview_direction?: string;
  supporting_signal_ids?: string[];
};

type SignalRecord = {
  signal_id?: string;
  theme_id?: string;
  title?: string;
  direct_read?: string;
  why_it_matters?: string;
  depth_opening?: string;
};

type ReviewAnnotationContext = {
  page_2_entities?: Record<string, { signal_ids?: string[]; theme_ids?: string[] }>;
  page_3_fragments?: Record<
    string,
    Array<{ fragment_id: string; start_char: number; end_char: number; signal_ids?: string[]; theme_ids?: string[] }>
  >;
  themes?: ThemeRecord[];
  signals?: SignalRecord[];
};

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
  const annotationContext = extractAnnotationContext(annotationSource);
  const hasSynthesisContent = Boolean(annotationSource);
  const activeTab = controlledActiveTab ?? internalActiveTab;
  const setActiveTab = onActiveTabChange ?? setInternalActiveTab;
  const navOptions: Array<{ value: ReviewPageTab; label: string; meta: string }> = [
    { value: "page1", label: "Overview", meta: "Applicant profile" },
    { value: "page2", label: "Academics & Activities", meta: "Study and engagement" },
    { value: "page3", label: "Writing", meta: "Essays and excerpts" },
    ...(hasSynthesisContent
      ? [
          { value: "page4" as const, label: "Focus Areas", meta: "Interview brief" },
          { value: "page5" as const, label: "Question Sets", meta: "Interview prompts" },
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
          <div className="max-w-full rounded-[1.5rem] border border-slate-200 bg-white/80 px-3 py-3 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
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
            annotations={annotationContext}
          />
        ) : null}
        {activeTab === "page3" ? (
          <ReviewPageThreeSection data={reviewPackage.pages_1_3.page_3_essays} annotations={annotationContext} />
        ) : null}
        {activeTab === "page4" && annotationSource ? (
          <SynthesisReportSection
            report={annotationSource}
            title="Focus Areas"
            description="Synthesized focus areas for interview preparation."
            initialTab="page4"
            hideInternalTabs
          />
        ) : null}
        {activeTab === "page5" && annotationSource ? (
          <SynthesisReportSection
            report={annotationSource}
            title="Question Sets"
            description="Grouped interview questions derived from the focus areas."
            initialTab="page5"
            hideInternalTabs
          />
        ) : null}
      </div>
    </div>
  );
}

function extractAnnotationContext(source?: Record<string, unknown> | null): ReviewAnnotationContext | null {
  const signalData = source?.signal_data;
  if (!signalData || typeof signalData !== "object" || Array.isArray(signalData)) {
    return null;
  }

  const annotations = (signalData as Record<string, unknown>).annotations;
  if (!annotations || typeof annotations !== "object" || Array.isArray(annotations)) {
    return null;
  }

  const themes = Array.isArray((signalData as Record<string, unknown>).themes)
    ? ((signalData as Record<string, unknown>).themes as ThemeRecord[])
    : [];
  const signals = Array.isArray((signalData as Record<string, unknown>).signals)
    ? ((signalData as Record<string, unknown>).signals as SignalRecord[])
    : [];

  return {
    ...(annotations as ReviewAnnotationContext),
    themes,
    signals,
  };
}
