"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail, generateDraft, publishDraft } from "@/lib/api";
import type { ApplicationDetailInterviewer } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { SynthesisReportSection } from "@/components/SynthesisReportSection";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";

export default function InterviewerApplicationPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailInterviewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<"generate" | "publish" | null>(null);
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
  const latestVersion = item.latest_draft?.version;

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <section className="hero-panel overflow-hidden p-6">
          <div className="grid gap-6 xl:grid-cols-[1.16fr_0.84fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Interviewer Workspace
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)] md:text-4xl">
                  {item.id}
                </h1>
                <StatusBadge status={item.status} />
              </div>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                Read the deterministic package, generate Pages 4–5 from canonical state, and inspect the resulting
                annotation overlay before deciding whether the draft is ready to publish.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <MetricCard label="Created" value={createdAt} />
              <MetricCard label="Assigned reviewer" value={item.assigned_interviewer?.name || "Unassigned"} />
              <MetricCard label="Latest draft" value={latestVersion ? `v${latestVersion}` : "Not generated"} />
            </div>
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
                applicationId={item.id}
                reviewPackage={item.review_package}
                roleLabel="interviewer"
                annotationSource={item.latest_draft?.content}
              />
            ) : null}
          </div>

          <aside className="space-y-6">
            {item.latest_draft ? (
              <SynthesisReportSection
                title={`Latest Draft · v${item.latest_draft.version}`}
                description="Pages 4–5 synthesized from canonical state."
                draft={item.latest_draft.content}
              />
            ) : (
              <Card title="Latest Draft" description="No draft yet">
                <p className="text-sm leading-7 text-[color:var(--muted)]">
                  Generate a draft to populate synthesized focus areas, signal framing, and interview question groups.
                </p>
              </Card>
            )}

            {canGenerate ? (
              <Card title="Draft Actions" description="Generation affects Pages 4–5 only">
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
                    Publishing freezes Pages 4–5 for admin visibility while leaving canonical Pages 1–3 unchanged.
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

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-sm leading-6 text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
