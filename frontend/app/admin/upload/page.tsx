"use client";

import { useEffect, useState } from "react";
import { fetchApplications, retryApplication, uploadApplication } from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

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

  return (
    <AdminShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Upload Queue</h1>
          <p className="text-sm text-muted">Barebones upload and retry surface for the deterministic pipeline.</p>
        </div>

        <Card
          title="Upload PDF"
          description="Current backend upload still processes inline, so the returned state may already be READY or FAILED."
        >
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex-1 text-sm text-muted">
              PDF file
              <input
                className="mt-2 block w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink"
                type="file"
                accept="application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>
            <Button disabled={uploading || !file} onClick={() => void handleUpload()}>
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </Card>

        {message ? <p className="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading upload queue..." />
        ) : items.length === 0 ? (
          <EmptyState title="No uploads in queue." description="UPLOADED, PROCESSING, and FAILED items appear here." />
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <Card key={item.id} title={item.id} description={new Date(item.created_at).toLocaleString()}>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <StatusBadge status={item.status} />
                  {item.status === "FAILED" ? (
                    <Button disabled={busyRetryId === item.id} onClick={() => void handleRetry(item.id)}>
                      {busyRetryId === item.id ? "Retrying..." : "Retry"}
                    </Button>
                  ) : null}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AdminShell>
  );
}
