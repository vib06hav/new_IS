"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, FileUp, Sparkles, Stars, Trash2 } from "lucide-react";
import {
  IBM_Plex_Sans,
  Libre_Franklin,
} from "next/font/google";
import { fetchApplications, retryApplication, uploadApplication } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Loader } from "@/components/ui/Loader";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { Badge } from "@/components/shadcn/badge";
import { Button as ShadButton } from "@/components/shadcn/button";
import { Separator } from "@/components/shadcn/separator";
import { AdminSessionLogPanel } from "@/components/layout/AdminSessionLogPanel";
import { useAdminSessionHistory } from "@/components/layout/AdminSessionHistory";

type LocalQueueItem = {
  name: string;
  file: File;
  added_at: string;
  status: "QUEUED" | "FAILED";
  note: string;
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

function sortQueueRows(rows: QueueRow[]) {
  return [...rows].sort((a, b) => {
    if (a.kind !== b.kind) {
      return a.kind === "application" ? -1 : 1;
    }
    return b.createdAt.localeCompare(a.createdAt);
  });
}

export default function AdminUploadPage() {
  return (
    <AdminShell>
      <AdminUploadContent />
    </AdminShell>
  );
}

function AdminUploadContent() {
  const isMountedRef = useRef(true);
  const processingLoopActiveRef = useRef(false);
  const localQueueRef = useRef<LocalQueueItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [localQueue, setLocalQueue] = useState<LocalQueueItem[]>([]);
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyRetryId, setBusyRetryId] = useState<string | null>(null);
  const [busyPendingRemoveName, setBusyPendingRemoveName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [duplicateMessage, setDuplicateMessage] = useState<string | null>(null);
  const { entries: sessionHistoryEntries, addEntry } = useAdminSessionHistory();

  async function loadUploads() {
    try {
      const [processing, failed] = await Promise.all([
        fetchApplications("PROCESSING"),
        fetchApplications("FAILED"),
      ]);

      const nextItems = [...processing, ...failed]
        .filter((item): item is ApplicationListItem & { status: "PROCESSING" | "FAILED" } =>
          item.status === "PROCESSING" || item.status === "FAILED",
        )
        .sort((a, b) => b.created_at.localeCompare(a.created_at));

      setItems(nextItems);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load upload queue.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUploads();
  }, []);

  useEffect(() => {
    localQueueRef.current = localQueue;
  }, [localQueue]);

  useEffect(() => {
    isMountedRef.current = true;
    processingLoopActiveRef.current = false;

    return () => {
      isMountedRef.current = false;
      processingLoopActiveRef.current = false;
    };
  }, []);

  usePolling(loadUploads, uploading ? 1000 : 5000, !loading);

  const hasPendingBrowserWork = useMemo(
    () => localQueue.some((item) => item.status === "QUEUED") || items.some((item) => item.status === "PROCESSING"),
    [items, localQueue],
  );

  const metrics = useMemo(
    () => ({
      queued: localQueue.filter((item) => item.status === "QUEUED").length,
      processing: items.filter((item) => item.status === "PROCESSING").length,
      failed:
        items.filter((item) => item.status === "FAILED").length +
        localQueue.filter((item) => item.status === "FAILED").length,
    }),
    [items, localQueue],
  );

  useEffect(() => {
    if (!hasPendingBrowserWork) {
      return;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasPendingBrowserWork]);

  useEffect(() => {
    if (processingLoopActiveRef.current) {
      return;
    }
    if (!localQueue.some((item) => item.status === "QUEUED")) {
      return;
    }

    processingLoopActiveRef.current = true;

    async function processQueueLoop() {
      while (isMountedRef.current) {
        const nextItem = localQueueRef.current.find((item) => item.status === "QUEUED");
        if (!nextItem) {
          break;
        }

        if (isMountedRef.current) {
          setUploading(true);
        }

        addEntry({
          action: "Processing",
          reportId: nextItem.name,
          detail: "Backend extraction has started for this PDF.",
          tone: "cyan",
        });

        setLocalQueue((currentItems) => currentItems.filter((currentItem) => currentItem.name !== nextItem.name));
        await loadUploads();

        try {
          await uploadApplication(nextItem.file);
          if (!isMountedRef.current) {
            return;
          }
          await loadUploads();
        } catch (uploadError) {
          if (!isMountedRef.current) {
            return;
          }
          const errorMessage = uploadError instanceof Error ? uploadError.message : "Upload failed.";
          setLocalQueue((currentItems) => [
            {
              ...nextItem,
              status: "FAILED",
              note: errorMessage,
            },
            ...currentItems,
          ]);
          setError(errorMessage);
          addEntry({
            action: "Failed",
            reportId: nextItem.name,
            detail: errorMessage,
            tone: "pink",
          });
          await loadUploads();
        } finally {
          if (isMountedRef.current) {
            setUploading(false);
          }
        }
      }

      processingLoopActiveRef.current = false;
    }

    void processQueueLoop();
  }, [addEntry, localQueue]);

  function handleFileSelection(event: React.ChangeEvent<HTMLInputElement>) {
    const chosenFiles = Array.from(event.target.files ?? []);
    setSelectedFiles(chosenFiles);
    event.target.value = "";
  }

  function handleAddToBatch() {
    if (selectedFiles.length === 0) {
      return;
    }

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
      validSelections.forEach((selection) => {
        addEntry({
          action: "Queued",
          reportId: selection.name,
          detail: "Added to browser batch and waiting for upload.",
          tone: "blue",
        });
      });
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
    addEntry({
      action: "Removed",
      reportId: name,
      detail: "Pending file cleared from the browser queue.",
      tone: "lime",
    });
    setBusyPendingRemoveName(null);
  }

  async function handleRetry(applicationId: string) {
    const item = items.find((candidate) => candidate.id === applicationId);

    setMessage(null);
    setError(null);
    setBusyRetryId(applicationId);
    try {
      await retryApplication(applicationId);
      if (item) {
        addEntry({
          action: "Retry",
          reportId: item.display_id,
          detail: "Failed upload sent back into processing.",
          tone: "orange",
        });
      }
      setMessage("Retry triggered.");
      await loadUploads();
    } catch (retryError) {
      setError(retryError instanceof Error ? retryError.message : "Retry failed.");
    } finally {
      setBusyRetryId(null);
    }
  }

  const queueRows = useMemo(
    () =>
      sortQueueRows([
        ...items.map<QueueRow>((item) => ({
          kind: "application",
          key: item.id,
          id: item.id,
          label: item.display_id,
          status: item.status as "PROCESSING" | "FAILED",
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
    [items, localQueue],
  );

  return (
    <div
      className={`${plexSans.variable} ${libreFranklin.variable} space-y-6`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm xl:h-full">
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
                    <p className="max-w-3xl text-base leading-[1.6] text-slate-600">
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

                  <ShadButton
                    className="w-full justify-center bg-blue-700 text-white hover:bg-blue-800"
                    disabled={selectedFiles.length === 0}
                    onClick={handleAddToBatch}
                  >
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

                  {loading ? (
                    <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white px-4 py-10">
                      <Loader label="Loading upload queue..." />
                    </div>
                  ) : queueRows.length === 0 ? (
                    <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white px-4 py-10 text-center">
                      <p className="text-base font-semibold text-slate-800">No uploads in queue.</p>
                      <p className="mt-2 text-sm text-slate-500">QUEUED, PROCESSING, and FAILED items appear here.</p>
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
                                <Button disabled={busyRetryId === row.id} onClick={() => void handleRetry(row.id)}>
                                  {busyRetryId === row.id ? "Retrying..." : "Retry"}
                                </Button>
                              ) : null}
                              {row.action === "remove" && row.kind === "pending" ? (
                                <Button
                                  variant="secondary"
                                  disabled={busyPendingRemoveName === row.label}
                                  onClick={() => handleRemovePending(row.label)}
                                >
                                  <Trash2 className="size-4" />
                                  {busyPendingRemoveName === row.label ? "Removing..." : "Remove"}
                                </Button>
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
          <AdminSessionLogPanel entries={sessionHistoryEntries} />
        </aside>
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
