import { ArrowRight, MessageSquareText, Sparkles } from "lucide-react";

const SOURCES = ["Page 4 - Focus Areas", "Page 5 - Question Sets", "Page 2 - Activities"];
const FOLLOWUPS = [
  "Summarize the focus area",
  "What should I ask next?",
  "What is still unvalidated?",
];

export function LandingReportChatSlice() {
  return (
    <section className="overflow-hidden rounded-[1.6rem] border border-slate-200 bg-[linear-gradient(155deg,rgba(255,255,255,0.98),rgba(241,245,249,0.98),rgba(255,255,255,0.96))] shadow-[0_30px_80px_rgba(15,23,42,0.18)] backdrop-blur">
      <div className="border-b border-slate-200 px-4 py-2">
        <span className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700">
          <Sparkles className="size-3.5" />
          Interview Copilot
        </span>
      </div>

      <div className="space-y-2 px-4 py-3">
        <div className="min-h-20 rounded-[1rem] border border-slate-200 bg-white/92 px-4 py-3 text-sm leading-6 text-slate-900">
          What should I probe first in this interview?
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2">
          <button
            className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white shadow-[0_16px_36px_rgba(37,99,235,0.28)] transition hover:bg-blue-800"
            type="button"
          >
            <MessageSquareText className="size-4" />
            Ask copilot
          </button>
        </div>
      </div>

      <div className="space-y-3 border-t border-slate-200 bg-white/75 px-4 py-3">
        <div className="rounded-[1rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.92),rgba(255,255,255,0.96))] px-4 py-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Answer</span>
            <span className="inline-flex rounded-full border border-slate-200 bg-white/90 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-600">
              Interview insight
            </span>
          </div>

          <p className="mt-3 text-sm leading-7 text-slate-900">
            Start by testing the gap between stated interest and demonstrated execution. The application review shows
            strong motivation and conceptual clarity, but the interview should probe for hands-on building,
            concrete project ownership, and how the candidate works through technical problems in practice.
          </p>

          <div className="mt-3 border-t border-slate-200/80 pt-3">
            <div className="flex flex-wrap items-center gap-2">
              {SOURCES.map((source) => (
                <span
                  key={source}
                  className="inline-flex items-center rounded-full border border-slate-200 bg-white/88 px-3 py-1.5 text-xs font-semibold text-slate-700"
                >
                  {source}
                </span>
              ))}
            </div>
          </div>

          <div className="mt-3 border-t border-slate-200/80 pt-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Follow-ups</span>
              {FOLLOWUPS.map((followup) => (
                <span
                  key={followup}
                  className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700"
                >
                  {followup}
                  <ArrowRight className="size-3.5" />
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
