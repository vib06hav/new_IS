const QUESTIONS = [
  {
    status: "Satisfied",
    text: "Tell me about a project where you built something using this technology from scratch.",
    note: "Described a full project build with clear ownership and practical execution.",
  },
  {
    status: "Mixed",
    text: "Walk me through a time you had to debug or fix something that wasn't working-what steps did you take?",
    note: "Good debugging sequence, but the final explanation stayed a little high level.",
  },
  {
    status: "Unasked",
    text: "What's one technical concept you've learned recently, and how have you applied it in practice?",
    note: "Not covered in the live interview.",
  },
];

export function LandingFinalReportSlice() {
  return (
    <div className="space-y-4">
      <section className="rounded-[1.3rem] border border-slate-200 bg-white/88 p-4 shadow-[0_14px_28px_rgba(15,23,42,0.08)]">
        <h4 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Interview Summary</h4>
        <p className="mt-2.5 text-sm leading-7 text-slate-800">
          Strong conceptual interest and clear technical communication. The interview surfaced genuine motivation,
          though practical building experience still needs deeper validation across hands-on examples.
        </p>
      </section>

      <section className="rounded-[1.3rem] border border-slate-200 bg-white/88 p-4 shadow-[0_14px_28px_rgba(15,23,42,0.08)]">
        <div className="space-y-2">
          <h4 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Question Outcomes</h4>
        </div>

        <div className="mt-3.5 space-y-3">
          {QUESTIONS.map((question, index) => (
            <article
              key={question.text}
              className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-3.5 py-3 shadow-[0_8px_18px_rgba(15,23,42,0.04)]"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                  Q{index + 1}
                </span>
                <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(question.status)}`}>
                  {question.status}
                </span>
              </div>
              <p className="mt-3 truncate text-sm font-medium leading-6 text-slate-900" title={question.text}>
                {question.text}
              </p>
              <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-slate-700">{question.note}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function getStatusClasses(status: string) {
  if (status === "Satisfied") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "Mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "Unsatisfied") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-200 bg-slate-100 text-slate-700";
}
