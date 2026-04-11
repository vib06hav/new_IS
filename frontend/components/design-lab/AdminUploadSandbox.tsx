"use client";

import { motion } from "motion/react";
import { useMemo, useState } from "react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import {
  ArrowUpRight,
  FileUp,
  Sparkles,
  Stars,
  Trash2,
} from "lucide-react";
import { Badge } from "@/components/shadcn/badge";
import { Button as ShadButton } from "@/components/shadcn/button";
import { Separator } from "@/components/shadcn/separator";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Button } from "@/components/ui/Button";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
  display: "swap",
});

const sessionLogEntries = [
  {
    id: "upload-log-1",
    action: "Queued",
    subject: "candidate-batch-07.pdf",
    detail: "Added to browser batch and waiting for upload",
    time: "Just now",
    accent: "#dbeafe",
    badgeText: "#1e3a8a",
  },
  {
    id: "upload-log-2",
    action: "Retry",
    subject: "PLK-2026-0181",
    detail: "Failed upload sent back into processing",
    time: "3 min ago",
    accent: "#fef3c7",
    badgeText: "#92400e",
  },
  {
    id: "upload-log-3",
    action: "Failed",
    subject: "portfolio-scan-02.pdf",
    detail: "Upload stalled in browser and needs a fresh attempt",
    time: "8 min ago",
    accent: "#fee2e2",
    badgeText: "#9f1239",
  },
  {
    id: "upload-log-4",
    action: "Processing",
    subject: "PLK-2026-0184",
    detail: "Backend extraction is still running",
    time: "11 min ago",
    accent: "#e0f2fe",
    badgeText: "#0c4a6e",
  },
  {
    id: "upload-log-5",
    action: "Removed",
    subject: "candidate-batch-03.pdf",
    detail: "Pending file cleared from queue before upload",
    time: "18 min ago",
    accent: "#d9f99d",
    badgeText: "#365314",
  },
] as const;

type LocalQueueItem = {
  name: string;
  file?: File;
  added_at: string;
  status: "QUEUED" | "FAILED";
  note: string;
};

type MockApplication = {
  id: string;
  display_id: string;
  status: "PROCESSING" | "FAILED";
  created_at: string;
};

type QueueRow =
  | {
      kind: "pending";
      key: string;
      label: string;
      status: "QUEUED" | "FAILED";
      createdAt: string;
      action: "remove";
      note: string;
    }
  | {
      kind: "application";
      key: string;
      id: string;
      label: string;
      status: "PROCESSING" | "FAILED";
      createdAt: string;
      action: "retry" | "none";
    };

const initialApplications: MockApplication[] = [
  {
    id: "upload-1",
    display_id: "PLK-2026-0184",
    status: "PROCESSING",
    created_at: "2026-04-08T13:42:00.000Z",
  },
  {
    id: "upload-2",
    display_id: "PLK-2026-0181",
    status: "FAILED",
    created_at: "2026-04-08T13:24:00.000Z",
  },
];

const initialPendingQueue: LocalQueueItem[] = [
  {
    name: "candidate-batch-04.pdf",
    added_at: "2026-04-08T13:49:00.000Z",
    status: "QUEUED",
    note: "Waiting to be sent from this browser tab.",
  },
  {
    name: "portfolio-scan-02.pdf",
    added_at: "2026-04-08T13:19:00.000Z",
    status: "FAILED",
    note: "Upload failed in-browser. Review file and retry with a fresh batch.",
  },
];

function sortQueueRows(rows: QueueRow[]) {
  return [...rows].sort((a, b) => {
    if (a.kind !== b.kind) {
      return a.kind === "application" ? -1 : 1;
    }
    return b.createdAt.localeCompare(a.createdAt);
  });
}

export function AdminUploadSandbox() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [localQueue, setLocalQueue] = useState<LocalQueueItem[]>(initialPendingQueue);
  const [applications, setApplications] = useState<MockApplication[]>(initialApplications);
  const [busyRetryId, setBusyRetryId] = useState<string | null>(null);
  const [busyPendingRemoveName, setBusyPendingRemoveName] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [duplicateMessage, setDuplicateMessage] = useState<string | null>(null);

  const hasPendingBrowserWork = useMemo(
    () => localQueue.some((item) => item.status === "QUEUED") || applications.some((item) => item.status === "PROCESSING"),
    [applications, localQueue],
  );

  const metrics = useMemo(
    () => ({
      queued: localQueue.filter((item) => item.status === "QUEUED").length,
      processing: applications.filter((item) => item.status === "PROCESSING").length,
      failed:
        applications.filter((item) => item.status === "FAILED").length +
        localQueue.filter((item) => item.status === "FAILED").length,
    }),
    [applications, localQueue],
  );

  const queueRows = useMemo(
    () =>
      sortQueueRows([
        ...applications.map<QueueRow>((item) => ({
          kind: "application",
          key: item.id,
          id: item.id,
          label: item.display_id,
          status: item.status,
          createdAt: item.created_at,
          action: item.status === "FAILED" ? "retry" : "none",
        })),
        ...localQueue.map<QueueRow>((item) => ({
          kind: "pending",
          key: `pending:${item.name}`,
          label: item.name,
          status: item.status,
          createdAt: item.added_at,
          action: "remove",
          note: item.note,
        })),
      ]),
    [applications, localQueue],
  );

  function handleFileSelection(event: React.ChangeEvent<HTMLInputElement>) {
    const chosenFiles = Array.from(event.target.files ?? []);
    setSelectedFiles(chosenFiles);
    event.target.value = "";
  }

  function handleAddToBatch() {
    if (selectedFiles.length === 0) return;

    setMessage(null);
    setError(null);

    const seenNames = new Set(localQueue.map((item) => item.name));
    const duplicates: string[] = [];
    const validSelections: LocalQueueItem[] = [];

    for (const file of selectedFiles) {
      const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
      if (!isPdf) {
        duplicates.push(`${file.name} (not a PDF)`);
        continue;
      }
      if (seenNames.has(file.name)) {
        duplicates.push(file.name);
        continue;
      }
      seenNames.add(file.name);
      validSelections.push({
        name: file.name,
        file,
        added_at: new Date().toISOString(),
        status: "QUEUED",
        note: "Waiting to be sent from this browser tab.",
      });
    }

    if (validSelections.length > 0) {
      setLocalQueue((currentItems) => [...validSelections, ...currentItems]);
      setMessage(`${validSelections.length} PDF${validSelections.length === 1 ? "" : "s"} added to the upload queue.`);
    }

    if (duplicates.length > 0) {
      setDuplicateMessage(
        `Skipped ${duplicates.length} duplicate or invalid selection${duplicates.length === 1 ? "" : "s"}: ${duplicates.join(", ")}`,
      );
    } else {
      setDuplicateMessage(null);
    }

    setSelectedFiles([]);
  }

  function handleRemovePending(name: string) {
    setMessage(null);
    setError(null);
    setBusyPendingRemoveName(name);
    setLocalQueue((currentItems) => currentItems.filter((item) => item.name !== name));
    setMessage(`Removed ${name} from the queue.`);
    setBusyPendingRemoveName(null);
  }

  function handleRetry(applicationId: string) {
    setMessage(null);
    setError(null);
    setBusyRetryId(applicationId);
    setApplications((currentItems) =>
      currentItems.map((item) =>
        item.id === applicationId ? { ...item, status: "PROCESSING", created_at: new Date().toISOString() } : item,
      ),
    );
    setMessage("Retry triggered.");
    setBusyRetryId(null);
  }

  return (
    <div
      className={`${libreFranklin.variable} ${ibmPlexSans.variable} min-h-screen text-slate-900`}
      style={pageCanvasStyle}
    >
      <div className="min-h-screen">
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="min-h-screen text-slate-900"
          initial={{ opacity: 0, y: 26 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
        >
          <AdminDesignLabNavbar activeItem="Upload" />

          <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
              <div className="space-y-6">
                <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
                  <div className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm xl:h-full">
                    <div className="flex h-full flex-col">
                      <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
                        <span className="inline-flex items-center gap-2 text-slate-800">
                          <Stars className="size-3.5" />
                          Document ingestion
                        </span>
                      </div>
                      <div className="mt-5 space-y-4">
                        <h1
                          className="max-w-4xl text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                          style={{ fontFamily: "var(--font-display)" }}
                        >
                          Upload Queue
                        </h1>
                        <p className="max-w-3xl text-base leading-[1.6] text-slate-600" style={{ fontFamily: "var(--font-body)" }}>
                          Queue PDFs, monitor processing, retry failures, and remove stale items before they re-enter the
                          pipeline.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm xl:h-full">
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Status totals</p>
                    <div className="mt-4 space-y-3">
                      <MetricStrip label="Queued" value={metrics.queued} />
                      <MetricStrip label="Processing" value={metrics.processing} />
                      <MetricStrip label="Failed" value={metrics.failed} />
                    </div>
                  </div>
                </section>

                <section className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)] xl:items-start">
                  <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                    <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Add PDFs</p>
                    <div className="mt-4 flex flex-col gap-4 rounded-[1.4rem] border border-slate-200 bg-white/70 p-4">
                      <input
                        id="application-pdf"
                        className="sr-only"
                        type="file"
                        accept="application/pdf"
                        multiple
                        onChange={handleFileSelection}
                      />

                      <div className="rounded-[1.4rem] border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-center">
                        <div className="mx-auto grid size-11 place-items-center rounded-full bg-blue-700 text-white">
                          <FileUp className="size-5" />
                        </div>
                        <div className="mt-4 flex flex-col items-center gap-3">
                          <Badge variant={selectedFiles.length > 0 ? "secondary" : "outline"}>
                            {selectedFiles.length > 0
                              ? `${selectedFiles.length} PDF${selectedFiles.length === 1 ? "" : "s"} selected`
                              : "No PDFs selected yet"}
                          </Badge>
                          <label
                            htmlFor="application-pdf"
                            className="inline-flex cursor-pointer items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50"
                          >
                            Choose PDFs
                          </label>
                        </div>
                      </div>

                      <Separator />

                      <div className="flex items-center justify-between gap-3 rounded-[1.2rem] border border-slate-200 bg-white px-4 py-3">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Sparkles className="size-4 text-blue-700" />
                          <span>
                            {selectedFiles.length > 0
                              ? "Ready to append these PDFs to the upload queue"
                              : hasPendingBrowserWork
                                ? "Queue is running. You can keep adding more PDFs."
                                : "Select one or many PDFs to start the batch"}
                          </span>
                        </div>
                        {selectedFiles.length > 0 ? (
                          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">Batch ready</span>
                        ) : null}
                      </div>

                      <div className="rounded-[1.2rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                        Batch execution pauses if you refresh or leave this page. Any files already processed by the backend
                        stay saved with their latest status.
                      </div>

                      <ShadButton className="w-full justify-center bg-blue-700 text-white hover:bg-blue-800" disabled={selectedFiles.length === 0} onClick={handleAddToBatch}>
                        <ArrowUpRight data-icon="inline-end" />
                        Add to Batch
                      </ShadButton>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {message ? (
                      <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p>
                    ) : null}
                    {error ? (
                      <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
                    ) : null}
                    {duplicateMessage ? (
                      <p className="rounded-[1.2rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                        {duplicateMessage}
                      </p>
                    ) : null}

                    <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Upload queue</p>
                          <p className="mt-2 text-sm leading-6 text-slate-600">
                            Queued, processing, and failed files stay visible in one operational list.
                          </p>
                        </div>
                      </div>

                      {queueRows.length === 0 ? (
                        <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white px-4 py-10 text-center">
                          <p className="text-base font-semibold text-slate-800">No uploads in queue.</p>
                          <p className="mt-2 text-sm text-slate-500">
                            QUEUED, PROCESSING, and FAILED items appear here.
                          </p>
                        </div>
                      ) : (
                        <div className="mt-5 overflow-hidden rounded-[1.4rem] border border-slate-200 bg-white/70">
                          <div className="grid gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                            <span>Application</span>
                            <span>Status</span>
                            <span>Created</span>
                            <span>Action</span>
                          </div>

                          <div className="divide-y divide-slate-200">
                            {queueRows.map((row) => (
                              <div key={row.key} className="grid gap-4 px-4 py-4 md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr] md:items-center">
                                <div className="space-y-1">
                                  <p className="text-base font-semibold tracking-tight text-slate-800">{row.label}</p>
                                  {row.kind === "pending" ? <p className="text-xs text-slate-500">{row.note}</p> : null}
                                </div>
                                <UploadStatusMark status={row.status} />
                                <p className="text-sm text-slate-600">{new Date(row.createdAt).toLocaleString()}</p>
                                <div className="flex items-center gap-2">
                                  {row.action === "retry" && row.kind === "application" ? (
                                    <button
                                      className="rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
                                      disabled={busyRetryId === row.id}
                                      onClick={() => handleRetry(row.id)}
                                      type="button"
                                    >
                                      {busyRetryId === row.id ? "Retrying..." : "Retry"}
                                    </button>
                                  ) : null}
                                  {row.action === "remove" && row.kind === "pending" ? (
                                    <button
                                      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                                      disabled={busyPendingRemoveName === row.label}
                                      onClick={() => handleRemovePending(row.label)}
                                      type="button"
                                    >
                                      <Trash2 className="size-4" />
                                      {busyPendingRemoveName === row.label ? "Removing..." : "Remove"}
                                    </button>
                                  ) : null}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </section>
              </div>

              <aside className="grid gap-5 self-start">
                <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                  <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Session log</p>
                  <p className="mt-3 text-sm leading-6 text-slate-600">Actions taken during this session appear here in order.</p>
                  <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white/70">
                    <div className="border-b border-slate-200 px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Current session</p>
                    </div>
                    <div className="divide-y divide-slate-200">
                      {sessionLogEntries.map((entry) => (
                        <div key={entry.id} className="px-4 py-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span
                                  className="inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]"
                                  style={{ backgroundColor: entry.accent, color: entry.badgeText }}
                                >
                                  {entry.action}
                                </span>
                                <p className="text-sm font-semibold text-slate-800">{entry.subject}</p>
                              </div>
                              <p className="mt-2 text-sm leading-6 text-slate-600">{entry.detail}</p>
                            </div>
                            <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                              {entry.time}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function MetricStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-slate-200 bg-white px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function UploadStatusMark({ status }: { status: QueueRow["status"] }) {
  const styles = {
    QUEUED: "border-blue-200 bg-blue-100 text-blue-900",
    PROCESSING: "border-sky-200 bg-sky-100 text-sky-900",
    FAILED: "border-rose-200 bg-rose-100 text-rose-800",
  } satisfies Record<QueueRow["status"], string>;

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status]}`}>
      {status}
    </span>
  );
}

const pageCanvasStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  backgroundImage: "radial-gradient(#e2e8f0 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
  fontFamily: "var(--font-body)",
};
