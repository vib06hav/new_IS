"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchApplications, retryApplication, uploadApplication } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { Card } from "@/components/ui/Card";

export default function AdminUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [busyRetryId, setBusyRetryId] = useState<string | null>(null);
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
        <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(230,242,236,0.9))] p-6 shadow-[var(--card-shadow)]">
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

        <div className="grid gap-6 xl:grid-cols-[24rem_1fr]">
          <Card
            title="Upload PDF"
            description="Current backend upload still processes inline, so the returned state may already be READY or FAILED."
          >
            <div className="space-y-3">
              <label className="block text-sm text-[color:var(--muted)]">
                <span className="text-[11px] font-bold uppercase tracking-[0.18em]">PDF file</span>
                <input
                  className="mt-2 block w-full rounded-xl border border-[color:var(--line)] bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)]"
                  type="file"
                  accept="application/pdf"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </label>
              <Button className="w-full" disabled={uploading || !file} onClick={() => void handleUpload()}>
                {uploading ? "Uploading..." : "Upload PDF"}
              </Button>
            </div>
          </Card>

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
                    {item.status === "FAILED" ? (
                      <Button disabled={busyRetryId === item.id} onClick={() => void handleRetry(item.id)}>
                        {busyRetryId === item.id ? "Retrying..." : "Retry"}
                      </Button>
                    ) : (
                      <span className="text-sm text-[color:var(--muted)]">Waiting</span>
                    )}
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
    <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/82 px-4 py-4 shadow-[var(--card-shadow-soft)]">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
