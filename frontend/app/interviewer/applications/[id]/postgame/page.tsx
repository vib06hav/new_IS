"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { InterviewerShell } from "@/components/layout/InterviewerShell";
import { Loader } from "@/components/ui/Loader";
import { fetchInterviewWorkspace } from "@/lib/api";
import type { InterviewWorkspaceSummary } from "@/lib/types";
import { InterviewWorkspaceEditor } from "@/components/interviewer/InterviewWorkspaceEditor";
import { ReportChatWidget } from "@/components/ReportChatWidget";

export default function InterviewPostgamePage() {
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
        setError(loadError instanceof Error ? loadError.message : "Unable to open postgame review.");
      } finally {
        setLoading(false);
      }
    }

    void loadWorkspace();
  }, [params.id]);

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Post-Interview Review</p>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Complete Interview Evaluation</h1>
          </div>
          <Link
            className="inline-flex rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
            href={`/interviewer/applications/${params.id}`}
          >
            Back to application review
          </Link>
        </div>

        {loading ? <Loader label="Loading postgame review..." /> : null}
        {!loading && error ? (
          <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p>
        ) : null}
        {!loading && workspace ? (
          <>
            <InterviewWorkspaceEditor applicationId={params.id} initialWorkspace={workspace} mode="postgame" />
            <ReportChatWidget
              applicationId={params.id}
              surfaceType="postgame"
              currentPage="postgame"
              workflowStage="postgame"
              availableActions={[
                "review question outcomes",
                "edit response notes",
                "add custom questions",
                "polish the overall evaluation",
                "submit interview evaluation",
                "save review",
              ]}
            />
          </>
        ) : null}
      </div>
    </InterviewerShell>
  );
}
