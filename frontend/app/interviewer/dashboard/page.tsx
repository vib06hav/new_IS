"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { fetchMyApplications } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";

export default function InterviewerDashboardPage() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadApplications() {
    try {
      const data = await fetchMyApplications();
      setItems(data);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadApplications();
  }, []);

  usePolling(loadApplications, 5000, !loading);

  const metrics = useMemo(
    () => ({
      total: items.length,
      drafts: items.filter((item) => item.status === "DRAFT").length,
      published: items.filter((item) => item.status === "PUBLISHED").length,
    }),
    [items],
  );

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <section className="hero-panel p-6">
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr] xl:items-start">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Reviewer queue</p>
              <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Dashboard</h1>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                Your assigned applications live in one dense workboard. Open a row when you need the full workspace;
                otherwise stay in flow and monitor status changes here.
              </p>
            </div>
            <div className="metric-strip md:grid-cols-3 xl:self-start">
              <MetricCard label="Assigned" value={String(metrics.total)} />
              <MetricCard label="Drafting" value={String(metrics.drafts)} />
              <MetricCard label="Published" value={String(metrics.published)} />
            </div>
          </div>
        </section>

        {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading dashboard..." />
        ) : items.length === 0 ? (
          <EmptyState title="No applications assigned yet." description="Assigned, draft, and published work appears here." />
        ) : (
          <div className="data-table">
            <div className="data-table-header md:grid-cols-[1.2fr_0.8fr_0.9fr_0.7fr]">
              <span>Application</span>
              <span>Status</span>
              <span>Created</span>
              <span>Open</span>
            </div>
            {items.map((item) => (
              <div key={item.id} className="data-table-row md:grid-cols-[1.2fr_0.8fr_0.9fr_0.7fr]">
                <div>
                  <p className="display-font text-base font-semibold text-[color:var(--ink)]">{item.id}</p>
                  <p className="mt-1 text-xs text-[color:var(--muted)]">
                    {item.assigned_interviewer ? `Assigned to ${item.assigned_interviewer.name}` : "Awaiting reviewer"}
                  </p>
                </div>
                <StatusBadge status={item.status} />
                <p className="text-sm text-[color:var(--muted)]">{new Date(item.created_at).toLocaleString()}</p>
                <Link
                  className="display-font text-sm font-semibold text-[color:var(--accent)] underline underline-offset-4"
                  href={`/interviewer/applications/${item.id}`}
                >
                  Open
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </InterviewerShell>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
