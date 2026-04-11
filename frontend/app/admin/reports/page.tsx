"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { Stars } from "lucide-react";
import {
  Cormorant_Garamond,
  IBM_Plex_Sans,
} from "next/font/google";
import {
  assignApplication,
  deleteApplication,
  fetchApplications,
  fetchInterviewers,
  generateReport,
  hideApplication,
  reassignApplication,
  unhideApplication,
  updateApplicationDisplayId,
} from "@/lib/api";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { usePolling } from "@/lib/usePolling";
import {
  useAdminSessionHistory,
} from "@/components/layout/AdminSessionHistory";
import { AdminSessionLogPanel } from "@/components/layout/AdminSessionLogPanel";
import { AdminShell } from "@/components/layout/AdminShell";
import { AdminReportCard } from "@/components/admin/AdminReportCard";

const REPORT_STATUSES = ["ALL", "READY", "COMPLETE", "ASSIGNED", "HIDDEN"] as const;

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-reports-cormorant",
});

export default function AdminReportsPage() {
  return (
    <AdminShell>
      <AdminReportsContent />
    </AdminShell>
  );
}

function AdminReportsContent() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<(typeof REPORT_STATUSES)[number]>("ALL");
  const [loading, setLoading] = useState(true);
  const [busyAppId, setBusyAppId] = useState<string | null>(null);
  const [generatingAppId, setGeneratingAppId] = useState<string | null>(null);
  const [hiddenBusyAppId, setHiddenBusyAppId] = useState<string | null>(null);
  const [deletingAppId, setDeletingAppId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedInterviewerByApp, setSelectedInterviewerByApp] = useState<Record<string, string>>({});
  const [editingDisplayIdAppId, setEditingDisplayIdAppId] = useState<string | null>(null);
  const [pendingDisplayIdByApp, setPendingDisplayIdByApp] = useState<Record<string, string>>({});
  const [savingDisplayIdAppId, setSavingDisplayIdAppId] = useState<string | null>(null);
  const { entries: sessionHistoryEntries, addEntry } = useAdminSessionHistory();

  async function loadData() {
    try {
      const [visibleApplications, hiddenApplications, interviewerList] = await Promise.all([
        fetchApplications(),
        fetchApplications("HIDDEN"),
        fetchInterviewers(),
      ]);

      const applications = [...visibleApplications, ...hiddenApplications]
        .filter((item) => item.status !== "UPLOADED" && item.status !== "PROCESSING" && item.status !== "FAILED")
        .sort((left, right) => new Date(right.last_activity_at).getTime() - new Date(left.last_activity_at).getTime());

      setItems(
        applications,
      );
      setInterviewers(interviewerList);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void loadData();
  }, []);

  usePolling(loadData, 5000, !loading);

  async function mutateAssignment(applicationId: string, mode: "assign" | "reassign") {
    const interviewerId = selectedInterviewerByApp[applicationId];
    if (!interviewerId) {
      setError("Choose an interviewer first.");
      return;
    }

    setBusyAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      const report = items.find((item) => item.id === applicationId);
      const nextInterviewer = interviewers.find((interviewer) => interviewer.id === interviewerId);

      if (mode === "assign") {
        await assignApplication(applicationId, interviewerId);
        setMessage("Application assigned.");
      } else {
        await reassignApplication(applicationId, interviewerId);
        setMessage("Application reassigned.");
      }

      if (report && nextInterviewer) {
        addEntry({
          action: mode === "assign" ? "Assigned" : "Reassigned",
          reportId: report.display_id,
          detail:
            mode === "assign"
              ? `${nextInterviewer.name} added as first interviewer`
              : report.assigned_interviewer
                ? `${report.assigned_interviewer.name} -> ${nextInterviewer.name}`
                : `${nextInterviewer.name} selected as interviewer`,
          tone: mode === "assign" ? "lime" : "blue",
        });
      }

      await loadData();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Assignment update failed.");
    } finally {
      setBusyAppId(null);
    }
  }

  async function handleGenerate(applicationId: string) {
    setGeneratingAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      const report = items.find((item) => item.id === applicationId);
      await generateReport(applicationId);
      setMessage("Final report generated.");

      if (report) {
        addEntry({
          action: "Generated",
          reportId: report.display_id,
          detail: "Pages 4-5 and annotations were created for assignment-ready review.",
          tone: "lime",
        });
      }

      await loadData();
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Final report generation failed.");
    } finally {
      setGeneratingAppId(null);
    }
  }

  async function toggleHidden(applicationId: string, nextHidden: boolean) {
    setHiddenBusyAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      const report = items.find((item) => item.id === applicationId);

      if (nextHidden) {
        await hideApplication(applicationId);
        setMessage("Report hidden.");
      } else {
        await unhideApplication(applicationId);
        setMessage("Report restored.");
      }

      if (report) {
        addEntry({
          action: nextHidden ? "Hidden" : "Unhidden",
          reportId: report.display_id,
          detail: nextHidden
            ? "Removed from visible list for this session"
            : "Restored to the visible report list",
          tone: nextHidden ? "orange" : "pink",
        });
      }

      await loadData();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Failed to update report visibility.");
    } finally {
      setHiddenBusyAppId(null);
    }
  }

  async function removeReport(applicationId: string) {
    const report = items.find((item) => item.id === applicationId);
    if (!report) {
      return;
    }

    if (!window.confirm(`Delete report ${report.display_id}? This cannot be undone.`)) {
      return;
    }

    setDeletingAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      await deleteApplication(applicationId);
      addEntry({
        action: "Deleted",
        reportId: report.display_id,
        detail: "Removed report from the current review set",
        tone: "slate",
      });
      setMessage("Report deleted.");
      await loadData();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete report.");
    } finally {
      setDeletingAppId(null);
    }
  }

  function startEditingDisplayId(item: ApplicationListItem) {
    setEditingDisplayIdAppId(item.id);
    setPendingDisplayIdByApp((current) => ({ ...current, [item.id]: item.display_id }));
    setMessage(null);
    setError(null);
  }

  function cancelEditingDisplayId(applicationId: string) {
    setEditingDisplayIdAppId((current) => (current === applicationId ? null : current));
    setPendingDisplayIdByApp((current) => {
      const next = { ...current };
      delete next[applicationId];
      return next;
    });
  }

  async function saveDisplayId(applicationId: string) {
    const displayId = pendingDisplayIdByApp[applicationId];
    if (!displayId) {
      setError("Display ID cannot be empty.");
      return;
    }

    setSavingDisplayIdAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      const report = items.find((item) => item.id === applicationId);
      await updateApplicationDisplayId(applicationId, { display_id: displayId });
      setEditingDisplayIdAppId(null);
      setMessage("Application ID updated.");

      if (report) {
        addEntry({
          action: "Updated ID",
          reportId: report.display_id,
          detail: `Updated reporting identifier to ${displayId}`,
          tone: "cyan",
        });
      }

      await loadData();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update application ID.");
    } finally {
      setSavingDisplayIdAppId(null);
    }
  }

  const metrics = useMemo(
    () => ({
      ready: items.filter((item) => item.status === "READY").length,
      complete: items.filter((item) => item.status === "COMPLETE").length,
      assigned: items.filter((item) => item.status === "ASSIGNED").length,
      hidden: items.filter((item) => item.is_hidden).length,
    }),
    [items],
  );

  const filteredItems = useMemo(() => {
    if (statusFilter === "ALL") {
      return items.filter((item) => !item.is_hidden);
    }

    if (statusFilter === "HIDDEN") {
      return items.filter((item) => item.is_hidden);
    }

    return items.filter((item) => !item.is_hidden && item.status === statusFilter);
  }, [items, statusFilter]);

  return (
    <div
      className={`${plexSans.variable} ${cormorant.variable} space-y-6`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_22rem]">
        <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
              <div className="space-y-4 xl:flex xl:h-full xl:flex-col xl:gap-4 xl:space-y-0">
                <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6 xl:flex-1">
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                    <span className="inline-flex items-center gap-2 text-[#111111]">
                      <Stars className="size-3.5" />
                      Admin review desk
                    </span>
                  </div>
                  <div className="mt-5 space-y-4">
                    <h3
                      className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.85rem]"
                      style={{ fontFamily: "var(--font-reports-cormorant)" }}
                    >
                      Generated Reports
                    </h3>
                    <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                      Open generated reports, update report IDs, assign or reassign interviewers, manage visibility, and
                      remove reports when necessary.
                    </p>
                  </div>
                </div>

                <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-4">
                  <div className="rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {REPORT_STATUSES.map((status) => (
                        <button
                          key={status}
                          className={`rounded-[1rem] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-200 ${
                            statusFilter === status
                              ? getFilterActiveClasses(status)
                              : "border border-transparent bg-transparent text-[#49536B] hover:border-[#727D97] hover:bg-[#F7F7F1] hover:text-[#111111]"
                          }`}
                          onClick={() => setStatusFilter(status)}
                          type="button"
                        >
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 xl:flex xl:h-full xl:flex-col">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Status totals</p>
                <div className="mt-4 flex flex-1 flex-col gap-3">
                  <StatusTotal className="flex-1" label="Ready" value={metrics.ready} />
                  <StatusTotal className="flex-1" label="Complete" value={metrics.complete} />
                  <StatusTotal className="flex-1" label="Assigned" value={metrics.assigned} />
                  <StatusTotal className="flex-1" label="Hidden" value={metrics.hidden} />
                </div>
              </div>
            </section>

            {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading reports..." />
        ) : filteredItems.length === 0 ? (
          <ReportsEmptyState statusFilter={statusFilter} />
        ) : (
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredItems.map((item) => (
              <AdminReportCard
                key={item.id}
                item={item}
                interviewers={interviewers}
                selectedInterviewerId={selectedInterviewerByApp[item.id] ?? ""}
                onSelectedInterviewerChange={(value) =>
                  setSelectedInterviewerByApp((current) => ({ ...current, [item.id]: value }))
                }
                onGenerate={() => void handleGenerate(item.id)}
                onAssign={(mode) => void mutateAssignment(item.id, mode)}
                onToggleHidden={() => void toggleHidden(item.id, !item.is_hidden)}
                onDelete={() => void removeReport(item.id)}
                onStartEdit={() => startEditingDisplayId(item)}
                onCancelEdit={() => cancelEditingDisplayId(item.id)}
                onSaveEdit={() => void saveDisplayId(item.id)}
                onPendingDisplayIdChange={(value) =>
                  setPendingDisplayIdByApp((current) => ({ ...current, [item.id]: value }))
                }
                pendingDisplayId={pendingDisplayIdByApp[item.id] ?? ""}
                isGenerating={generatingAppId === item.id}
                isBusy={busyAppId === item.id}
                isHiddenBusy={hiddenBusyAppId === item.id}
                isDeleting={deletingAppId === item.id}
                isEditingDisplayId={editingDisplayIdAppId === item.id}
                isSavingDisplayId={savingDisplayIdAppId === item.id}
              />
            ))}
          </section>
        )}
          </div>

        <aside className="grid gap-5 self-start">
          <AdminSessionLogPanel entries={sessionHistoryEntries} />
        </aside>
      </div>
    </div>
  );
}

function getFilterActiveClasses(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") return "bg-[#198FF0] text-[#111111] shadow-[0_8px_20px_rgba(25,143,240,0.28)]";
  if (status === "READY") return "bg-[#d7ff53] text-[#111111] shadow-[0_8px_20px_rgba(215,255,83,0.28)]";
  if (status === "COMPLETE") return "bg-[#9af5b4] text-[#111111] shadow-[0_8px_20px_rgba(154,245,180,0.24)]";
  if (status === "ASSIGNED") return "bg-[#7cf0ff] text-[#111111] shadow-[0_8px_20px_rgba(124,240,255,0.22)]";
  return "bg-[#8A94A6] text-[#111111] shadow-[0_8px_20px_rgba(138,148,166,0.24)]";
}

function getEmptyStateBorderClasses(status: (typeof REPORT_STATUSES)[number]) {
  return "border-[#727D97] shadow-[0_18px_44px_rgba(114,125,151,0.14)]";
}

function getEmptyStateCopy(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") {
    return {
      title: "No visible reports right now.",
      description: "Generated reports will appear here once they move into review-ready states.",
    };
  }

  if (status === "READY") {
    return {
      title: "No ready reports yet.",
      description: "Reports waiting for Pages 4-5 generation will appear here.",
    };
  }

  if (status === "COMPLETE") {
    return {
      title: "No complete reports yet.",
      description: "Reports ready for assignment will appear here.",
    };
  }

  if (status === "ASSIGNED") {
    return {
      title: "No assigned reports yet.",
      description: "Reports currently owned by an interviewer will appear here.",
    };
  }

  return {
    title: "No hidden reports yet.",
    description: "Reports you hide from the main view will appear here.",
  };
}

function ReportsEmptyState({ statusFilter }: { statusFilter: (typeof REPORT_STATUSES)[number] }) {
  const copy = getEmptyStateCopy(statusFilter);

  return (
    <div
      className={`rounded-[1.9rem] border bg-[#F7F7F1] px-6 py-10 text-center ${getEmptyStateBorderClasses(statusFilter)}`}
    >
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="grid size-16 place-items-center overflow-hidden rounded-2xl border border-[#198FF0]/25 bg-[#EAF4FD] shadow-[0_0_40px_rgba(25,143,240,0.2)]">
          <Image
            alt="Interview Standardiser logo"
            className="h-14 w-14 scale-[1.28] object-cover"
            height={56}
            src="/Logo-removebg-preview.png"
            width={56}
          />
        </div>
        <h4
          className="mt-5 text-[2.1rem] leading-[0.95] tracking-[-0.05em] text-[#111111]"
          style={{ fontFamily: "var(--font-reports-cormorant)" }}
        >
          {copy.title}
        </h4>
        <p className="mt-3 text-sm leading-7 text-[#49536B]">{copy.description}</p>
      </div>
    </div>
  );
}

function StatusTotal({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={`${className ?? ""} flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-[#E6E9F0] px-3 py-3`}>
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
    </div>
  );
}
