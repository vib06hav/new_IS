"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail, fetchSourcePdf } from "@/lib/api";
import type { ApplicationDetailAdmin } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

export default function AdminApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailAdmin | null>(null);
  const [loading, setLoading] = useState(true);
  const [openingPdf, setOpeningPdf] = useState(false);
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

  async function handleOpenPdf() {
    const applicationId = item?.id;
    if (!applicationId) return;
    setOpeningPdf(true);
    setError(null);
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
    } catch (openError) {
      popup?.close();
      setError(openError instanceof Error ? openError.message : "Failed to open source PDF.");
    } finally {
      setOpeningPdf(false);
    }
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="rounded-[1.35rem] border border-white/85 bg-white/75 px-4 py-3 shadow-[0_10px_24px_rgba(148,163,184,0.1)] backdrop-blur">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={item.status} />
              <MetaPill label="Application ID" value={item.id} />
              <MetaPill label="Created" value={createdAt} />
              <MetaPill label="Interviewer" value={assignee} />
            </div>
            <Button variant="secondary" disabled={openingPdf} onClick={() => void handleOpenPdf()}>
              {openingPdf ? "Opening PDF..." : "Open source PDF"}
            </Button>
          </div>
        </section>

        {item.status === "DRAFT" ? (
          <Card title="Draft Status" description="Admin visibility before publish">
            <p className="text-sm leading-7 text-[color:var(--muted)]">
              An interviewer draft exists, but the written assessment remains private until publish. You can continue
              reviewing the application summary and source material in the meantime.
            </p>
          </Card>
        ) : null}

        {item.review_package ? (
          <ReviewPackageSection
            reviewPackage={item.review_package}
            annotationSource={item.published_draft?.content}
          />
        ) : null}
      </div>
    </AdminShell>
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
