"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Loader } from "@/components/ui/Loader";
import { fetchInterviewWorkspace } from "@/lib/api";
import type { InterviewWorkspaceSummary } from "@/lib/types";
import { InterviewOverlayRunner } from "@/components/interviewer/InterviewOverlayRunner";
import { ReportChatWidget } from "@/components/ReportChatWidget";

export default function InterviewOverlayPage() {
  const params = useParams<{ id: string }>();
  const [workspace, setWorkspace] = useState<InterviewWorkspaceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadWorkspace() {
      try {
        const data = await fetchInterviewWorkspace(params.id);
        setWorkspace(data);
        setError(null);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Unable to open interview overlay.");
      } finally {
        setLoading(false);
      }
    }

    void loadWorkspace();
  }, [params.id]);

  return (
    <div>
      {loading ? <Loader label="Loading interview overlay..." /> : null}
      {!loading && error ? (
        <div className="min-h-screen bg-slate-50 p-4">
          <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
        </div>
      ) : null}
      {!loading && workspace ? (
        <>
          <InterviewOverlayRunner applicationId={params.id} initialWorkspace={workspace} />
          <ReportChatWidget
            applicationId={params.id}
            surfaceType="overlay"
            currentPage="overlay"
            workflowStage="live_interview"
            availableActions={[
              "mark question status",
              "add notes",
              "add follow-ups",
              "add custom questions",
              "finish interview",
            ]}
          />
        </>
      ) : null}
    </div>
  );
}
