"use client";

import { FormEvent, useState } from "react";
import { MessageSquareText, Search, X } from "lucide-react";
import { askReportChat } from "@/lib/api";
import { getReportChatSourceLabel } from "@/lib/reportChat";
import type { ReportChatResponse, ReportChatSource } from "@/lib/types";
import { Button } from "@/components/ui/Button";

export function ReportChatWidget({
  applicationId,
  onNavigateResult,
}: {
  applicationId: string;
  onNavigateResult: (result: ReportChatSource) => void | Promise<void>;
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

  function handleClear() {
    setQuestion("");
    setAnswer(null);
    setError(null);
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      {open ? (
        <section className="w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.98),rgba(248,250,252,0.96),rgba(255,255,255,0.92))] shadow-[0_24px_60px_rgba(15,23,42,0.22)] backdrop-blur">
          <div className="flex items-start justify-between gap-3 border-b border-slate-200 px-4 py-4">
            <div className="space-y-1">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Ask This Report</p>
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

          <form className="space-y-3 px-4 py-4" onSubmit={(event) => void handleSubmit(event)}>
            <label className="block">
              <span className="sr-only">Ask a question about this report</span>
              <input
                aria-label="Ask a question about this report"
                className="w-full rounded-[1rem] border border-slate-200 bg-white/92 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200/80"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about a report area"
                value={question}
              />
            </label>

            <div className="flex items-center justify-between gap-2">
              <Button disabled={submitting} size="sm" type="submit">
                <Search className="size-4" />
                {submitting ? "Searching..." : "Search report"}
              </Button>
              <Button onClick={handleClear} size="sm" type="button" variant="secondary">
                Clear
              </Button>
            </div>
          </form>

          <div className="max-h-[22rem] overflow-y-auto border-t border-slate-200 bg-white/72 px-4 py-4">
            {error ? (
              <p className="rounded-[1rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
            ) : null}

            {!error && !answer ? (
              <div className="rounded-[1rem] border border-dashed border-slate-200 bg-white/75 px-4 py-5 text-sm leading-6 text-slate-600">
                Ask about academics, tests, activities, writing, focus areas, or interview questions.
              </div>
            ) : null}

            {!error && answer ? (
              <div className="rounded-[1rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.92),rgba(255,255,255,0.92))] px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Answer</p>
                <p className="mt-2 text-sm leading-6 text-slate-900">{answer.answer_summary}</p>

                {answer.response_kind === "scope_redirect" ? (
                  <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Area summaries only</p>
                ) : null}

                {answer.response_state === "degraded" ? (
                  <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-amber-700">High-level fallback</p>
                ) : null}

                {answer.sources.length ? (
                  <div className="mt-4 border-t border-slate-200/80 pt-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Grounded in</span>
                      {answer.sources.map((source, index) => (
                        <button
                          key={`${source.anchor_id}-${source.section_key}-${index}`}
                          className="inline-flex items-center rounded-full border border-slate-200 bg-white/88 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-blue-200 hover:text-blue-700"
                          onClick={() => void onNavigateResult(source)}
                          type="button"
                        >
                          {getReportChatSourceLabel(source)}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      <button
        aria-label="Open report assistant"
        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white shadow-[0_16px_36px_rgba(37,99,235,0.28)] transition hover:bg-blue-800"
        onClick={() => setOpen(true)}
        type="button"
      >
        <MessageSquareText className="size-4" />
        Ask this report
      </button>
    </div>
  );
}
