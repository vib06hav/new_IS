"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { JsonSection } from "@/components/JsonSection";
import { ReviewPageThreeSection, ReviewPageTwoSection } from "@/components/ReviewPackagePages";
import { fetchSourcePdf } from "@/lib/api";
import type { ReviewPackageSummary } from "@/lib/types";
import { Button } from "@/components/ui/Button";

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
  const annotations = extractAnnotations(annotationSource);
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
    <div className="space-y-6">
      <Card title="Review Package" description={description}>
        <div className="flex flex-col gap-3 text-sm text-muted md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <p>Canonical version {reviewPackage.canonical_version}</p>
            <p>Pages 1-3 are rendered from the persisted deterministic review package.</p>
          </div>
          <Button disabled={openingPdf} onClick={() => void handleOpenPdf()} variant="secondary">
            {openingPdf ? "Opening source PDF..." : "Open source PDF"}
          </Button>
        </div>
        {pdfError ? <p className="mt-3 text-sm text-red-700">{pdfError}</p> : null}
      </Card>

      <JsonSection
        title="ROS Page 1"
        description="Background profile"
        data={reviewPackage.pages_1_3.page_1_background_profile}
      />
      <ReviewPageTwoSection
        data={reviewPackage.pages_1_3.page_2_academic_and_engagement}
        annotations={annotations}
      />
      <ReviewPageThreeSection
        data={reviewPackage.pages_1_3.page_3_essays}
        annotations={annotations}
      />
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
