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
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
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

export function ReportsDashboardSandboxPlayground() {
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

      setItems(applications);
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
    if (!report) return;

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
      className={`${plexSans.variable} ${libreFranklin.variable} min-h-screen bg-slate-50`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <AdminDesignLabNavbar activeItem="Reports" />

      <main className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8 space-y-6">
        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_20rem] gap-6 items-stretch">
            <div className="space-y-6">
              <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm transition-all duration-200 hover:shadow-md">
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

            <div className="rounded-3xl border border-slate-200 bg-white py-5 px-6 shadow-sm flex flex-col justify-center">
              <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mb-3 px-1">Status totals</p>
              <div className="flex flex-col gap-1.5">
                <StatusTotalStrip label="Processed" value={metrics.processed} />
                <StatusTotalStrip label="Ready" value={metrics.ready} />
                <StatusTotalStrip label="Assigned" value={metrics.assigned} />
                <StatusTotalStrip label="Complete" value={metrics.complete} />
                <StatusTotalStrip label="Hidden" value={metrics.hidden} />
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
      </main>
    </div>
  );
}

function ReportsEmptyState({ statusFilter }: { statusFilter: (typeof REPORT_STATUSES)[number] }) {
  const copy = getEmptyStateCopy(statusFilter);

  return (
    <div className="rounded-[1.9rem] border border-slate-200 bg-[#F7F7F1] px-6 py-10 text-center shadow-sm">
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="grid size-16 place-items-center overflow-hidden rounded-2xl border border-blue-100 bg-blue-50 shadow-sm">
          <Image
            alt="Interview Standardiser logo"
            className="h-14 w-14 scale-[1.28] object-cover"
            height={56}
            src="/Logo-removebg-preview.png"
            width={56}
          />
        </div>
        <h4 className="mt-5 text-[2.1rem] leading-[0.95] tracking-tight text-slate-800 font-bold">
          {copy.title}
        </h4>
        <p className="mt-3 text-sm leading-7 text-slate-500">{copy.description}</p>
      </div>
    </div>
  );
}

function StatusTotalStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-1.5 transition-all hover:bg-white hover:shadow-sm">
      <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
      <span className="text-xs font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function getEmptyStateCopy(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") return { title: "No visible reports right now.", description: "Generated reports will appear here once they move into review-ready states." };
  if (status === "PROCESSED") return { title: "No processed reports yet.", description: "Reports with Pages 1-3 ready and waiting for synthesis will appear here." };
  if (status === "READY") return { title: "No ready reports yet.", description: "Reports ready for assignment will appear here." };
  if (status === "ASSIGNED") return { title: "No assigned reports yet.", description: "Reports currently owned by an interviewer will appear here." };
  if (status === "COMPLETE") return { title: "No complete reports yet.", description: "Finalized post-interview reports will appear here." };
  return { title: "No hidden reports yet.", description: "Reports you hide from the main view will appear here." };
}
