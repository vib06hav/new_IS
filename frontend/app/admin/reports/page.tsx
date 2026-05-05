"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, FileChartColumn, LayoutPanelLeft, ListTodo, Search, Settings2, Stars } from "lucide-react";
import {
  Libre_Franklin,
  IBM_Plex_Sans,
} from "next/font/google";
import {
  assignApplication,
  deleteApplication,
  fetchApplications,
  fetchInterviewers,
  fetchLlmCapacity,
  generateReport,
  hideApplication,
  reassignApplication,
  unhideApplication,
  updateApplicationDisplayId,
} from "@/lib/api";
import type { ApplicationListItem, InterviewerListItem, LLMCapacityStatusResponse } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { AdminReportCard } from "@/components/admin/AdminReportCard";

const REPORT_STATUSES = ["ALL", "PROCESSED", "READY", "ASSIGNED", "COMPLETE", "HIDDEN"] as const;

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-reports-display",
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
  const [llmCapacity, setLlmCapacity] = useState<LLMCapacityStatusResponse | null>(null);
  const [selectedInterviewerByApp, setSelectedInterviewerByApp] = useState<Record<string, string>>({});
  const [editingDisplayIdAppId, setEditingDisplayIdAppId] = useState<string | null>(null);
  const [pendingDisplayIdByApp, setPendingDisplayIdByApp] = useState<Record<string, string>>({});
  const [savingDisplayIdAppId, setSavingDisplayIdAppId] = useState<string | null>(null);

  async function loadData() {
    try {
      const [visibleApplications, hiddenApplications, interviewerList, capacity] = await Promise.all([
        fetchApplications(),
        fetchApplications("HIDDEN"),
        fetchInterviewers(),
        fetchLlmCapacity(),
      ]);

      const applications = [...visibleApplications, ...hiddenApplications]
        .filter((item) => item.status !== "UPLOADED" && item.status !== "PROCESSING" && item.status !== "FAILED")
        .sort((left, right) => new Date(right.last_activity_at).getTime() - new Date(left.last_activity_at).getTime());

      setItems(
        applications,
      );
      setInterviewers(interviewerList);
      setLlmCapacity(capacity);
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
      processed: items.filter((item) => item.status === "PROCESSED").length,
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
      className={`${plexSans.variable} ${libreFranklin.variable} space-y-5`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="space-y-5">
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_20rem] gap-6 items-stretch">
          <div className="space-y-6">
            <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="relative">
                <div className="space-y-3">
                  <h1
                    className="max-w-4xl text-3xl md:text-4xl font-black tracking-tight text-slate-800 leading-none"
                    style={{ fontFamily: "var(--font-reports-display)" }}
                  >
                    Reports Dashboard
                  </h1>
                  <p className="max-w-3xl text-sm text-slate-600 leading-relaxed">
                    Monitor the status of interview reports, manage assignments, and track generation capacity across the pipeline.
                  </p>
                </div>
              </div>
            </section>

            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
              <div className="flex-1 rounded-xl border border-slate-100 bg-slate-50 p-1.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  {REPORT_STATUSES.map((status) => (
                    <button
                      key={status}
                      className={`rounded-lg px-4 py-2 text-xs font-semibold uppercase tracking-widest transition-all duration-200 ${
                        statusFilter === status
                          ? "bg-blue-600 text-white shadow-md"
                          : "text-slate-500 hover:bg-white hover:text-blue-700 hover:shadow-sm"
                      }`}
                      onClick={() => setStatusFilter(status)}
                      type="button"
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>
              {llmCapacity ? (
                <div className="shrink-0 flex items-center gap-2 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
                  <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">Generation</span>
                  <span className={`text-xs font-semibold ${llmCapacity.generation.active >= llmCapacity.generation.limit ? "text-red-600" : "text-slate-800"}`}>
                    {llmCapacity.generation.active}/{llmCapacity.generation.limit}
                  </span>
                </div>
              ) : null}
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white py-5 px-6 shadow-sm flex flex-col">
            <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mb-3 px-1">Status totals</p>
            <div className="flex flex-col justify-between flex-1">
              <StatusTotal label="Processed" value={metrics.processed} />
              <StatusTotal label="Ready" value={metrics.ready} />
              <StatusTotal label="Assigned" value={metrics.assigned} />
              <StatusTotal label="Complete" value={metrics.complete} />
              <StatusTotal label="Hidden" value={metrics.hidden} />
            </div>
          </div>
        </div>

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
                onAssign={(mode) => void mutateAssignment(item.id, mode)}
                onGenerate={() => void handleGenerate(item.id)}
                onToggleHidden={() => void toggleHidden(item.id, !item.is_hidden)}
                onDelete={() => void removeReport(item.id)}
                onStartEdit={() => startEditingDisplayId(item)}
                onCancelEdit={() => cancelEditingDisplayId(item.id)}
                onSaveEdit={() => void saveDisplayId(item.id)}
                onPendingDisplayIdChange={(value) =>
                  setPendingDisplayIdByApp((current) => ({ ...current, [item.id]: value }))
                }
                pendingDisplayId={pendingDisplayIdByApp[item.id] ?? ""}
                isBusy={busyAppId === item.id}
                isGenerating={generatingAppId === item.id}
                generationCapacityFull={
                  (llmCapacity?.generation.active ?? 0) >= (llmCapacity?.generation.limit ?? Number.MAX_SAFE_INTEGER)
                }
                isHiddenBusy={hiddenBusyAppId === item.id}
                isDeleting={deletingAppId === item.id}
                isEditingDisplayId={editingDisplayIdAppId === item.id}
                isSavingDisplayId={savingDisplayIdAppId === item.id}
              />
            ))}
          </section>
        )}
      </div>
    </div>
  );
}

function getFilterActiveClasses(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") return "border border-blue-100 bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-slate-800 shadow-[0_10px_22px_rgba(148,163,184,0.16)]";
  if (status === "PROCESSED") return "border border-violet-200 bg-violet-100 text-violet-900 shadow-[0_8px_20px_rgba(221,214,254,0.32)]";
  if (status === "READY") return "border border-lime-200 bg-lime-100 text-lime-900 shadow-[0_8px_20px_rgba(190,242,100,0.28)]";
  if (status === "COMPLETE") return "border border-emerald-200 bg-emerald-100 text-emerald-900 shadow-[0_8px_20px_rgba(167,243,208,0.26)]";
  if (status === "ASSIGNED") return "border border-sky-200 bg-sky-100 text-sky-900 shadow-[0_8px_20px_rgba(186,230,253,0.28)]";
  return "border border-slate-200 bg-slate-100 text-slate-700 shadow-[0_8px_20px_rgba(226,232,240,0.24)]";
}


function getEmptyStateCopy(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") {
    return {
      title: "No visible reports right now.",
      description: "Generated reports will appear here once they move into review-ready states.",
    };
  }

  if (status === "PROCESSED") {
    return {
      title: "No processed reports yet.",
      description: "Reports with Pages 1-3 ready and waiting for synthesis will appear here.",
    };
  }

  if (status === "READY") {
    return {
      title: "No ready reports yet.",
      description: "Reports ready for assignment will appear here.",
    };
  }

  if (status === "ASSIGNED") {
    return {
      title: "No assigned reports yet.",
      description: "Reports currently owned by an interviewer will appear here.",
    };
  }

  if (status === "COMPLETE") {
    return {
      title: "No complete reports yet.",
      description: "Finalized post-interview reports will appear here.",
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
    <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 px-6 py-10 text-center shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="grid size-16 place-items-center overflow-hidden rounded-2xl border border-blue-200 bg-blue-50 shadow-sm">
          <Image
            alt="Interview Standardiser logo"
            className="h-14 w-14 scale-[1.28] object-cover"
            height={56}
            src="/Logo-removebg-preview.png"
            width={56}
          />
        </div>
        <h4
          className="mt-5 text-[2.1rem] font-black leading-[0.98] tracking-tight text-slate-800"
          style={{ fontFamily: "var(--font-reports-display)" }}
        >
          {copy.title}
        </h4>
        <p className="mt-3 text-sm leading-7 text-slate-600">{copy.description}</p>
      </div>
    </div>
  );
}

function StatusTotal({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={`${className ?? ""} flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-1.5 transition-all hover:bg-white hover:shadow-sm`}>
      <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">{label}</span>
      <span className="text-xs font-semibold text-slate-800">{value}</span>
    </div>
  );
}
