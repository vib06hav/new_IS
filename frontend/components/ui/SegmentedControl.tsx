"use client";

type SegmentedControlProps<T extends string> = {
  label?: string;
  value: T;
  options: Array<{ value: T; label: string; meta?: string }>;
  onChange: (value: T) => void;
};

export function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
}: SegmentedControlProps<T>) {
  return (
    <div className="space-y-2">
      {label ? (
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      ) : null}
      <div className="inline-flex flex-wrap gap-2 rounded-[1.35rem] border border-[color:var(--line)] bg-[linear-gradient(135deg,rgba(255,255,255,0.82),rgba(239,246,255,0.86))] p-1.5 shadow-[var(--card-shadow-soft)] backdrop-blur-sm">
        {options.map((option) => {
          const active = option.value === value;

          return (
            <button
              key={option.value}
              className={`rounded-[1rem] px-4 py-2.5 text-left transition duration-200 ${
                active
                  ? "bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-[color:var(--brand-deep)] shadow-[0_10px_24px_rgba(148,163,184,0.18)] ring-1 ring-blue-100"
                  : "bg-transparent text-[color:var(--muted)] hover:bg-white/80 hover:text-[color:var(--ink)]"
              }`}
              onClick={() => onChange(option.value)}
              type="button"
            >
              <div className="text-sm font-semibold">{option.label}</div>
              {option.meta ? (
                <div className={`text-[11px] ${active ? "text-slate-500" : "text-[color:var(--muted)]"}`}>{option.meta}</div>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}
