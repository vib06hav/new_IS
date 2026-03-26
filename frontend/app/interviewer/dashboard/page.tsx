"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchMyApplications } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ApplicationListItem } from "@/lib/types";
import { Card } from "@/components/ui/Card";
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
    const token = getToken();
    if (!token) {
      return;
    }
    try {
      const data = await fetchMyApplications(token);
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

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Dashboard</h1>
          <p className="text-sm text-muted">Assigned applications ready for generation or review.</p>
        </div>

        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading dashboard..." />
        ) : items.length === 0 ? (
          <EmptyState title="No applications assigned yet." description="Assigned, draft, and published work appears here." />
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <Card key={item.id} title={item.id} description={new Date(item.created_at).toLocaleString()}>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <StatusBadge status={item.status} />
                  <Link className="text-sm text-accent underline" href={`/interviewer/applications/${item.id}`}>
                    Open application
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </InterviewerShell>
  );
}
