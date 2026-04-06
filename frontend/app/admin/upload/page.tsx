"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowUpRight, FileUp, Sparkles, Trash2 } from "lucide-react";
import { fetchApplications, removeQueuedApplication, retryApplication, uploadApplication } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { HeroPanel } from "@/components/ui/HeroPanel";
import { Card } from "@/components/ui/Card";
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
      status: string;
      createdAt: string;
      action: "retry" | "remove" | "none";
    };

function sortQueueRows(rows: QueueRow[]) {
  return [...rows].sort((a, b) => {
    if (a.kind !== b.kind) {
      return a.kind === "application" ? -1 : 1;
    }
    return b.createdAt.localeCompare(a.createdAt);
  });
};

export default function AdminUploadPage() {
  const isMountedRef = useRef(true);
  const processingLoopActiveRef = useRef(false);
  const localQueueRef = useRef<LocalQueueItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [localQueue, setLocalQueue] = useState<LocalQueueItem[]>([]);
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyRetryId, setBusyRetryId] = useState<string | null>(null);
  const [busyRemoveId, setBusyRemoveId] = useState<string | null>(null);
  const [busyPendingRemoveName, setBusyPendingRemoveName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [duplicateMessage, setDuplicateMessage] = useState<string | null>(null);
  const [queueDebug, setQueueDebug] = useState<string>("Idle");

  async function loadUploads() {
    try {
      const [uploaded, processing, failed] = await Promise.all([
        fetchApplications("UPLOADED"),
        fetchApplications("PROCESSING"),
        fetchApplications("FAILED"),
      ]);
      setItems([...uploaded, ...processing, ...failed].sort((a, b) => b.created_at.localeCompare(a.created_at)));
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
    () => localQueue.some((item) => item.status === "QUEUED") || uploading,
    [localQueue, uploading],
  );
  const metrics = useMemo(
    () => ({
      queued: localQueue.filter((item) => item.status === "QUEUED").length,
      processing: items.filter((item) => item.status === "PROCESSING").length,
      failed: items.filter((item) => item.status === "FAILED").length + localQueue.filter((item) => item.status === "FAILED").length,
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
      if (isMountedRef.current) {
        setQueueDebug(`Runner started with ${localQueueRef.current.filter((item) => item.status === "QUEUED").length} queued item(s).`);
      }

      while (isMountedRef.current) {
        const nextItem = localQueueRef.current.find((item) => item.status === "QUEUED");
        if (!nextItem) {
          break;
        }

        if (isMountedRef.current) {
          setUploading(true);
          setQueueDebug(`Starting upload for ${nextItem.name}. Remaining queued before start: ${localQueueRef.current.filter((item) => item.status === "QUEUED").length}.`);
        }

        setLocalQueue((currentItems) => currentItems.filter((currentItem) => currentItem.name !== nextItem.name));
        await loadUploads();

        try {
          await uploadApplication(nextItem.file);
          if (!isMountedRef.current) {
            return;
          }
          setQueueDebug(`Upload finished for ${nextItem.name}. Refreshing queue before moving to the next file.`);
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
          setQueueDebug(`Upload failed for ${nextItem.name}: ${errorMessage}`);
          await loadUploads();
        } finally {
          if (isMountedRef.current) {
            setUploading(false);
          }
        }
      }

      if (isMountedRef.current) {
        setQueueDebug("Runner idle. No queued items left.");
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
      setLocalQueue((currentItems) => [...currentItems, ...validSelections]);
      setMessage(
        `${validSelections.length} PDF${validSelections.length === 1 ? "" : "s"} added to the upload queue.`,
      );
      setError(null);
    }

    if (duplicates.length > 0) {
      setDuplicateMessage(`Skipped ${duplicates.length} duplicate or invalid selection${duplicates.length === 1 ? "" : "s"}: ${duplicates.join(", ")}`);
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

  async function handleRemove(applicationId: string) {
    if (!window.confirm("Remove this PDF from the queue?")) {
      return;
    }

    setMessage(null);
    setError(null);
    setBusyRemoveId(applicationId);
    try {
      await removeQueuedApplication(applicationId);
      setMessage("Queue item removed.");
      await loadUploads();
    } catch (removeError) {
      setError(removeError instanceof Error ? removeError.message : "Failed to remove queue item.");
    } finally {
      setBusyRemoveId(null);
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
          status: item.status,
          createdAt: item.created_at,
          action: item.status === "FAILED" ? "retry" : item.status === "UPLOADED" || item.status === "FAILED" ? "remove" : "none",
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
    <AdminShell>
      <div className="space-y-6">
        <HeroPanel
          eyebrow="Document ingestion"
          title="Upload Queue"
          metrics={[
            { label: "Queued", value: String(metrics.queued) },
            { label: "Processing", value: String(metrics.processing) },
            { label: "Failed", value: String(metrics.failed) },
          ]}
        />

        <div className="grid gap-6 xl:grid-cols-[24rem_1fr] xl:items-start">
          <div className="self-start">
            <Card title="Add PDFs">
              <div className="flex flex-col gap-4">
                <input
                  id="application-pdf"
                  className="sr-only"
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={handleFileSelection}
                />

                <div className="upload-dropzone">
                  <span className="upload-glyph" aria-hidden="true">
                    <FileUp className="size-5" />
                  </span>
                  <Badge variant={selectedFiles.length > 0 ? "secondary" : "outline"}>
                    {selectedFiles.length > 0
                      ? `${selectedFiles.length} PDF${selectedFiles.length === 1 ? "" : "s"} selected`
                      : "No PDFs selected yet"}
                  </Badge>
                  <label
                    htmlFor="application-pdf"
                    className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-[color:var(--surface-border)] bg-white px-3 py-2 text-sm font-medium text-[color:var(--brand-deep)] shadow-sm transition hover:border-blue-200 hover:bg-blue-50/70"
                  >
                    Choose PDFs
                  </label>
                </div>

                <Separator />

                <div className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/70 px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
                    <Sparkles className="size-4 text-[color:var(--accent)]" />
                    <span>
                      {selectedFiles.length > 0
                        ? "Ready to append these PDFs to the upload queue"
                        : hasPendingBrowserWork
                          ? "Queue is running. You can keep adding more PDFs."
                          : "Select one or many PDFs to start the batch"}
                    </span>
                  </div>
                  {selectedFiles.length > 0 ? (
                    <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--accent)]">Batch ready</span>
                  ) : null}
                </div>

                <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  Batch execution pauses if you refresh or leave this page. Any files already processed by the backend stay saved with their latest status.
                </div>

                <ShadButton className="w-full justify-center" disabled={selectedFiles.length === 0} onClick={handleAddToBatch}>
                  <ArrowUpRight data-icon="inline-end" />
                  Add to Batch
                </ShadButton>
              </div>
            </Card>
          </div>

          <div className="space-y-4">
            {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}
            {duplicateMessage ? (
              <p className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-800">{duplicateMessage}</p>
            ) : null}
            <p className="rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-xs text-stone-700">{queueDebug}</p>

            {loading ? (
              <Loader label="Loading upload queue..." />
            ) : queueRows.length === 0 ? (
              <EmptyState title="No uploads in queue." description="QUEUED, UPLOADED, PROCESSING, and FAILED items appear here." />
            ) : (
              <Card title="Upload Queue">
                <div className="data-table">
                  <div className="data-table-header md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                    <span>Application</span>
                    <span>Status</span>
                    <span>Created</span>
                    <span>Action</span>
                  </div>
                  {queueRows.map((row) => (
                    <div key={row.key} className="data-table-row md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                      <div className="space-y-1">
                        <p className="display-font text-base font-semibold text-[color:var(--ink)]">{row.label}</p>
                        {row.kind === "pending" ? <p className="text-xs text-[color:var(--muted)]">{row.note}</p> : null}
                      </div>
                      <StatusBadge status={row.status} />
                      <p className="text-sm text-[color:var(--muted)]">{new Date(row.createdAt).toLocaleString()}</p>
                      <div className="flex items-center gap-2">
                        {row.action === "retry" && row.kind === "application" ? (
                          <Button disabled={busyRetryId === row.id} onClick={() => void handleRetry(row.id)}>
                            {busyRetryId === row.id ? "Retrying..." : "Retry"}
                          </Button>
                        ) : null}
                        {row.action === "remove" && row.kind === "application" ? (
                          <Button
                            variant="secondary"
                            disabled={busyRemoveId === row.id}
                            onClick={() => void handleRemove(row.id)}
                          >
                            <Trash2 className="size-4" />
                            {busyRemoveId === row.id ? "Removing..." : "Remove"}
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
                        {row.action === "none" ? <span className="text-sm text-[color:var(--muted)]">Waiting</span> : null}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
