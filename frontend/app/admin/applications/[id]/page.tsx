"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowUpRight } from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { fetchApplicationDetail, fetchSourcePdf } from "@/lib/api";
import type { ApplicationDetailAdmin } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

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
      <div
        className={`${plexSans.variable} ${libreFranklin.variable} space-y-6`}
        style={{ fontFamily: "var(--font-reports-plex)" }}
      >
        {error ? (
          <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}
          </p>
        ) : null}

        <section className="rounded-[1.8rem] border border-slate-200 bg-white/80 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <StatusBadge status={item.status} />
              <MetaPill label="Application ID" value={item.display_id} />
              <MetaPill label="Created" value={createdAt} />
              <MetaPill label="Interviewer" value={assignee} />
            </div>

            <button
              className="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition-all duration-200 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-55"
              disabled={openingPdf}
              onClick={() => void handleOpenPdf()}
              type="button"
            >
              {openingPdf ? "Opening PDF..." : "Open source PDF"}
              <ArrowUpRight className="size-3.5" />
            </button>
          </div>
        </section>

        {item.status === "READY" ? (
          <Card title="Report Generation" description="Admin-controlled completion step" eyebrow={null}>
            <p className="text-sm leading-7 text-[color:var(--muted)]">
              Pages 1-3 are ready. Generate the final report from the reports dashboard to unlock assignment and full
              review visibility.
            </p>
          </Card>
        ) : null}

        {item.review_package ? (
          <ReviewPackageSection
            reviewPackage={item.review_package}
            annotationSource={item.final_report?.content}
          />
        ) : null}
      </div>
    </AdminShell>
  );
}

function MetaPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-slate-200 bg-white px-3 py-2 shadow-[0_10px_24px_rgba(15,23,42,0.06)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}: </span>
      <span className="text-sm text-slate-800">{value}</span>
    </div>
  );
}
