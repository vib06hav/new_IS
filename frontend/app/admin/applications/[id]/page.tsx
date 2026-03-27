"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail } from "@/lib/api";
import type { ApplicationDetailAdmin } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { JsonSection } from "@/components/JsonSection";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
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
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error || "Application not found."}
        </p>
      </AdminShell>
    );
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        <Card title={item.id} description={new Date(item.created_at).toLocaleString()}>
          <div className="space-y-2 text-sm text-muted">
            <StatusBadge status={item.status} />
            <p>{item.assigned_interviewer ? `Assigned to ${item.assigned_interviewer.name}` : "Not assigned"}</p>
          </div>
        </Card>

        {item.review_package ? (
          <ReviewPackageSection
            applicationId={item.id}
            reviewPackage={item.review_package}
            roleLabel="admin"
            annotationSource={item.published_draft?.content}
          />
        ) : null}

        {item.status === "DRAFT" ? (
          <Card title="Draft Status" description="Admin cannot view draft pages before publish.">
            <p className="text-sm text-muted">
              Draft in progress. The interviewer workspace owns Pages 4-5 until publish.
            </p>
          </Card>
        ) : null}

        {item.published_draft ? (
          <JsonSection
            title="Published Draft"
            description={`Version ${item.published_draft.version}`}
            data={item.published_draft.content}
          />
        ) : null}
      </div>
    </AdminShell>
  );
}
