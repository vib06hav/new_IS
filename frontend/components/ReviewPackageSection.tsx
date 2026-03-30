"use client";

import { useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { ReviewPageOneSection, ReviewPageThreeSection, ReviewPageTwoSection } from "@/components/ReviewPackagePages";
import { fetchSourcePdf } from "@/lib/api";
import type { ReviewPackageSummary } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

type ReviewPageTab = "page1" | "page2" | "page3";

export function ReviewPackageSection({
  reviewPackage,
  applicationId,
  roleLabel,
  annotationSource,
}: {
  reviewPackage: ReviewPackageSummary;
  applicationId: string;
  roleLabel: "admin" | "interviewer";
  annotationSource?: Record<string, unknown> | null;
}) {
  const [openingPdf, setOpeningPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ReviewPageTab>("page1");
  const annotations = extractAnnotations(annotationSource);
  const annotationSummary = useMemo(() => summarizeAnnotations(annotations), [annotations]);
  const description =
    roleLabel === "admin"
      ? "Admin review artifact: raw PDF plus deterministic ROS Pages 1-3."
      : "Assigned review artifact: raw PDF plus deterministic ROS Pages 1-3.";

  async function handleOpenPdf() {
    setOpeningPdf(true);
    setPdfError(null);
    const popup = window.open("", "_blank");

    try {
      const blob = await fetchSourcePdf(applicationId);
      const objectUrl = window.URL.createObjectURL(blob);
      if (popup) {
        popup.location.href = objectUrl;
      } else {
        window.open(objectUrl, "_blank", "noopener,noreferrer");
      }
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    } catch (error) {
      popup?.close();
      setPdfError(error instanceof Error ? error.message : "Failed to open source PDF.");
    } finally {
      setOpeningPdf(false);
    }
  }

  return (
    <div className="space-y-5">
      <Card title="Review Package" description={description}>
        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr] xl:items-end">
          <div className="metric-strip">
            <MetricCard label="Canonical version" value={reviewPackage.canonical_version} />
            <MetricCard label="Page 2 annotations" value={String(annotationSummary.page2)} />
            <MetricCard label="Page 3 highlights" value={String(annotationSummary.page3)} />
          </div>
          <div className="space-y-3">
            <p className="rounded-[1.15rem] border border-[color:var(--line)] bg-white/72 px-4 py-3 text-sm leading-6 text-[color:var(--muted)]">
              Pages 1-3 stay deterministic. Post-generation evidence appears as a trace overlay, not a mutation of the
              canonical review record.
            </p>
            <Button className="w-full" disabled={openingPdf} onClick={() => void handleOpenPdf()} variant="secondary">
              {openingPdf ? "Opening source PDF..." : "Open source PDF"}
            </Button>
          </div>
        </div>
        {pdfError ? (
          <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{pdfError}</p>
        ) : null}
      </Card>

      <Card title="Pages 1-3 Workspace" description="Navigate the deterministic review package one page at a time.">
        <div className="space-y-5">
          <SegmentedControl
            label="Review pages"
            value={activeTab}
            onChange={setActiveTab}
            options={[
              { value: "page1", label: "Page 1", meta: "Background profile" },
              { value: "page2", label: "Page 2", meta: "Academic and engagement" },
              { value: "page3", label: "Page 3", meta: "Essays and fragments" },
            ]}
          />

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
          </div>
        </div>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-sm leading-6 text-[color:var(--ink)]">{value}</p>
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

function summarizeAnnotations(
  annotations:
    | {
        page_2_entities?: Record<string, { signal_ids?: string[]; theme_ids?: string[] }>;
        page_3_fragments?: Record<
          string,
          Array<{ fragment_id: string; start_char: number; end_char: number; signal_ids?: string[]; theme_ids?: string[] }>
        >;
      }
    | null,
) {
  if (!annotations) {
    return { page2: 0, page3: 0 };
  }

  const page2 = annotations.page_2_entities ? Object.keys(annotations.page_2_entities).length : 0;
  const page3 = annotations.page_3_fragments
    ? Object.values(annotations.page_3_fragments).reduce((sum, value) => sum + value.length, 0)
    : 0;

  return { page2, page3 };
}
