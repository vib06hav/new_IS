"use client";

import { FormEvent, useState } from "react";
import { MessageSquareText, Search, X } from "lucide-react";
import { askReportChat } from "@/lib/api";
import { getReportChatSourceLabel } from "@/lib/reportChat";
import type { ReportChatResponse, ReportChatResult } from "@/lib/types";
import { Button } from "@/components/ui/Button";

export function ReportChatWidget({
  applicationId,
  onNavigateResult,
}: {
  applicationId: string;
  onNavigateResult: (result: ReportChatResult) => void | Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ReportChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Enter a question about the report.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await askReportChat(applicationId, { question: trimmed });
      setAnswer(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to search this report right now.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRetry() {
    if (!question.trim() || submitting) {
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await askReportChat(applicationId, { question: question.trim() });
      setAnswer(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to search this report right now.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleClear() {
    setQuestion("");
    setAnswer(null);
    setError(null);
  }

  return (
    <div className="fixed bottom-6 right-6 z-40 flex flex-col items-end gap-4">
      {open ? (
        <section className="w-[min(30rem,calc(100vw-2rem))] overflow-hidden rounded-[2rem] border border-white/60 bg-[linear-gradient(165deg,rgba(255,255,255,0.98),rgba(240,249,255,0.96))] shadow-[0_32px_64px_-12px_rgba(15,23,42,0.25)] ring-1 ring-slate-900/5 backdrop-blur-lg transition-all">
          <div className="flex items-start justify-between gap-4 border-b border-white/40 bg-white/40 px-6 py-6">
            <div className="space-y-1.5">
              <p className="text-xs font-black uppercase tracking-[0.25em] text-blue-600">Ask This Report</p>
              <p className="text-sm leading-6 text-slate-600 font-medium">Single-turn factual lookup from the current report pages.</p>
            </div>
            <button
              aria-label="Close report assistant"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-700 transition hover:bg-slate-100"
              onClick={() => setOpen(false)}
              type="button"
            >
              <X className="size-4" />
            </button>
          </div>

          <form className="space-y-4 px-6 py-5 bg-white/20" onSubmit={(event) => void handleSubmit(event)}>
            <label className="block">
              <span className="sr-only">Ask a question about this report</span>
              <input
                aria-label="Ask a question about this report"
                className="w-full rounded-2xl border-2 border-slate-200/80 bg-white px-5 py-4 text-base font-medium text-slate-900 outline-none transition-all focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 shadow-sm placeholder:text-slate-400"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about scores, schools, tests or themes..."
                value={question}
              />
            </label>

            <div className="flex items-center justify-between gap-3">
              <Button disabled={submitting} size="lg" type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-base rounded-xl font-bold shadow-md hover:shadow-lg transition-all hover:-translate-y-0.5">
                <Search className="size-5 mr-2" />
                {submitting ? "Searching..." : "Search report"}
              </Button>
              <Button onClick={handleClear} size="lg" type="button" variant="outline" className="rounded-xl font-semibold border-slate-300 hover:bg-slate-100">
                Clear
              </Button>
            </div>
          </form>

          <div className="max-h-[26rem] overflow-y-auto border-t border-slate-200/60 bg-white/40 px-6 py-5">
            {error ? (
              <p className="rounded-[1rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
            ) : null}

            {!error && !answer ? (
              <div className="rounded-[1rem] border border-dashed border-slate-200 bg-white/75 px-4 py-5 text-sm leading-6 text-slate-600">
                Ask a quick factual question like “Any internships?” or “What is the Class 10 physics score?”
              </div>
            ) : null}

            {!error && answer ? (
              <div className="space-y-3">
                <div className="rounded-[1rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.92),rgba(255,255,255,0.92))] px-4 py-3">
                  <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Answer</p>
                  <p className="mt-2 text-sm leading-6 text-slate-900">{answer.answer_summary}</p>
                  {answer.response_state === "degraded" ? (
                    <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-amber-700">
                      Summary recovered, section links unavailable
                    </p>
                  ) : answer.response_state !== "clean" ? (
                    <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-amber-700">
                      Recovered response
                    </p>
                  ) : null}
                </div>

                {answer.not_found ? (
                  <div className="space-y-3 rounded-[1rem] border border-slate-200 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-600">
                    <p>I could not find that in the current report.</p>
                    <Button disabled={submitting} onClick={() => void handleRetry()} size="sm" type="button" variant="secondary">
                      Try again
                    </Button>
                  </div>
                ) : null}

                {!answer.not_found ? (
                  <div className="space-y-3">
                    {answer.results.length === 0 ? (
                      <div className="space-y-3 rounded-[1rem] border border-slate-200 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-600">
                        <p>Section links are unavailable for this answer, but the summary above is still usable.</p>
                        {(answer.response_state === "degraded" || answer.response_state === "retried") ? (
                          <Button disabled={submitting} onClick={() => void handleRetry()} size="sm" type="button" variant="secondary">
                            Try again
                          </Button>
                        ) : null}
                      </div>
                    ) : null}
                    {answer.results.map((result, index) => (
                      <button
                        key={`${result.section_key}-${result.anchor_id}-${index}`}
                        className="block w-full rounded-[1rem] border border-slate-200 bg-white/92 px-4 py-3 text-left shadow-sm transition hover:border-blue-200 hover:bg-blue-50/50"
                        onClick={() => void onNavigateResult(result)}
                        type="button"
                      >
                        <p className="text-sm font-semibold text-slate-900">{result.label}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-700">{result.value}</p>
                        <div className="mt-3 flex items-center justify-between gap-3 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                          <span>{getReportChatSourceLabel(result)}</span>
                          <span>Jump to section</span>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      <button
        aria-label="Open report assistant"
        className="inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 text-base font-bold text-white shadow-[0_16px_36px_rgba(37,99,235,0.35)] transition-all duration-300 hover:scale-105 hover:from-blue-700 hover:to-indigo-700 hover:shadow-[0_20px_45px_rgba(37,99,235,0.45)]"
        onClick={() => setOpen(true)}
        type="button"
      >
        <MessageSquareText className="size-5" />
        Ask this report
      </button>
    </div>
  );
}
