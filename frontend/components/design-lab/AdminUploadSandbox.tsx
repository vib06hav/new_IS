"use client";

import { motion } from "motion/react";
import { useMemo, useState } from "react";
import Image from "next/image";
import {
  Cormorant_Garamond,
  IBM_Plex_Sans,
  Space_Grotesk,
} from "next/font/google";
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

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
});

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

const sessionLogEntries = [
  {
    id: "upload-log-1",
    action: "Queued",
    subject: "candidate-batch-07.pdf",
    detail: "Added to browser batch and waiting for upload",
    time: "Just now",
    accent: "#198FF0",
    badgeText: "#F7F7F1",
  },
  {
    id: "upload-log-2",
    action: "Retry",
    subject: "PLK-2026-0181",
    detail: "Failed upload sent back into processing",
    time: "3 min ago",
    accent: "#FFB347",
    badgeText: "#111111",
  },
  {
    id: "upload-log-3",
    action: "Failed",
    subject: "portfolio-scan-02.pdf",
    detail: "Upload stalled in browser and needs a fresh attempt",
    time: "8 min ago",
    accent: "#FF6B9D",
    badgeText: "#111111",
  },
  {
    id: "upload-log-4",
    action: "Processing",
    subject: "PLK-2026-0184",
    detail: "Backend extraction is still running",
    time: "11 min ago",
    accent: "#7CF0FF",
    badgeText: "#111111",
  },
  {
    id: "upload-log-5",
    action: "Removed",
    subject: "candidate-batch-03.pdf",
    detail: "Pending file cleared from queue before upload",
    time: "18 min ago",
    accent: "#D7FF53",
    badgeText: "#111111",
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
  const [busyRemoveId, setBusyRemoveId] = useState<string | null>(null);
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

  function handleRemove(applicationId: string) {
    setMessage(null);
    setError(null);
    setBusyRemoveId(applicationId);
    setApplications((currentItems) => currentItems.filter((item) => item.id !== applicationId));
    setMessage("Queue item removed.");
    setBusyRemoveId(null);
  }

  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        cormorant.variable,
        "min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="min-h-screen">
        <motion.div
          animate={{ opacity: 1, y: 0 }}
          className="min-h-screen bg-[#D8DBE2] text-[#111111]"
          initial={{ opacity: 0, y: 26 }}
          transition={{ duration: 0.55, ease: "easeOut" }}
        >
          <AdminDesignLabNavbar activeItem="Upload" />

          <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
              <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
              <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6 xl:h-full">
                <div className="flex h-full flex-col">
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                    <span className="inline-flex items-center gap-2 text-[#111111]">
                      <Stars className="size-3.5" />
                      Document ingestion
                    </span>
                  </div>
                  <div className="mt-5 space-y-4">
                    <h1
                      className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.85rem]"
                      style={{ fontFamily: "var(--font-reports-cormorant)" }}
                    >
                      Upload Queue
                    </h1>
                    <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                      Queue PDFs, monitor processing, retry failures, and remove stale items before they re-enter the
                      pipeline.
                    </p>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 xl:h-full">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Status totals</p>
                <div className="mt-4 space-y-3">
                  <MetricStrip label="Queued" value={metrics.queued} />
                  <MetricStrip label="Processing" value={metrics.processing} />
                  <MetricStrip label="Failed" value={metrics.failed} />
                </div>
              </div>
            </section>

            <section className="grid gap-4 xl:grid-cols-[24rem_minmax(0,1fr)] xl:items-start">
              <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-5">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Add PDFs</p>
                <div className="mt-4 flex flex-col gap-4 rounded-[1.4rem] border border-[#727D97] bg-[#F7F7F1] p-4">
                  <input
                    id="application-pdf"
                    className="sr-only"
                    type="file"
                    accept="application/pdf"
                    multiple
                    onChange={handleFileSelection}
                  />

                  <div className="rounded-[1.4rem] border border-dashed border-[#727D97] bg-[#E6E9F0] px-4 py-5 text-center">
                    <div className="mx-auto grid size-11 place-items-center rounded-full bg-[#198FF0] text-[#F7F7F1]">
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
                        className="inline-flex cursor-pointer items-center justify-center rounded-full border border-[#727D97] bg-white px-4 py-2 text-sm font-semibold text-[#111111] transition hover:border-[#198FF0] hover:bg-[#EAF4FD]"
                      >
                        Choose PDFs
                      </label>
                    </div>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between gap-3 rounded-[1.2rem] border border-[#727D97] bg-[#E6E9F0] px-4 py-3">
                    <div className="flex items-center gap-2 text-sm text-[#49536B]">
                      <Sparkles className="size-4 text-[#198FF0]" />
                      <span>
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

                  <div className="rounded-[1.2rem] border border-[#FFB347]/45 bg-[#FFF1DF] px-4 py-3 text-sm text-[#8C5B1C]">
                    Batch execution pauses if you refresh or leave this page. Any files already processed by the backend
                    stay saved with their latest status.
                  </div>

                  <ShadButton className="w-full justify-center bg-[#111111] text-[#F7F7F1] hover:bg-[#2B3444]" disabled={selectedFiles.length === 0} onClick={handleAddToBatch}>
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

                <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Upload queue</p>
                      <p className="mt-2 text-sm leading-6 text-[#49536B]">
                        Queued, processing, and failed files stay visible in one operational list.
                      </p>
                    </div>
                  </div>

                  {queueRows.length === 0 ? (
                    <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-10 text-center">
                      <p className="text-base font-semibold text-[#111111]">No uploads in queue.</p>
                      <p className="mt-2 text-sm text-[#5F6C86]">
                        QUEUED, PROCESSING, and FAILED items appear here.
                      </p>
                    </div>
                  ) : (
                    <div className="mt-5 overflow-hidden rounded-[1.4rem] border border-[#727D97] bg-[#F7F7F1]">
                      <div className="grid gap-3 border-b border-[#727D97] bg-[#E6E9F0] px-4 py-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86] md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                        <span>Application</span>
                        <span>Status</span>
                        <span>Created</span>
                        <span>Action</span>
                      </div>

                      <div className="divide-y divide-[#727D97]/45">
                        {queueRows.map((row) => (
                          <div key={row.key} className="grid gap-4 px-4 py-4 md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr] md:items-center">
                            <div className="space-y-1">
                              <p className="text-base font-semibold tracking-[-0.03em] text-[#111111]">{row.label}</p>
                              {row.kind === "pending" ? <p className="text-xs text-[#5F6C86]">{row.note}</p> : null}
                            </div>
                            <UploadStatusMark status={row.status} />
                            <p className="text-sm text-[#49536B]">{new Date(row.createdAt).toLocaleString()}</p>
                            <div className="flex items-center gap-2">
                              {row.action === "retry" && row.kind === "application" ? (
                                <Button disabled={busyRetryId === row.id} onClick={() => handleRetry(row.id)}>
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
                <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Session log</p>
                  <p className="mt-3 text-sm leading-6 text-[#49536B]">Actions taken during this session appear here in order.</p>
                  <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0]">
                    <div className="border-b border-[#727D97] px-4 py-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">Current session</p>
                    </div>
                    <div className="divide-y divide-[#727D97]/45">
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
                                <p className="text-sm font-semibold text-[#111111]">{entry.subject}</p>
                              </div>
                              <p className="mt-2 text-sm leading-6 text-[#49536B]">{entry.detail}</p>
                            </div>
                            <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F6C86]">
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
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-[#CBD2DE] px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
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
