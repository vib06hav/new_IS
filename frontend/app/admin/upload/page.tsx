"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, ChevronLeft, ChevronRight, FileUp, Sparkles, Stars, Trash2 } from "lucide-react";
import {
  Libre_Franklin,
  IBM_Plex_Sans,
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

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-reports-display",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
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
  }, [localQueue]);

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

  async function handleRetry(applicationId: string) {
    const item = items.find((candidate) => candidate.id === applicationId);

    setMessage(null);
    setError(null);
    setBusyRetryId(applicationId);
    try {
      await retryApplication(applicationId);
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
      className={`${libreFranklin.variable} ${plexSans.variable} space-y-6`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="space-y-6">
            <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="relative">
                
                <div className="space-y-3">
                  <h1
                    className="max-w-4xl text-3xl md:text-4xl font-black tracking-tight text-slate-800 leading-none"
                    style={{ fontFamily: "var(--font-reports-display)" }}
                  >
                    Upload Queue
                  </h1>
                  <p className="max-w-3xl text-sm text-slate-600 leading-relaxed">
                    Queue PDFs, monitor processing, retry failures, and remove stale items before they re-enter the
                    pipeline.
                  </p>
                </div>
              </div>
            </section>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400">Status totals</p>
              <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-2">
                <MetricStrip label="Queued" value={metrics.queued} />
                <MetricStrip label="Processing" value={metrics.processing} />
                <MetricStrip label="Failed" value={metrics.failed} />
              </div>
            </div>

            <section className="grid gap-6 xl:grid-cols-[24rem_minmax(0,1fr)] xl:items-start">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Add PDFs</p>
                <div className="mt-5 flex flex-col gap-4 rounded-2xl border border-slate-100 bg-slate-50 p-4">
                  <input
                    id="application-pdf"
                    className="sr-only"
                    type="file"
                    accept="application/pdf"
                    multiple
                    onChange={handleFileSelection}
                  />

                  <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-8 text-center transition-colors hover:border-blue-400">
                    <div className="mx-auto grid size-12 place-items-center rounded-full bg-blue-100 text-blue-600">
                      <FileUp className="size-6" />
                    </div>
                    <div className="mt-5 flex flex-col items-center gap-4">
                      <Badge variant={selectedFiles.length > 0 ? "secondary" : "outline"} className="px-3 py-1">
                        {selectedFiles.length > 0
                          ? `${selectedFiles.length} PDF${selectedFiles.length === 1 ? "" : "s"} selected`
                          : "No PDFs selected yet"}
                      </Badge>
                      <label
                        htmlFor="application-pdf"
                        className="inline-flex cursor-pointer items-center justify-center rounded-full border border-slate-200 bg-white px-6 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:border-blue-500 hover:text-blue-700 hover:shadow-md"
                      >
                        Choose PDFs
                      </label>
                    </div>
                  </div>

                  <Separator className="bg-slate-200/60" />

                  <div className="flex items-center justify-between gap-3 rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
                    <div className="flex items-center gap-2 text-sm text-blue-700">
                      <Sparkles className="size-4" />
                      <span className="text-xs font-medium">
                        {selectedFiles.length > 0
                          ? "Ready to append these PDFs to the upload queue"
                          : hasPendingBrowserWork
                            ? "Queue is running. You can keep adding more PDFs."
                            : "Select one or many PDFs to start the batch"}
                      </span>
                    </div>
                    {selectedFiles.length > 0 ? (
                      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[#198FF0]">Batch ready</span>
                    ) : null}
                  </div>

                  <div className="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3 text-[11px] leading-relaxed text-amber-800">
                    Batch execution pauses if you refresh or leave this page. Any files already processed by the backend
                    stay saved with their latest status.
                  </div>

                  <ShadButton
                    className="w-full justify-center bg-blue-600 text-white shadow-sm hover:bg-blue-700 hover:shadow-md transition-all rounded-full h-11"
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
                  <p className="rounded-[1.2rem] border border-[#198FF0]/35 bg-[#EAF4FD] px-4 py-3 text-sm text-[#24527A]">{message}</p>
                ) : null}
                {error ? (
                  <p className="rounded-[1.2rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] px-4 py-3 text-sm text-[#9A315A]">{error}</p>
                ) : null}
                {duplicateMessage ? (
                  <p className="rounded-[1.2rem] border border-[#FFB347]/45 bg-[#FFF1DF] px-4 py-3 text-sm text-[#8C5B1C]">
                    {duplicateMessage}
                  </p>
                ) : null}

                <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Upload queue</p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        Queued, processing, and failed files stay visible in one operational list.
                      </p>
                    </div>
                  </div>

                  {loading ? (
                    <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-10">
                      <Loader label="Loading upload queue..." />
                    </div>
                  ) : queueRows.length === 0 ? (
                    <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-10 text-center">
                      <p className="text-base font-semibold text-[#111111]">No uploads in queue.</p>
                      <p className="mt-2 text-sm text-[#5F6C86]">QUEUED, PROCESSING, and FAILED items appear here.</p>
                    </div>
                  ) : (
                    <div className="mt-6 overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm ring-1 ring-slate-100">
                      <div className="grid gap-3 border-b border-slate-50 bg-slate-50 px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-slate-400 md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                        <span>Application</span>
                        <span>Status</span>
                        <span>Created</span>
                        <span>Action</span>
                      </div>

                      <div className="divide-y divide-slate-100">
                        {queueRows.map((row) => (
                          <div key={row.key} className="grid gap-4 px-4 py-4 md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr] md:items-center transition-colors hover:bg-slate-100/50">
                            <div className="space-y-1">
                              <p className="text-sm font-bold tracking-tight text-slate-800">{row.label}</p>
                              {row.kind === "pending" ? <p className="text-[11px] text-slate-500">{row.note}</p> : null}
                            </div>
                            <UploadStatusMark status={row.status} />
                            <p className="text-xs text-slate-500">{new Date(row.createdAt).toLocaleString()}</p>
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
    </div>
  );
}

function MetricStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-1.5 transition-all hover:bg-white hover:shadow-sm">
      <span className="text-[9px] font-bold uppercase tracking-widest text-slate-400">{label}</span>
      <span className="text-xs font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function UploadStatusMark({ status }: { status: QueueRow["status"] }) {
  const styles = {
    QUEUED: "bg-[#198FF0] text-[#F7F7F1]",
    PROCESSING: "bg-[#7CF0FF] text-[#111111]",
    FAILED: "bg-[#FF6B9D] text-[#111111]",
  } satisfies Record<QueueRow["status"], string>;

  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status]}`}>
      {status}
    </span>
  );
}
