"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowUpRight } from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { fetchApplicationDetail, fetchSourcePdf } from "@/lib/api";
import type { ApplicationDetailAdmin } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection, type ReviewPageTab } from "@/components/ReviewPackageSection";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { ReportChatWidget } from "@/components/ReportChatWidget";
import { navigateToReportResult } from "@/lib/reportChat";
import { FinalInterviewReportSection } from "@/components/interviewer/FinalInterviewReportSection";

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
  const [activePageTab, setActivePageTab] = useState<ReviewPageTab>("page1");

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

  useEffect(() => {
    const hasFinalReportPages = Boolean(item?.final_report?.content);
    if (!hasFinalReportPages && (activePageTab === "page4" || activePageTab === "page5")) {
      setActivePageTab("page1");
    }
  }, [activePageTab, item]);

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
  const hasFinalReportPages = Boolean(item.final_report?.content);
  const hasPostgameReport = item.interview_workspace?.status === "completed";
  const copilotActions = [
    "review Pages 1-3",
    ...(hasFinalReportPages ? ["inspect focus areas", "review interview questions"] : []),
    ...(hasPostgameReport ? ["review post-interview outcomes"] : []),
    "open source PDF",
  ];
  const pageOptions: Array<{ value: ReviewPageTab; label: string; meta: string }> = [
    { value: "page1", label: "Overview", meta: "Applicant profile" },
    { value: "page2", label: "Academics & Activities", meta: "Study and engagement" },
    { value: "page3", label: "Writing", meta: "Essays and excerpts" },
    ...(hasFinalReportPages
      ? [
          { value: "page4" as const, label: "Focus Areas", meta: "Themes and signals" },
          { value: "page5" as const, label: "Questions", meta: "Interview prompts" },
        ]
      : []),
    ...(hasPostgameReport
      ? [
          { value: "page6" as const, label: "Final Report", meta: "Post-interview outcomes" },
        ]
      : []),
  ];

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
        className={`${plexSans.variable} ${libreFranklin.variable} space-y-5 pb-28 md:pb-32`}
        style={{ fontFamily: "var(--font-reports-plex)" }}
      >
        {error ? (
          <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}
          </p>
        ) : null}

        <section className="rounded-[1.6rem] border border-slate-200 bg-white/85 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <StatusBadge status={item.status} />
              <MetaPill label="Application ID" value={item.display_id} />
              <MetaPill label="Created" value={createdAt} />
              <MetaPill label="Interviewer" value={assignee} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
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
          </div>
        </section>

        {item.review_package ? (
          <>
            <ReviewPackageSection
              reviewPackage={item.review_package}
              annotationSource={item.final_report?.content}
              activeTab={activePageTab}
              onActiveTabChange={setActivePageTab}
            />
            <ReportChatWidget
              applicationId={item.id}
              surfaceType="report_viewer"
              currentPage={activePageTab}
              workflowStage={item.interview_workspace?.status === "completed" ? "completed" : "prep"}
              availableActions={copilotActions}
              onNavigateResult={(result) => navigateToReportResult(result, setActivePageTab)}
            />
          </>
        ) : null}

        {activePageTab === "page6" && item.interview_workspace?.status === "completed" ? (
          <FinalInterviewReportSection workspace={item.interview_workspace} />
        ) : null}

        {item.review_package ? (
          <div className="pointer-events-none fixed inset-x-0 bottom-4 z-30 flex justify-center px-4 [padding-bottom:calc(env(safe-area-inset-bottom,0px))]">
            <div className="pointer-events-auto max-w-full rounded-full border border-slate-200/90 bg-white/92 p-1.5 shadow-[0_20px_48px_rgba(15,23,42,0.2)] backdrop-blur-xl">
              <SegmentedControl
                value={activePageTab}
                onChange={setActivePageTab}
                options={pageOptions}
                compact
                hideMeta
                className="space-y-0"
                listClassName="border-0 bg-transparent p-0 shadow-none"
                buttonClassName="min-h-10"
              />
            </div>
          </div>
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
