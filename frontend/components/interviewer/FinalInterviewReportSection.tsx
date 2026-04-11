"use client";

import { Card } from "@/components/ui/Card";
import type { InterviewWorkspaceSummary } from "@/lib/types";

export function FinalInterviewReportSection({
  workspace,
}: {
  workspace: InterviewWorkspaceSummary;
}) {
  return (
    <div className="space-y-5">
      <Card
        title="Final Interview Report"
        description="Read-only post-interview summary captured from the interviewer workspace."
        eyebrow={null}
      >
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Status" value={workspace.status.toUpperCase()} />
          <Metric label="Updated" value={formatDateTime(workspace.updated_at)} />
          <Metric label="Completed" value={workspace.completed_at ? formatDateTime(workspace.completed_at) : "Unavailable"} />
        </div>
      </Card>

      <Card title="Postgame Summary" description="Top-line summary after interview completion." eyebrow={null}>
        <p className="text-sm leading-7 text-slate-800">
          {workspace.content.final_summary || "No final summary was recorded."}
        </p>
      </Card>

      <Card title="Question Outcomes" description="Final interviewer ratings and notes grouped by theme." eyebrow={null}>
        <div className="space-y-4">
          {workspace.content.themes.length ? (
            workspace.content.themes.map((theme, index) => (
              <article
                key={theme.id}
                className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-4 shadow-[0_12px_24px_rgba(15,23,42,0.06)]"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                    Theme {index + 1}
                  </span>
                  <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
                    {theme.source}
                  </span>
                </div>
                <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-900">{theme.title || "Untitled theme"}</h3>
                <div className="mt-4 space-y-3">
                  {theme.questions.length ? (
                    theme.questions
                      .slice()
                      .sort((left, right) => left.order - right.order)
                      .map((question, questionIndex) => (
                        <div key={question.id} className="rounded-[1rem] border border-slate-200 bg-slate-50/80 p-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                              Q{questionIndex + 1}
                            </span>
                            <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(question.status)}`}>
                              {formatStatus(question.status)}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-7 text-slate-900">{question.text}</p>
                          <p className="mt-2 text-sm leading-7 text-slate-700">
                            {question.note || "No question note recorded."}
                          </p>
                        </div>
                      ))
                  ) : (
                    <p className="text-sm leading-7 text-slate-600">No questions were recorded under this theme.</p>
                  )}
                </div>
              </article>
            ))
          ) : (
            <p className="text-sm leading-7 text-slate-600">No question outcomes were recorded.</p>
          )}
        </div>
      </Card>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.1rem] border border-slate-200 bg-white/80 px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatStatus(status: string) {
  if (status === "satisfactory") return "Satisfied";
  if (status === "mixed") return "Mixed";
  if (status === "unsatisfactory") return "Unsatisfied";
  return "Unasked";
}

function getStatusClasses(status: string) {
  if (status === "satisfactory") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "unsatisfactory") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-200 bg-slate-100 text-slate-700";
}
