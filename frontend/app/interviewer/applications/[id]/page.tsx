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
              <MetaPill label="Application ID" value={item.id} />
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

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.28fr)_minmax(22rem,0.92fr)]">
          <div className="space-y-6">
            {item.review_package ? (
              <ReviewPackageSection
                reviewPackage={item.review_package}
                annotationSource={item.latest_draft?.content}
              />
            ) : null}
          </div>

          <aside className="space-y-6">
            {canGenerate ? (
              <Card title="Draft Actions" description="Generation affects Pages 4-5 only">
                <div className="space-y-3">
                  <Button className="w-full" disabled={busyAction !== null} onClick={() => void handleGenerate()}>
                    {busyAction === "generate"
                      ? item.status === "DRAFT"
                        ? "Regenerating..."
                        : "Generating..."
                      : item.status === "DRAFT"
                        ? "Regenerate draft"
                        : "Generate draft"}
                  </Button>
                  <Button
                    className="w-full"
                    disabled={busyAction !== null || !canPublish || !item.latest_draft}
                    variant="secondary"
                    onClick={() => void handlePublish()}
                  >
                    {busyAction === "publish" ? "Publishing..." : "Publish draft"}
                  </Button>
                  <p className="text-xs leading-6 text-[color:var(--muted)]">
                    Publishing freezes the written assessment for admin visibility while leaving the application summary unchanged.
                  </p>
                </div>
              </Card>
            ) : null}

            {item.status === "PUBLISHED" ? (
              <Card title="Published" description="Read-only state">
                <p className="text-sm leading-7 text-[color:var(--muted)]">
                  This application has already been published. The synthesized report is now fixed for downstream review.
                </p>
              </Card>
            ) : null}
          </aside>
        </div>
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
