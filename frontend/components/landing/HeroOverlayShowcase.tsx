const themes = [
  { title: "Problem Solving", progress: "2/4", active: true },
  { title: "Motivation", progress: "1/3" },
  { title: "Communication", progress: "0/3" },
];

const grounding = [
  "Low-cost water monitoring prototype",
  "Limited access to lab equipment",
  "Redesigned after the first sensing model failed",
];

const flowSteps = [
  { label: "Why this program?", state: "done", tone: "Satisfactory" },
  { label: "Adapting under constraint", state: "current", tone: "Current" },
  { label: "Explaining technical work", state: "next", tone: "Next" },
];

export function HeroOverlayShowcase() {
  return (
    <div className="relative max-w-[48rem] overflow-hidden rounded-[2rem] border border-slate-200/80 bg-[linear-gradient(155deg,rgba(255,255,255,0.97),rgba(239,246,255,0.95),rgba(248,250,252,0.92))] p-3 shadow-[0_30px_80px_rgba(15,23,42,0.18)]">
      <div className="pointer-events-none absolute inset-x-10 top-0 h-px bg-[linear-gradient(90deg,rgba(37,99,235,0.4),rgba(59,130,246,0.1),transparent)]" />

      <div className="rounded-[1.65rem] border border-white/80 bg-white/88 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)] backdrop-blur">
        <div className="rounded-[1.4rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.86),rgba(255,255,255,0.94))] shadow-[0_20px_48px_rgba(15,23,42,0.1)]">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200/90 px-4 py-3">
            <div className="space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Aarav Mehta</p>
              <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
                <span>Mechanical Engineering</span>
                <span className="h-1 w-1 rounded-full bg-slate-300" aria-hidden="true" />
                <span>South Asia Track</span>
              </div>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
              Interview in progress
            </span>
          </div>

          <div className="grid items-start gap-3 p-3 xl:grid-cols-[9.25rem_minmax(0,1.45fr)_10.25rem]">
            <aside className="rounded-[1.25rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.92),rgba(255,255,255,0.96))] p-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Focus Areas</p>
              <div className="mt-3 space-y-2.5">
                {themes.map((theme) => (
                  <div
                    key={theme.title}
                    className={`rounded-[1rem] border px-3 py-3 ${
                      theme.active
                        ? "border-blue-200 bg-[linear-gradient(145deg,rgba(219,234,254,0.88),rgba(255,255,255,0.96))] shadow-[0_14px_28px_rgba(37,99,235,0.12)]"
                        : "border-slate-200 bg-white/88"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold leading-5 text-slate-900">{theme.title}</p>
                        <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                          {theme.active ? "Current theme" : "Queued"}
                        </p>
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${
                          theme.active ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {theme.progress}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </aside>

            <section className="rounded-[1.35rem] border border-slate-200 bg-white p-4 shadow-[0_18px_40px_rgba(15,23,42,0.08)]">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-700">Current focus</p>
                  <h3 className="mt-1 text-lg font-semibold tracking-[-0.03em] text-slate-950">
                    Problem Solving under constraint
                  </h3>
                </div>
                <span className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
                  Guided live flow
                </span>
              </div>

              <div className="mt-4 rounded-[1.2rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.95),rgba(255,255,255,0.98))] p-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Current question</p>
                <p className="mt-3 text-base font-semibold leading-7 tracking-[-0.03em] text-slate-950">
                  Tell me about a project where the original plan failed and you had to change course.
                </p>
              </div>

              <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.92fr)]">
                <div className="space-y-3.5">
                  <div className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 p-3.5">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                      Grounded in applicant material
                    </p>
                    <ul className="mt-3 space-y-2.5 text-sm leading-5 text-slate-700">
                      {grounding.map((item) => (
                        <li key={item} className="flex items-start gap-2">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-600" aria-hidden="true" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-[1.1rem] border border-slate-200 bg-white p-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Live note</p>
                    <div className="mt-3 rounded-[0.95rem] border border-blue-100 bg-blue-50/60 px-3 py-3 text-sm leading-6 text-slate-800">
                      Clear explanation of the redesign. Strong tradeoff thinking, but still light on how the equipment limits shaped the final choice.
                    </div>
                  </div>
                </div>

                <div className="space-y-3.5">
                  <div className="rounded-[1.1rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.94))] p-3.5">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Live judgment</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <StatusChip label="Satisfactory" tone="emerald" active />
                      <StatusChip label="Mixed" tone="amber" />
                      <StatusChip label="Unsatisfactory" tone="rose" />
                    </div>
                  </div>

                  <div className="rounded-[1.1rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.94))] p-3.5">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Flow controls</p>
                    <div className="mt-3 space-y-2.5">
                      <button
                        type="button"
                        className="inline-flex w-full items-center justify-center rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                      >
                        Add follow-up
                      </button>
                      <button
                        type="button"
                        className="inline-flex w-full items-center justify-center rounded-full bg-blue-700 px-3 py-2 text-sm font-semibold text-white shadow-[0_14px_28px_rgba(37,99,235,0.24)] transition hover:bg-blue-800"
                      >
                        Next question
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <aside className="rounded-[1.25rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.9),rgba(255,255,255,0.98))] p-3">
              <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Interview Flow</p>
              <div className="mt-3 space-y-2.5">
                {flowSteps.map((step) => (
                  <div
                    key={step.label}
                    className={`rounded-[1rem] border px-3 py-3 ${
                      step.state === "current"
                        ? "border-blue-200 bg-blue-50/78 shadow-[0_14px_28px_rgba(37,99,235,0.12)]"
                        : step.state === "done"
                          ? "border-emerald-200 bg-emerald-50/82"
                          : "border-slate-200 bg-white/90"
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <span
                        className={`mt-0.5 inline-flex size-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                          step.state === "current"
                            ? "bg-blue-700 text-white"
                            : step.state === "done"
                              ? "bg-emerald-600 text-white"
                              : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {step.state === "done" ? "OK" : step.state === "current" ? "->" : "..."}
                      </span>
                      <div>
                        <p className="text-sm font-semibold leading-5 text-slate-900">{step.label}</p>
                        <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                          {step.tone}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusChip({
  label,
  tone,
  active = false,
}: {
  label: string;
  tone: "emerald" | "amber" | "rose";
  active?: boolean;
}) {
  const tones = {
    emerald: active
      ? "border-emerald-300 bg-emerald-100 text-emerald-900"
      : "border-emerald-100 bg-white text-emerald-800",
    amber: active ? "border-amber-300 bg-amber-100 text-amber-900" : "border-amber-100 bg-white text-amber-800",
    rose: active ? "border-rose-300 bg-rose-100 text-rose-900" : "border-rose-100 bg-white text-rose-800",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.16em] ${tones[tone]}`}
    >
      {label}
    </span>
  );
}
