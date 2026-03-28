"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchAssignments } from "@/lib/api";
import type { AssignmentListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

export default function AdminAssignmentsPage() {
  const [items, setItems] = useState<AssignmentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadAssignments() {
    try {
      const data = await fetchAssignments();
      setItems(data);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAssignments();
  }, []);

  usePolling(loadAssignments, 5000, !loading);

  const metrics = useMemo(
    () => ({
      total: items.length,
      draft: items.filter((item) => item.status === "DRAFT").length,
      published: items.filter((item) => item.status === "PUBLISHED").length,
    }),
    [items],
  );

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(245,238,230,0.88))] p-6 shadow-[var(--card-shadow)]">
          <div className="grid gap-6 xl:grid-cols-[1.22fr_0.78fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Global mapping</p>
              <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Assignment Manager</h1>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                A compact read-only map of the application-to-interviewer graph across active and completed review states.
              </p>
            </div>
            <div className="metric-strip">
              <MetricCard label="Assignments" value={String(metrics.total)} />
              <MetricCard label="Drafts live" value={String(metrics.draft)} />
              <MetricCard label="Published" value={String(metrics.published)} />
            </div>
          </div>
        </section>

        {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading assignments..." />
        ) : items.length === 0 ? (
          <EmptyState title="No assignments yet." description="Assigned, draft, and published applications appear here." />
        ) : (
          <div className="data-table">
            <div className="data-table-header md:grid-cols-[1.2fr_0.9fr_1fr_0.9fr]">
              <span>Application</span>
              <span>Interviewer</span>
              <span>Assigned</span>
              <span>Status</span>
            </div>
            {items.map((item) => (
              <div key={item.application_id} className="data-table-row md:grid-cols-[1.2fr_0.9fr_1fr_0.9fr]">
                <div>
                  <p className="display-font text-base font-semibold text-[color:var(--ink)]">{item.application_id}</p>
                  <p className="mt-1 text-xs text-[color:var(--muted)]">{item.interviewer.email}</p>
                </div>
                <p className="text-sm text-[color:var(--ink)]">{item.interviewer.name}</p>
                <p className="text-sm text-[color:var(--muted)]">{new Date(item.assigned_at).toLocaleString()}</p>
                <StatusBadge status={item.status} />
              </div>
            ))}
          </div>
        )}
      </div>
    </AdminShell>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/82 px-4 py-4 shadow-[var(--card-shadow-soft)]">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
