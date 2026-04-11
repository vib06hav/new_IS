"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowUpRight } from "lucide-react";
import { IBM_Plex_Sans } from "next/font/google";
import { fetchApplicationDetail, fetchSourcePdf } from "@/lib/api";
import type { ApplicationDetailInterviewer } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection, type ReviewPageTab } from "@/components/ReviewPackageSection";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

export default function InterviewerApplicationPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailInterviewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [openingPdf, setOpeningPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [activePageTab, setActivePageTab] = useState<ReviewPageTab>("page1");
  const [showStickyPageTabs, setShowStickyPageTabs] = useState(false);
  const pageControlCardRef = useRef<HTMLElement | null>(null);

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

  usePolling(loadDetail, 5000, !loading);

  async function handleOpenPdf() {
    if (!item) return;
    setOpeningPdf(true);
    setError(null);
    const popup = window.open("", "_blank");

    try {
      const blob = await fetchSourcePdf(item.id);
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

  useEffect(() => {
    const hasFinalReportPages = Boolean(item?.final_report?.content);
    if (!hasFinalReportPages && (activePageTab === "page4" || activePageTab === "page5")) {
      setActivePageTab("page1");
    }
  }, [activePageTab, item]);

  useEffect(() => {
    function updateStickyState() {
      const card = pageControlCardRef.current;
      if (!card) {
        setShowStickyPageTabs(false);
        return;
      }

      const rect = card.getBoundingClientRect();
      const stickyThreshold = 112;
      setShowStickyPageTabs(rect.bottom <= stickyThreshold);
    }

    updateStickyState();
    window.addEventListener("scroll", updateStickyState, { passive: true });
    window.addEventListener("resize", updateStickyState);

    return () => {
      window.removeEventListener("scroll", updateStickyState);
      window.removeEventListener("resize", updateStickyState);
    };
  }, []);

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

  const lastUpdatedAt = new Date(item.last_activity_at).toLocaleString();
  const hasFinalReportPages = Boolean(item.final_report?.content);
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
  ];

  return (
    <InterviewerShell>
      <div
        className={`${plexSans.variable} space-y-6`}
        style={{ fontFamily: "var(--font-reports-plex)" }}
      >
        <section className="rounded-[1.6rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_42%,#ced4df_100%)] px-4 py-4 shadow-[0_18px_50px_rgba(114,125,151,0.14)]">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <StatusBadge status={item.status} />
              <InlineMeta label="Application ID" value={item.display_id} />
              <InlineMeta label="Last updated" value={lastUpdatedAt} />
              <InlineMeta label="Interviewer" value={item.assigned_interviewer?.name || "Unassigned"} />
            </div>

            <SourcePdfButton disabled={openingPdf} onClick={() => void handleOpenPdf()}>
              {openingPdf ? "Opening PDF..." : "Open source PDF"}
            </SourcePdfButton>
          </div>
        </section>

        {message ? (
          <p className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-700">{message}</p>
        ) : null}
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
        ) : null}

        <section className="grid items-stretch gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(21rem,0.92fr)]">
          <article className="flex min-h-[8.9rem] flex-col justify-between rounded-[1.5rem] border border-[#727D97] bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(239,246,255,0.95),rgba(224,231,255,0.84))] p-3.5 shadow-[0_18px_36px_rgba(148,163,184,0.14),inset_0_1px_0_rgba(255,255,255,0.62)]">
            <div className="space-y-1.5">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#198FF0]">Report workflow</p>
              <div className="space-y-1">
                <h2 className="text-[1.05rem] font-semibold tracking-[-0.03em] text-[#111111]">Completed report</h2>
                <p className="max-w-2xl text-sm leading-5 text-[#49536B]">
                  This report was completed by an admin before assignment. You can review the full Pages 1-5 package
                  without any generation or publishing steps.
                </p>
              </div>
            </div>
          </article>

          <div>
            <article
              ref={pageControlCardRef}
              className="flex min-h-[8.9rem] flex-col rounded-[1.5rem] border border-[#727D97] bg-[#E6E9F0] p-3.5 shadow-[0_18px_36px_rgba(114,125,151,0.14)]"
            >
              <div className="space-y-1">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Report pages</p>
                <h2 className="text-[1.05rem] font-semibold tracking-[-0.03em] text-[#111111]">Page controls</h2>
                <p className="text-sm leading-5 text-[#49536B]">
                  Pages 4 and 5 appear once the final report has been generated and stay available throughout assignment.
                </p>
              </div>

              <div className="mt-2.5 flex flex-1 items-center">
                <div className="w-full rounded-[1.1rem] border border-[#727D97] bg-[#F7F7F1] p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
                  <SegmentedControl value={activePageTab} onChange={setActivePageTab} options={pageOptions} />
                </div>
              </div>
            </article>
          </div>
        </section>

        <div className="pointer-events-none hidden h-0 xl:block">
          <div className="sticky top-[calc(var(--portal-header-height)+1rem)] z-20 flex justify-end">
            <div
              className={`pointer-events-auto w-[min(100%,31rem)] rounded-[1.2rem] border border-[#727D97] bg-[#F7F7F1]/96 p-1.5 shadow-[0_18px_36px_rgba(114,125,151,0.18)] backdrop-blur transition-all duration-300 ${
                showStickyPageTabs
                  ? "pointer-events-auto translate-y-0 opacity-100"
                  : "pointer-events-none -translate-y-3 opacity-0"
              }`}
            >
              <SegmentedControl value={activePageTab} onChange={setActivePageTab} options={pageOptions} />
            </div>
          </div>
        </div>

        {item.review_package ? (
          <ReviewPackageSection
            reviewPackage={item.review_package}
            annotationSource={item.final_report?.content}
            activeTab={activePageTab}
            onActiveTabChange={setActivePageTab}
          />
        ) : null}
      </div>
    </InterviewerShell>
  );
}

function InlineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-[#727D97] bg-[#F7F7F1] px-3 py-2 shadow-[0_10px_24px_rgba(114,125,151,0.1)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#5F6C86]">{label}: </span>
      <span className="text-sm text-[#111111]">{value}</span>
    </div>
  );
}

function SourcePdfButton({
  children,
  disabled,
  onClick,
}: {
  children: React.ReactNode;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      className="inline-flex items-center gap-1 rounded-full bg-[#111111] px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-[#f7f8ec] transition-all duration-200 hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-55"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {children}
      <ArrowUpRight className="size-3.5" />
    </button>
  );
}
