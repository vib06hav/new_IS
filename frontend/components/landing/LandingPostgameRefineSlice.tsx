import { CheckCircle2, ChevronDown, MinusCircle, Sparkles, XCircle } from "lucide-react";

export function LandingPostgameRefineSlice() {
  return (
    <section className="rounded-[1.6rem] border border-slate-200 bg-white/90 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.1)] backdrop-blur">
      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-700">
            generated
          </span>
          <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-blue-700">
            Theme 1
          </span>
        </div>
        <h3 className="text-xl font-semibold tracking-tight text-slate-900">Technical Depth vs Practice</h3>
      </div>

      <div className="mt-5 space-y-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Questions</p>

        <div className="space-y-3">
          <div className="rounded-[1.2rem] border border-slate-200 bg-slate-50/70 p-4">
            <button className="flex w-full items-start justify-between gap-3 text-left" type="button">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Question 1</p>
                  <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                    generated
                  </span>
                </div>
                <p className="truncate text-sm leading-6 text-slate-900">
                  Tell me about a project where you built something using this technology from scratch.
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <span className="inline-flex rounded-full border border-emerald-200 bg-emerald-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-emerald-900">
                  Satisfied
                </span>
                <ChevronDown className="size-4 text-slate-500" />
              </div>
            </button>
          </div>

          <div className="rounded-[1.2rem] border border-slate-200 bg-slate-50/70 p-4">
            <button className="flex w-full items-start justify-between gap-3 text-left" type="button">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Question 2</p>
                  <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                    generated
                  </span>
                </div>
                <p className="truncate text-sm leading-6 text-slate-900">
                  Walk me through a time you had to debug or fix something that wasn&apos;t working.
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <span className="inline-flex rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                  Unasked
                </span>
                <ChevronDown className="size-4 rotate-180 text-slate-500" />
              </div>
            </button>

            <div className="mt-3 space-y-4">
              <p className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900">
                Walk me through a time you had to debug or fix something that wasn&apos;t working-what steps did you take?
              </p>

              <div className="flex flex-wrap gap-2">
                <StatusOption icon={<span className="inline-block size-3 rounded-full border border-current" />} label="Unasked" />
                <StatusOption active icon={<CheckCircle2 className="size-3.5" />} label="Satisfied" tone="emerald" />
                <StatusOption icon={<MinusCircle className="size-3.5" />} label="Mixed" tone="amber" />
                <StatusOption icon={<XCircle className="size-3.5" />} label="Unsatisfied" tone="rose" />
              </div>

              <TextAreaField
                label="Question note"
                rows={2}
                value="Clear debugging sequence with good ownership of the problem."
              />

              <button
                className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
                type="button"
              >
                <Sparkles className="size-3.5" />
                Refine
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TextAreaField({
  label,
  rows,
  value,
}: {
  label: string;
  rows: number;
  value: string;
}) {
  return (
    <label className="block text-sm text-slate-600">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <textarea
        className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none"
        readOnly
        rows={rows}
        value={value}
      />
    </label>
  );
}

function StatusOption({
  active = false,
  icon,
  label,
  tone = "slate",
}: {
  active?: boolean;
  icon: React.ReactNode;
  label: string;
  tone?: "slate" | "emerald" | "amber" | "rose";
}) {
  const toneClasses =
    tone === "emerald"
      ? "border-emerald-200 bg-emerald-100 text-emerald-900"
      : tone === "amber"
        ? "border-amber-200 bg-amber-100 text-amber-900"
        : tone === "rose"
          ? "border-rose-200 bg-rose-100 text-rose-900"
          : "border-slate-300 bg-slate-100 text-slate-700";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold uppercase tracking-[0.16em] ${
        active ? toneClasses : "border-slate-200 bg-white text-slate-600"
      }`}
    >
      {icon}
      {label}
    </span>
  );
}
