"use client";

import type { InterviewWorkspaceSummary } from "@/lib/types";

export function FinalInterviewReportSection({
  workspace,
}: {
  workspace: InterviewWorkspaceSummary;
}) {
  const questions = flattenWorkspaceQuestions(workspace);
  const totals = {
    questions: questions.length,
    satisfactory: questions.filter((question) => question.status === "satisfactory").length,
    mixed: questions.filter((question) => question.status === "mixed").length,
    unsatisfactory: questions.filter((question) => question.status === "unsatisfactory").length,
    unasked: questions.filter((question) => question.status === "unasked").length,
  };

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem] xl:items-stretch">
        <section className="rounded-[1.8rem] border border-amber-200/70 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(255,255,255,0.94))] px-6 py-6 shadow-[0_20px_48px_rgba(180,138,34,0.12)]">
          <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-amber-700">Post-Interview</p>
          <h1 className="mt-3 text-[2rem] font-semibold tracking-[-0.05em] text-slate-950 sm:text-[2.4rem]">
            Final Interview Report
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-700">
            Final interviewer feedback and question outcomes captured after interview completion.
          </p>
        </section>

        <aside className="rounded-[1.8rem] border border-slate-200 bg-white/92 px-5 py-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)]">
          <p className="px-1 text-[9px] font-bold uppercase tracking-widest text-slate-400">Status totals</p>
          <div className="mt-3 space-y-2">
            <StatusTotal label="Questions" value={totals.questions} />
            <div className="grid grid-cols-2 gap-2">
              <StatusTotal label="Satisfied" value={totals.satisfactory} tone="emerald" />
              <StatusTotal label="Mixed" value={totals.mixed} tone="amber" />
              <StatusTotal label="Unsatisfied" value={totals.unsatisfactory} tone="rose" />
              <StatusTotal label="Unasked" value={totals.unasked} />
            </div>
          </div>
        </aside>
      </div>

      <section className="rounded-[1.5rem] border border-slate-200 bg-white/88 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)]">
        <div className="space-y-2">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Summary</p>
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Interview Summary</h2>
        </div>
        <p className="mt-4 text-sm leading-7 text-slate-800">
          {workspace.content.final_summary || "No final summary was recorded."}
        </p>
      </section>

      <section className="rounded-[1.5rem] border border-slate-200 bg-white/88 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)]">
        <div className="space-y-2">
          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Outcomes</p>
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Question Outcomes</h2>
          <p className="text-sm leading-6 text-slate-600">Final interviewer ratings and notes grouped by theme.</p>
        </div>

        <div className="mt-5 space-y-4">
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
                          {question.follow_ups.length ? (
                            <div className="mt-4 space-y-2 rounded-[0.95rem] border border-slate-200 bg-white/80 p-3">
                              <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Follow-ups</p>
                              {question.follow_ups
                                .slice()
                                .sort((left, right) => left.order - right.order)
                                .map((followUp, followUpIndex) => (
                                  <div key={followUp.id} className="rounded-[0.9rem] border border-slate-200 bg-slate-50/80 p-3">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                        Follow-up {followUpIndex + 1}
                                      </span>
                                      <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(followUp.status)}`}>
                                        {formatStatus(followUp.status)}
                                      </span>
                                    </div>
                                    <p className="mt-3 text-sm leading-7 text-slate-900">{followUp.text}</p>
                                    <p className="mt-2 text-sm leading-7 text-slate-700">
                                      {followUp.note || "No follow-up note recorded."}
                                    </p>
                                  </div>
                                ))}
                            </div>
                          ) : null}
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
      </section>
    </div>
  );
}

function StatusTotal({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: number;
  tone?: "slate" | "emerald" | "amber" | "rose";
}) {
  return (
    <div className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2 transition-all ${getTotalToneClasses(tone)}`}>
      <span className="text-[9px] font-bold uppercase tracking-widest">{label}</span>
      <span className="text-xs font-semibold">{value}</span>
    </div>
  );
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

function getTotalToneClasses(tone: "slate" | "emerald" | "amber" | "rose") {
  if (tone === "emerald") return "border-emerald-100 bg-emerald-50 text-emerald-900";
  if (tone === "amber") return "border-amber-100 bg-amber-50 text-amber-900";
  if (tone === "rose") return "border-rose-100 bg-rose-50 text-rose-900";
  return "border-slate-100 bg-slate-50 text-slate-800";
}

function flattenWorkspaceQuestions(workspace: InterviewWorkspaceSummary) {
  return workspace.content.themes.flatMap((theme) =>
    theme.questions.flatMap((question) => [question, ...question.follow_ups]),
  );
}
