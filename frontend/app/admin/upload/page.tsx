"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, FileUp, Sparkles, Trash2 } from "lucide-react";
import { fetchApplications, removeQueuedApplication, retryApplication, uploadApplication } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/shadcn/badge";
import { Button as ShadButton } from "@/components/shadcn/button";
import { Separator } from "@/components/shadcn/separator";

export default function AdminUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyRetryId, setBusyRetryId] = useState<string | null>(null);
  const [busyRemoveId, setBusyRemoveId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

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

  usePolling(loadUploads, 5000, !loading);

  async function handleUpload() {
    if (!file) {
      return;
    }

    setMessage(null);
    setError(null);
    setUploading(true);
    try {
      const response = await uploadApplication(file);
      setMessage(`Upload completed with status ${response.status}.`);
      setFile(null);
      await loadUploads();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
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

  const metrics = useMemo(
    () => ({
      total: items.length,
      processing: items.filter((item) => item.status === "PROCESSING").length,
      failed: items.filter((item) => item.status === "FAILED").length,
    }),
    [items],
  );

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="hero-panel p-6">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Intake queue</p>
              <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Upload Queue</h1>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                Ingest new PDFs and keep an eye on inline-processing failures without sinking into a long list of large cards.
              </p>
            </div>
            <div className="metric-strip">
              <MetricCard label="Queue items" value={String(metrics.total)} />
              <MetricCard label="Processing" value={String(metrics.processing)} />
              <MetricCard label="Failed" value={String(metrics.failed)} />
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[24rem_1fr] xl:items-start">
          <div className="self-start">
            <Card
              title="Upload PDF"
              description="Current backend upload still processes inline, so the returned state may already be READY or FAILED."
            >
              <div className="flex flex-col gap-4">
                <input
                  id="application-pdf"
                  className="sr-only"
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />

                <div className="upload-dropzone">
                  <span className="upload-glyph" aria-hidden="true">
                    <FileUp className="size-5" />
                  </span>
                  <div className="flex flex-col gap-1">
                    <p className="text-sm font-semibold text-[color:var(--ink)]">Drop in the next interview packet</p>
                    <p className="text-xs leading-6 text-[color:var(--muted)]">
                      PDFs only. The queue updates inline once the backend returns READY, PROCESSING, or FAILED.
                    </p>
                  </div>
                  <Badge variant={file ? "secondary" : "outline"}>{file ? file.name : "No PDF selected yet"}</Badge>
                  <label
                    htmlFor="application-pdf"
                    className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-[color:var(--surface-border)] bg-white px-3 py-2 text-sm font-medium text-[color:var(--brand-deep)] shadow-sm transition hover:border-blue-200 hover:bg-blue-50/70"
                  >
                    Choose PDF
                  </label>
                </div>

                <Separator />

                <div className="flex items-center justify-between rounded-2xl border border-white/70 bg-white/70 px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-[color:var(--muted)]">
                    <Sparkles className="size-4 text-[color:var(--accent)]" />
                    <span>{file ? "Ready to send into intake" : "Select a file to unlock upload"}</span>
                  </div>
                  {file ? <span className="text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--accent)]">PDF ready</span> : null}
                </div>

                <ShadButton className="w-full justify-center" disabled={uploading || !file} onClick={() => void handleUpload()}>
                  <ArrowUpRight data-icon="inline-end" />
                  {uploading ? "Uploading..." : "Send to Queue"}
                </ShadButton>
              </div>
            </Card>
          </div>

          <div className="space-y-4">
            {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

            {loading ? (
              <Loader label="Loading upload queue..." />
            ) : items.length === 0 ? (
              <EmptyState title="No uploads in queue." description="UPLOADED, PROCESSING, and FAILED items appear here." />
            ) : (
              <div className="data-table">
                <div className="data-table-header md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                  <span>Application</span>
                  <span>Status</span>
                  <span>Created</span>
                  <span>Action</span>
                </div>
                {items.map((item) => (
                  <div key={item.id} className="data-table-row md:grid-cols-[1.2fr_0.8fr_0.9fr_0.8fr]">
                    <p className="display-font text-base font-semibold text-[color:var(--ink)]">{item.id}</p>
                    <StatusBadge status={item.status} />
                    <p className="text-sm text-[color:var(--muted)]">{new Date(item.created_at).toLocaleString()}</p>
                    <div className="flex items-center gap-2">
                      {item.status === "FAILED" ? (
                        <Button disabled={busyRetryId === item.id} onClick={() => void handleRetry(item.id)}>
                          {busyRetryId === item.id ? "Retrying..." : "Retry"}
                        </Button>
                      ) : (
                        <span className="text-sm text-[color:var(--muted)]">Waiting</span>
                      )}
                      {(item.status === "UPLOADED" || item.status === "FAILED") ? (
                        <Button
                          variant="secondary"
                          disabled={busyRemoveId === item.id}
                          onClick={() => void handleRemove(item.id)}
                        >
                          <Trash2 className="size-4" />
                          {busyRemoveId === item.id ? "Removing..." : "Remove"}
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
