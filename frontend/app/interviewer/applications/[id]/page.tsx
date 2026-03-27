"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchApplicationDetail, generateDraft, publishDraft } from "@/lib/api";
import type { ApplicationDetailInterviewer } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { JsonSection } from "@/components/JsonSection";
import { ReviewPackageSection } from "@/components/ReviewPackageSection";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";

export default function InterviewerApplicationPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<ApplicationDetailInterviewer | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<"generate" | "publish" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadDetail() {
    try {
      const detail = await fetchApplicationDetail<ApplicationDetailInterviewer>(params.id);
      setItem(detail);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load application.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [params.id]);

  usePolling(loadDetail, 5000, !loading && !busyAction);

  async function handleGenerate() {
    setMessage(null);
    setError(null);
    setBusyAction("generate");
    try {
      await generateDraft(params.id);
      setMessage(item?.status === "DRAFT" ? "Draft regenerated." : "Draft generated.");
      await loadDetail();
    } catch (generationError) {
      setError(generationError instanceof Error ? generationError.message : "Generation failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handlePublish() {
    setMessage(null);
    setError(null);
    setBusyAction("publish");
    try {
      await publishDraft(params.id);
      setMessage("Draft published.");
      await loadDetail();
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : "Publish failed.");
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return (
      <InterviewerShell>
        <Loader label="Loading application..." />
      </InterviewerShell>
    );
  }

  if (error && !item) {
    return (
      <InterviewerShell>
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      </InterviewerShell>
    );
  }

  if (!item) {
    return (
      <InterviewerShell>
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">Application not found.</p>
      </InterviewerShell>
    );
  }

  const canGenerate = item.status === "ASSIGNED" || item.status === "DRAFT";
  const canPublish = item.status === "DRAFT";

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <Card title={item.id} description={new Date(item.created_at).toLocaleString()}>
          <div className="space-y-2 text-sm text-muted">
            <StatusBadge status={item.status} />
            <p>{item.assigned_interviewer ? `Assigned to ${item.assigned_interviewer.name}` : "Not assigned"}</p>
          </div>
        </Card>

        {message ? <p className="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {item.review_package ? (
          <ReviewPackageSection applicationId={item.id} reviewPackage={item.review_package} roleLabel="interviewer" />
        ) : null}

        {item.latest_draft ? (
          <JsonSection
            title="Latest Draft"
            description={`Version ${item.latest_draft.version}`}
            data={item.latest_draft.content}
          />
        ) : null}

        {canGenerate ? (
          <Card title="Draft Actions" description="Generation affects Pages 4-5 only.">
            <div className="flex flex-col gap-3 md:flex-row">
              <Button disabled={busyAction !== null} onClick={() => void handleGenerate()}>
                {busyAction === "generate"
                  ? item.status === "DRAFT"
                    ? "Regenerating..."
                    : "Generating..."
                  : item.status === "DRAFT"
                    ? "Regenerate"
                    : "Generate"}
              </Button>
              <Button
                disabled={busyAction !== null || !canPublish || !item.latest_draft}
                variant="secondary"
                onClick={() => void handlePublish()}
              >
                {busyAction === "publish" ? "Publishing..." : "Publish"}
              </Button>
            </div>
          </Card>
        ) : null}

        {item.status === "PUBLISHED" ? (
          <Card title="Published" description="This report is now read-only.">
            <p className="text-sm text-muted">Pages 4-5 are frozen after publish.</p>
          </Card>
        ) : null}
      </div>
    </InterviewerShell>
  );
}
