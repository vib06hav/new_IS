"use client";

import { FormEvent, useState } from "react";
import { ArrowRight, Compass, MessageSquareText, Sparkles, X } from "lucide-react";
import { askReportChat } from "@/lib/api";
import { getReportChatSourceLabel } from "@/lib/reportChat";
import type {
  ReportChatCurrentPage,
  ReportChatResponse,
  ReportChatSource,
  ReportChatSurfaceType,
  ReportChatWorkflowStage,
} from "@/lib/types";
import { Button } from "@/components/ui/Button";

export function ReportChatWidget({
  applicationId,
  surfaceType,
  currentPage,
  workflowStage,
  availableActions,
  onNavigateResult,
}: {
  applicationId: string;
  surfaceType: ReportChatSurfaceType;
  currentPage?: ReportChatCurrentPage | null;
  workflowStage?: ReportChatWorkflowStage | null;
  availableActions: string[];
  onNavigateResult?: ((result: ReportChatSource) => void | Promise<void>) | null;
}) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ReportChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitQuestion(nextQuestion: string) {
    const trimmed = nextQuestion.trim();
    if (!trimmed) {
      setError("Enter a question for the copilot.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setQuestion(trimmed);
    try {
      const response = await askReportChat(applicationId, {
        question: trimmed,
        surface_type: surfaceType,
        current_page: currentPage ?? undefined,
        workflow_stage: workflowStage ?? undefined,
        available_actions: availableActions,
      });
      setAnswer(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to reach the copilot right now.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuestion(question);
  }

  function handleClear() {
    setQuestion("");
    setAnswer(null);
    setError(null);
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-3">
      {open ? (
        <section className="w-[min(28rem,calc(100vw-1.5rem))] overflow-hidden rounded-[1.6rem] border border-slate-200 bg-[linear-gradient(155deg,rgba(255,255,255,0.98),rgba(241,245,249,0.98),rgba(255,255,255,0.96))] shadow-[0_30px_80px_rgba(15,23,42,0.24)] backdrop-blur">
          <div className="border-b border-slate-200 px-4 py-2">
            <div className="flex items-start justify-between gap-3">
              <span className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700">
                <Sparkles className="size-3.5" />
                Report Copilot
              </span>
              <button
                aria-label="Close report copilot"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white/90 text-slate-700 transition hover:bg-slate-100"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>

          <form className="space-y-2 px-4 py-3" onSubmit={(event) => void handleSubmit(event)}>
            <label className="block">
              <span className="sr-only">Ask the report copilot</span>
              <textarea
                aria-label="Ask the report copilot"
                className="min-h-20 w-full rounded-[1rem] border border-slate-200 bg-white/92 px-4 py-3 text-sm leading-6 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200/80"
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about the report, this page, or the next step in the workflow"
                value={question}
              />
            </label>

            <div className="flex flex-wrap items-center justify-between gap-2">
              <Button disabled={submitting} size="sm" type="submit">
                <MessageSquareText className="size-4" />
                {submitting ? "Thinking..." : "Ask copilot"}
              </Button>
              <Button onClick={handleClear} size="sm" type="button" variant="secondary">
                Clear
              </Button>
            </div>
          </form>

          <div className="space-y-3 border-t border-slate-200 bg-white/75 px-4 py-3">
            {error ? (
              <p className="rounded-[1rem] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
            ) : null}

            {!error && answer ? (
              <div className="rounded-[1rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.92),rgba(255,255,255,0.96))] px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Answer</span>
                  <span className="inline-flex rounded-full border border-slate-200 bg-white/90 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-600">
                    {formatResponseKind(answer.response_kind)}
                  </span>
                  {answer.response_state === "degraded" ? (
                    <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-amber-700">
                      Grounded
                    </span>
                  ) : null}
                </div>

                <div className="mt-3 max-h-64 overflow-y-auto pr-1">
                  <p className="text-sm leading-7 text-slate-900">{answer.answer_summary}</p>
                </div>

                {answer.sources.length ? (
                  <div className="mt-3 border-t border-slate-200/80 pt-3">
                    <div className="flex flex-wrap items-center gap-2">
                      {answer.sources.map((source, index) =>
                        onNavigateResult ? (
                          <button
                            key={`${source.anchor_id}-${source.section_key}-${index}`}
                            className="inline-flex items-center rounded-full border border-slate-200 bg-white/88 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-blue-200 hover:text-blue-700"
                            onClick={() => void onNavigateResult(source)}
                            type="button"
                          >
                            {getReportChatSourceLabel(source)}
                          </button>
                        ) : (
                          <span
                            key={`${source.anchor_id}-${source.section_key}-${index}`}
                            className="inline-flex items-center rounded-full border border-slate-200 bg-white/88 px-3 py-1.5 text-xs font-semibold text-slate-700"
                          >
                            {getReportChatSourceLabel(source)}
                          </span>
                        ),
                      )}
                    </div>
                  </div>
                ) : null}

                {answer.suggested_followups.length ? (
                  <div className="mt-3 border-t border-slate-200/80 pt-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Follow-ups</span>
                      {answer.suggested_followups.map((followup) => (
                        <button
                          key={followup}
                          className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 transition hover:bg-blue-100"
                          disabled={submitting}
                          onClick={() => void submitQuestion(followup)}
                          type="button"
                        >
                          {followup}
                          <ArrowRight className="size-3.5" />
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}

            {!error && !answer ? (
              <div className="rounded-[1rem] border border-dashed border-slate-200 bg-white/80 px-4 py-4 text-sm leading-6 text-slate-600">
                The copilot can explain the report, describe this page, and answer your questions.
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      <button
        aria-label="Open report copilot"
        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white shadow-[0_16px_36px_rgba(37,99,235,0.28)] transition hover:bg-blue-800"
        onClick={() => setOpen(true)}
        type="button"
      >
        <Compass className="size-4" />
        Open copilot
      </button>
    </div>
  );
}

function formatResponseKind(responseKind: ReportChatResponse["response_kind"]) {
  if (responseKind === "workflow") return "Workflow help";
  if (responseKind === "action") return "Next step";
  if (responseKind === "mixed") return "Mixed";
  if (responseKind === "degraded") return "Fallback";
  return "Report insight";
}
