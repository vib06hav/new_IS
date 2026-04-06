"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail, fetchSourcePdf, generateDraft, publishDraft } from "@/lib/api";
import type { ApplicationDetailInterviewer } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";

export default function InterviewerApplicationPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailInterviewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<"generate" | "publish" | null>(null);
  const [openingPdf, setOpeningPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadDetail() {
    try {
      const detail = await fetchApplicationDetail<ApplicationDetailInterviewer>(params.id);
      setItem(detail);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load application.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [params.id]);

  usePolling(loadDetail, 5000, !loading && !busyAction);

  async function handleGenerate() {
    setMessage(null);
    setError(null);
    setBusyAction("generate");
    try {
      await generateDraft(params.id);
      setMessage(item?.status === "DRAFT" ? "Draft regenerated." : "Draft generated.");
      await loadDetail();
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Generation failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublish() {
    setMessage(null);
    setError(null);
    setBusyAction("publish");
    try {
      await publishDraft(params.id);
      setMessage("Draft published.");
      await loadDetail();
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : "Publish failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleOpenPdf() {
    if (!item) return;
    setOpeningPdf(true);
    setError(null);
    const popup = window.open("", "_blank");

    try {
      const blob = await fetchSourcePdf(item.id);
      const objectUrl = window.URL.createObjectURL(blob);
      if (popup) {
        popup.location.href = objectUrl;
      } else {
        window.open(objectUrl, "_blank", "noopener,noreferrer");
      }
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    } catch (openError) {
      popup?.close();
      setError(openError instanceof Error ? openError.message : "Failed to open source PDF.");
    } finally {
      setOpeningPdf(false);
    }
  }

  if (loading) {
    return (
      <InterviewerShell>
        <Loader label="Loading application..." />
      </InterviewerShell>
    );
  }

  if (error && !item) {
    return (
      <InterviewerShell>
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
      </InterviewerShell>
    );
  }

  if (!item) {
    return (
      <InterviewerShell>
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">Application not found.</p>
      </InterviewerShell>
    );
  }

  const canGenerate = item.status === "ASSIGNED" || item.status === "DRAFT";
  const canPublish = item.status === "DRAFT";
  const createdAt = new Date(item.created_at).toLocaleString();

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <section className="rounded-[1.35rem] border border-white/85 bg-white/75 px-4 py-3 shadow-[0_10px_24px_rgba(148,163,184,0.1)] backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={item.status} />
              <MetaPill label="Application ID" value={item.display_id} />
              <MetaPill label="Created" value={createdAt} />
              <MetaPill label="Interviewer" value={item.assigned_interviewer?.name || "Unassigned"} />
            </div>
            <Button variant="secondary" disabled={openingPdf} onClick={() => void handleOpenPdf()}>
              {openingPdf ? "Opening PDF..." : "Open source PDF"}
            </Button>
          </div>
        </section>

        {message ? (
          <p className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">{message}</p>
        ) : null}
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
        ) : null}

        {canGenerate ? (
          <section className="rounded-[1.6rem] border border-[rgba(191,219,254,0.9)] bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(239,246,255,0.95),rgba(224,231,255,0.84))] px-5 py-5 shadow-[0_18px_36px_rgba(148,163,184,0.14),inset_0_1px_0_rgba(255,255,255,0.62)] backdrop-blur-sm">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-3xl space-y-2">
                <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-sky-700">Draft Workflow</p>
                <h2 className="text-xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">Draft actions</h2>
                <p className="text-sm leading-7 text-[color:var(--muted)]">
                  Generate updates Pages 4-5. Publish locks the draft for admin review.
                </p>
              </div>

              <div className="flex w-full flex-col gap-3 sm:w-auto sm:min-w-[23rem] sm:flex-row lg:justify-end">
                <Button className="sm:flex-1" disabled={busyAction !== null} onClick={() => void handleGenerate()}>
                  {busyAction === "generate"
                    ? item.status === "DRAFT"
                      ? "Regenerating..."
                      : "Generating..."
                    : item.status === "DRAFT"
                      ? "Regenerate draft"
                      : "Generate draft"}
                </Button>
                <Button
                  className="sm:flex-1"
                  disabled={busyAction !== null || !canPublish || !item.latest_draft}
                  variant="secondary"
                  onClick={() => void handlePublish()}
                >
                  {busyAction === "publish" ? "Publishing..." : "Publish draft"}
                </Button>
              </div>
            </div>
          </section>
        ) : null}

        {item.status === "PUBLISHED" ? (
          <Card title="Published" description="Read-only state">
            <p className="text-sm leading-7 text-[color:var(--muted)]">
              This application has already been published. The synthesized report is now fixed for downstream review.
            </p>
          </Card>
        ) : null}

        {item.review_package ? (
          <ReviewPackageSection
            reviewPackage={item.review_package}
            annotationSource={item.latest_draft?.content}
          />
        ) : null}
      </div>
    </InterviewerShell>
  );
}

function MetaPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-[color:var(--line)] bg-white/88 px-3 py-2 shadow-sm">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">{label}: </span>
      <span className="text-sm text-[color:var(--ink)]">{value}</span>
    </div>
  );
}
