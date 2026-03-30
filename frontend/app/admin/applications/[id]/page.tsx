"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail } from "@/lib/api";
import type { ApplicationDetailAdmin } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { SynthesisReportSection } from "@/components/SynthesisReportSection";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

export default function AdminApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailAdmin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadDetail() {
    try {
      const detail = await fetchApplicationDetail<ApplicationDetailAdmin>(params.id);
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

  usePolling(loadDetail, 5000, !loading);

  if (loading) {
    return (
      <AdminShell>
        <Loader label="Loading application..." />
      </AdminShell>
    );
  }

  if (error || !item) {
    return (
      <AdminShell>
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error || "Application not found."}
        </p>
      </AdminShell>
    );
  }

  const createdAt = new Date(item.created_at).toLocaleString();
  const assignee = item.assigned_interviewer?.name || "Not assigned";
  const publishedVersion = item.published_draft?.version;

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="hero-panel overflow-hidden p-6">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">
                Admin Application Review
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)] md:text-4xl">
                  {item.id}
                </h1>
                <StatusBadge status={item.status} />
              </div>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                Deterministic Pages 1–3 remain the canonical review package. Published Pages 4–5 appear alongside
                annotation overlays so admin can inspect what was finalized without stepping into draft ownership.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
              <MetricCard label="Created" value={createdAt} />
              <MetricCard label="Assignee" value={assignee} />
              <MetricCard label="Published draft" value={publishedVersion ? `v${publishedVersion}` : "None yet"} />
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(22rem,0.9fr)]">
          <div className="space-y-6">
            {item.review_package ? (
              <ReviewPackageSection
                applicationId={item.id}
                reviewPackage={item.review_package}
                roleLabel="admin"
                annotationSource={item.published_draft?.content}
              />
            ) : null}
          </div>

          <aside className="space-y-6">
            {item.status === "DRAFT" ? (
              <Card title="Draft Status" description="Admin visibility before publish">
                <p className="text-sm leading-7 text-[color:var(--muted)]">
                  An interviewer draft exists, but Pages 4–5 remain private until publish. Admin can continue reviewing
                  the canonical package and source material in the meantime.
                </p>
              </Card>
            ) : null}

            {item.published_draft ? (
              <SynthesisReportSection
                title={`Published Report · v${item.published_draft.version}`}
                description="Pages 4–5 frozen at publish time."
                draft={item.published_draft.content}
              />
            ) : (
              <Card title="Published Report" description="No published synthesis yet">
                <p className="text-sm leading-7 text-[color:var(--muted)]">
                  Once the assigned interviewer publishes, the final focus areas and question groups will appear here.
                </p>
              </Card>
            )}
          </aside>
        </div>
      </div>
    </AdminShell>
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
