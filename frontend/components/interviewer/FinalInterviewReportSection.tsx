"use client";

import { NotebookPen } from "lucide-react";
import type { InterviewWorkspaceQuestion, InterviewWorkspaceSummary, InterviewWorkspaceTheme } from "@/lib/types";
import { FormattedText } from "@/components/ui/FormattedText";

export function FinalInterviewReportSection({
  workspace,
}: {
  workspace: InterviewWorkspaceSummary;
}) {
  const trackedItems = flattenWorkspaceItems(workspace);
  const totals = {
    questions: trackedItems.length,
    satisfactory: trackedItems.filter((item) => item.status === "satisfactory").length,
    mixed: trackedItems.filter((item) => item.status === "mixed").length,
    unsatisfactory: trackedItems.filter((item) => item.status === "unsatisfactory").length,
    unasked: trackedItems.filter((item) => item.status === "unasked").length,
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-2.5 xl:grid-cols-[minmax(0,1fr)_34rem] xl:items-stretch">
        <section className="overflow-hidden rounded-[1.55rem] border border-slate-200 bg-white/80 px-5 py-3.5 shadow-[0_12px_24px_rgba(15,23,42,0.07)] backdrop-blur-sm">
          <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
            <span className="inline-flex items-center gap-2 text-slate-800">
              <NotebookPen className="size-3.5" />
              Post-Interview
            </span>
          </div>
          <div className="mt-2.5 space-y-2">
            <h1 className="max-w-4xl text-[1.9rem] font-black leading-[0.96] tracking-tight text-slate-800 md:text-[2.3rem]">
              Interview Evaluation
            </h1>
            <p className="max-w-3xl text-[0.9rem] leading-6 text-slate-600">
              Submitted interviewer evaluation and question-set outcomes captured after interview completion.
            </p>
          </div>
        </section>

        <aside className="flex h-full flex-col justify-center rounded-[1.5rem] border border-slate-200 bg-white/80 p-3.5 shadow-[0_12px_24px_rgba(15,23,42,0.06)] backdrop-blur-sm">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Status totals</p>
          <div className="mt-3 grid grid-cols-[minmax(5.9rem,1fr)_minmax(5.9rem,1fr)_minmax(5.4rem,0.92fr)_minmax(7.15rem,1.18fr)_minmax(5.4rem,0.92fr)] gap-2">
            <StatusTotal label="Questions" value={totals.questions} />
            <StatusTotal label="Satisfied" value={totals.satisfactory} tone="emerald" />
            <StatusTotal label="Mixed" value={totals.mixed} tone="amber" />
            <StatusTotal label="Unsatisfied" value={totals.unsatisfactory} tone="rose" />
            <StatusTotal label="Unasked" value={totals.unasked} />
          </div>
        </aside>
      </div>

      <section className="rounded-[1.3rem] border border-slate-200 bg-white/88 p-4 shadow-[0_14px_28px_rgba(15,23,42,0.08)]">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Overall Evaluation</h2>
        </div>
        <FormattedText
          text={workspace.content.final_summary || "No overall evaluation was recorded."}
          className="mt-2.5 text-sm text-slate-800"
        />
      </section>

      <section className="mt-8">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Question Set Outcomes</h2>
          <p className="text-sm leading-6 text-slate-600">Final interviewer ratings and response notes grouped by focus area.</p>
        </div>

        <div className="mt-3.5 space-y-3">
          {workspace.content.themes.length ? (
            workspace.content.themes.map((theme, index) => (
              <article
                key={theme.id}
                className={`relative pl-7 py-10 ${index !== 0 ? "border-t border-slate-100" : ""}`}
              >
                <div className="absolute left-0 top-10 bottom-6 w-[3px] rounded-full bg-blue-500/10" />
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                    Focus Area {index + 1}
                  </span>
                  <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
                    {theme.source}
                  </span>
                </div>
                <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-900">{theme.title || "Untitled focus area"}</h3>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <DetailBlock label="Question set" value={theme.question_group_title || "Question set"} />
                  <DetailBlock label="Interview focus" value={theme.interview_direction || "No interview focus recorded."} />
                </div>
                <div className="mt-4 space-y-3">
                  {theme.questions.length ? (
                    theme.questions
                      .slice()
                      .sort((left, right) => left.order - right.order)
                      .map((question, questionIndex) => (
                        <div key={question.id} className="rounded-[1rem] border border-slate-200 bg-white p-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                              Question {questionIndex + 1}
                            </span>
                            <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(question.status)}`}>
                              {formatStatus(question.status)}
                            </span>
                          </div>
                          <p className="mt-3 text-base font-semibold text-slate-900">{question.text || "Untitled question"}</p>
                          <FormattedText
                            text={question.note || "No response note recorded."}
                            className="mt-3 text-sm text-slate-700"
                          />
                          {question.follow_ups.length ? (
                            <div className="mt-4 space-y-4">
                              {question.follow_ups
                                .slice()
                                .sort((left, right) => left.order - right.order)
                                .map((followUp, followUpIndex) => (
                                  <div key={followUp.id} className="pt-2">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                        Follow-up {followUpIndex + 1}
                                      </span>
                                      <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(followUp.status)}`}>
                                        {formatStatus(followUp.status)}
                                      </span>
                                    </div>
                                    <p className="mt-2.5 text-sm font-semibold leading-7 text-slate-900">{followUp.text}</p>
                                    <FormattedText
                                      text={followUp.note || "No follow-up response note recorded."}
                                      className="mt-1.5 text-sm text-slate-700"
                                    />
                                  </div>
                                ))}
                            </div>
                          ) : null}
                        </div>
                      ))
                  ) : (
                    <p className="text-sm leading-7 text-slate-600">No questions were recorded under this focus area.</p>
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
  className,
}: {
  label: string;
  value: number;
  tone?: "slate" | "emerald" | "amber" | "rose";
  className?: string;
}) {
  return (
    <div className={`${className ?? ""} flex min-w-0 items-center justify-between gap-2 rounded-[0.95rem] border px-3 py-3 transition-all ${getTotalToneClasses(tone)}`}>
      <span className="whitespace-nowrap text-[9px] font-bold uppercase tracking-[0.13em]">{label}</span>
      <span className="whitespace-nowrap text-[0.85rem] font-semibold">{value}</span>
    </div>
  );
}

function DetailBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[0.95rem] bg-white/65 px-3 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm leading-7 text-slate-900">{value}</p>
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

function flattenWorkspaceItems(workspace: InterviewWorkspaceSummary) {
  return workspace.content.themes.flatMap((theme) =>
    theme.questions.flatMap((question) => [question, ...question.follow_ups]),
  );
}

function getThemeQuestions(theme: InterviewWorkspaceTheme) {
  return theme.questions ?? [];
}

function getQuestionHeadline(question: InterviewWorkspaceQuestion) {
  return question.text?.trim() || "Untitled question";
}
