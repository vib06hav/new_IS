import { MessageSquareText, Search } from "lucide-react";

const SOURCES = ["Page 4 · Focus Areas", "Page 5 · Questions", "Page 2 · Activities"];

export function LandingReportChatSlice() {
  return (
    <div className="space-y-4">
      <section className="rounded-[1.6rem] border border-slate-200 bg-white p-4 shadow-[0_18px_36px_rgba(15,23,42,0.12)]">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Report Assistant</p>
            <h3 className="text-xl font-semibold tracking-tight text-slate-900">Ask This Report</h3>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
            <MessageSquareText className="size-3.5" />
            Grounded answers
          </span>
        </div>
      </section>

      <section className="rounded-[1.4rem] border border-slate-200 bg-white shadow-[0_18px_36px_rgba(15,23,42,0.1)]">
        <div className="border-b border-slate-200 px-4 py-4">
          <div className="rounded-[1rem] border border-slate-200 bg-white/92 px-4 py-3 text-sm text-slate-900 shadow-[0_8px_18px_rgba(15,23,42,0.04)]">
            What should I clarify before the interview?
          </div>

          <div className="mt-3 flex items-center justify-between gap-3">
            <button
              className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-white shadow-[0_14px_28px_rgba(37,99,235,0.24)]"
              type="button"
            >
              <Search className="size-3.5" />
              Search report
            </button>
            <p className="text-[11px] leading-5 text-slate-500">
              Ask about academics, writing, focus areas, or interview questions.
            </p>
          </div>
        </div>

        <div className="bg-white/72 px-4 py-4">
          <div className="rounded-[1rem] border border-slate-200 bg-[linear-gradient(135deg,rgba(239,246,255,0.92),rgba(255,255,255,0.92))] px-4 py-3">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Answer</p>
            <p className="mt-2 text-sm leading-6 text-slate-900">
              The report suggests clarifying whether the candidate&apos;s interest in technology has translated into hands-on building. It also points to question areas around practical execution and real project examples.
            </p>

            <div className="mt-4 border-t border-slate-200/80 pt-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">Grounded in</span>
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
          </div>
        </div>
      </section>
    </div>
  );
}
