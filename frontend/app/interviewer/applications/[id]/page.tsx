"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { ArrowUpRight, NotebookPen, Rocket } from "lucide-react";
import { IBM_Plex_Sans } from "next/font/google";
import { createInterviewWorkspace, fetchApplicationDetail, fetchSourcePdf } from "@/lib/api";
import type { ApplicationDetailInterviewer } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ReviewPackageSection, type ReviewPageTab } from "@/components/ReviewPackageSection";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";
import { ReportChatWidget } from "@/components/ReportChatWidget";
import { navigateToReportResult } from "@/lib/reportChat";
import { FinalInterviewReportSection } from "@/components/interviewer/FinalInterviewReportSection";
import { openInterviewPopup } from "@/lib/interviewPopup";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

export default function InterviewerApplicationPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [item, setItem] = useState<ApplicationDetailInterviewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [openingPdf, setOpeningPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [activePageTab, setActivePageTab] = useState<ReviewPageTab>("page1");
  const [workspaceBusy, setWorkspaceBusy] = useState(false);

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

  async function handleOpenConfigure() {
    if (!item) return;
    setWorkspaceBusy(true);
    setError(null);
    try {
      await createInterviewWorkspace(item.id);
      router.push(`/interviewer/applications/${item.id}/configure`);
    } catch (workspaceError) {
      setError(workspaceError instanceof Error ? workspaceError.message : "Unable to open interview plan.");
    } finally {
      setWorkspaceBusy(false);
    }
  }

  function handleOpenOverlayPopup() {
    if (!item) return;
    const popup = openInterviewPopup(item.id);
    if (!popup) {
      router.push(`/interviewer/applications/${item.id}/overlay`);
    }
  }

  useEffect(() => {
    const hasFinalReportPages = Boolean(item?.final_report?.content);
    if (!hasFinalReportPages && (activePageTab === "page4" || activePageTab === "page5")) {
      setActivePageTab("page1");
    }
    if (item?.status !== "COMPLETE" && activePageTab === "page6") {
      setActivePageTab("page1");
    }
  }, [activePageTab, item]);


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
  const workspace = item.interview_workspace;
  const isAssignedView = item.status === "ASSIGNED";
  const isCompletedView = item.status === "COMPLETE" && workspace?.status === "completed";
  const workflowStage =
    workspace?.status === "launched"
      ? "live_interview"
      : workspace?.status === "postgame"
        ? "postgame"
        : workspace?.status === "completed"
          ? "completed"
          : "prep";
  const workspaceActionLabel =
    workspace?.status === "completed"
      ? "View evaluation summary"
      : workspace?.status === "postgame"
        ? "Continue evaluation"
        : workspace?.status === "launched"
        ? "Resume interview"
        : workspace
          ? "Continue planning"
          : "Build interview plan";
  const pageOptions: Array<{ value: ReviewPageTab; label: string; meta: string; featured?: boolean }> = [
    { value: "page1", label: "Overview", meta: "Applicant profile" },
    { value: "page2", label: "Academics & Activities", meta: "Study and engagement" },
    { value: "page3", label: "Writing", meta: "Essays and excerpts" },
    ...(hasFinalReportPages
        ? [
          { value: "page4" as const, label: "Focus Areas", meta: "Interview brief" },
          { value: "page5" as const, label: "Question Sets", meta: "Interview prompts" },
        ]
      : []),
    ...(isCompletedView ? [{ value: "page6" as const, label: "Evaluation Summary", meta: "Submitted evaluation", featured: true }] : []),
  ];
  const copilotSurfaceType = activePageTab === "page6" ? "final_report" : "report_viewer";
  const copilotActions =
    activePageTab === "page6"
      ? ["review interview evaluation", "compare the interview outcome with earlier pages", "revisit Pages 1-5"]
      : [
          "review application review",
          ...(hasFinalReportPages ? ["inspect focus areas", "review question sets"] : []),
          ...(workspace?.status === "completed"
            ? ["review interview evaluation"]
            : workspace?.status === "postgame"
              ? ["continue evaluation"]
              : workspace?.status === "launched"
                ? ["resume interview"]
                : ["build interview plan"]),
        ];

  return (
    <InterviewerShell>
      <div
        className={`${plexSans.variable} space-y-2.5 ${isAssignedView || isCompletedView ? "pb-28 md:pb-32" : ""}`}
        style={{ fontFamily: "var(--font-reports-plex)" }}
      >
        <section className="rounded-[1.6rem] border border-slate-200 bg-white/80 px-4 py-3 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <StatusBadge status={item.status} />
              <InlineMeta label="Application ID" value={item.display_id} />
              <InlineMeta label="Last updated" value={lastUpdatedAt} />
              <InlineMeta label="Interviewer" value={item.assigned_interviewer?.name || "Unassigned"} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {isAssignedView && hasFinalReportPages ? (
                <InterviewerWorkflowAction
                  itemId={item.id}
                  workspace={workspace}
                  workspaceActionLabel={workspaceActionLabel}
                  workspaceBusy={workspaceBusy}
                  onConfigure={() => void handleOpenConfigure()}
                  onOpenOverlay={handleOpenOverlayPopup}
                />
              ) : null}
              <SourcePdfButton disabled={openingPdf} onClick={() => void handleOpenPdf()}>
                {openingPdf ? "Opening PDF..." : "Open source PDF"}
              </SourcePdfButton>
            </div>
          </div>
        </section>

        {message ? (
          <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p>
        ) : null}
        {error ? (
          <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
        ) : null}

        {!isAssignedView && !isCompletedView ? (
          <section className="grid items-stretch gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(21rem,0.92fr)]">
            <article className="flex min-h-[8.9rem] flex-col rounded-[1.5rem] border border-slate-200 bg-white/80 p-3.5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
              <div className="space-y-1">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Application Review</p>
                <h2 className="text-[1.05rem] font-semibold tracking-[0] text-slate-800">Page controls</h2>
                <p className="text-sm leading-5 text-slate-600">
                  Pages 4 and 5 appear once the interview brief has been generated and stay available throughout assignment.
                </p>
              </div>

              <div className="mt-2.5 flex flex-1 items-center">
                <div className="w-full rounded-[1.1rem] border border-slate-200 bg-white/70 p-1.5">
                  <SegmentedControl value={activePageTab} onChange={setActivePageTab} options={pageOptions} />
                </div>
              </div>
            </article>

            <article className="flex min-h-[8.9rem] flex-col justify-between rounded-[1.5rem] border border-slate-200 bg-white/80 p-3.5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
              <div className="space-y-1.5">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-700">Interview Workflow</p>
                <div className="space-y-1">
                  <h2 className="text-[1.05rem] font-semibold tracking-[-0.03em] text-slate-800">
                    {item.status === "COMPLETE" ? "Interview Evaluation" : "Assigned application"}
                  </h2>
                  <p className="max-w-2xl text-sm leading-5 text-slate-600">
                    {item.status === "COMPLETE"
                      ? "The interview has been completed. You can review the full Pages 1-5 package alongside the submitted interview evaluation."
                      : "This application review was generated by admin before assignment. You can review the full Pages 1-5 package and run the interview workflow from here."}
                  </p>
                </div>
              </div>

              {hasFinalReportPages ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  <InterviewerWorkflowAction
                    itemId={item.id}
                    workspace={workspace}
                    workspaceActionLabel={workspaceActionLabel}
                    workspaceBusy={workspaceBusy}
                    onConfigure={() => void handleOpenConfigure()}
                    onOpenOverlay={handleOpenOverlayPopup}
                  />
                </div>
              ) : null}
            </article>
          </section>
        ) : null}


        {item.review_package ? (
          <>
            {isCompletedView && activePageTab === "page6" ? (
              <>
                <FinalInterviewReportSection workspace={workspace} />
                <ReportChatWidget
                  applicationId={item.id}
                  surfaceType={copilotSurfaceType}
                  currentPage={activePageTab}
                  workflowStage={workflowStage}
                  availableActions={copilotActions}
                  onNavigateResult={(result) => navigateToReportResult(result, setActivePageTab)}
                />
              </>
            ) : (
              <>
                <ReviewPackageSection
                  reviewPackage={item.review_package}
                  annotationSource={item.final_report?.content}
                  activeTab={activePageTab}
                  onActiveTabChange={setActivePageTab}
                />
                <ReportChatWidget
                  applicationId={item.id}
                  surfaceType={copilotSurfaceType}
                  currentPage={activePageTab}
                  workflowStage={workflowStage}
                  availableActions={copilotActions}
                  onNavigateResult={(result) => navigateToReportResult(result, setActivePageTab)}
                />
              </>
            )}
          </>
        ) : null}

        {(isAssignedView || isCompletedView) && item.review_package ? (
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
    </InterviewerShell>
  );
}

function InterviewerWorkflowAction({
  itemId,
  workspace,
  workspaceActionLabel,
  workspaceBusy,
  onConfigure,
  onOpenOverlay,
}: {
  itemId: string;
  workspace?: ApplicationDetailInterviewer["interview_workspace"] | null;
  workspaceActionLabel: string;
  workspaceBusy: boolean;
  onConfigure: () => void;
  onOpenOverlay: () => void;
}) {
  if (workspace?.status === "completed") {
    return (
      <Link
        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition hover:bg-blue-800"
        href={`/interviewer/applications/${itemId}`}
      >
        <Rocket className="size-3.5" />
        {workspaceActionLabel}
      </Link>
    );
  }

  if (workspace?.status === "postgame") {
    return (
      <Link
        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition hover:bg-blue-800"
        href={`/interviewer/applications/${itemId}/postgame`}
      >
        <Rocket className="size-3.5" />
        {workspaceActionLabel}
      </Link>
    );
  }

  if (workspace?.status === "launched") {
    return (
      <button
        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
        onClick={onOpenOverlay}
        type="button"
      >
        <Rocket className="size-3.5" />
        {workspaceActionLabel}
      </button>
    );
  }

  return (
    <button
      className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
      disabled={workspaceBusy}
      onClick={onConfigure}
      type="button"
    >
      <NotebookPen className="size-3.5" />
      {workspaceBusy ? "Opening..." : workspaceActionLabel}
    </button>
  );
}

function InlineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-slate-200 bg-white px-3 py-2 shadow-[0_10px_24px_rgba(15,23,42,0.06)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}: </span>
      <span className="text-sm text-slate-800">{value}</span>
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
      className="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white transition-all duration-200 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-55"
      disabled={disabled}
      onClick={onClick}
      type="button"
    >
      {children}
      <ArrowUpRight className="size-3.5" />
    </button>
  );
}
