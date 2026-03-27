"use client";

import { useEffect, useState } from "react";
import { fetchAssignments } from "@/lib/api";
import type { AssignmentListItem } from "@/lib/types";
import { Card } from "@/components/ui/Card";
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

  return (
    <AdminShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Assignment Manager</h1>
          <p className="text-sm text-muted">Read-only global mapping of applications to interviewers.</p>
        </div>

        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading assignments..." />
        ) : items.length === 0 ? (
          <EmptyState title="No assignments yet." description="Assigned, draft, and published applications appear here." />
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <Card
                key={item.application_id}
                title={item.application_id}
                description={`Assigned ${new Date(item.assigned_at).toLocaleString()}`}
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-1 text-sm text-muted">
                    <p>{item.interviewer.name}</p>
                    <p>{item.interviewer.email}</p>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AdminShell>
  );
}
