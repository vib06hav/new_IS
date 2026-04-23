"use client";

type SegmentedControlProps<T extends string> = {
  label?: string;
  value: T;
  options: Array<{ value: T; label: string; meta?: string; featured?: boolean }>;
  onChange: (value: T) => void;
  compact?: boolean;
  hideMeta?: boolean;
  className?: string;
  listClassName?: string;
  buttonClassName?: string;
};

export function SegmentedControl<T extends string>({
  label,
  value,
  options,
  onChange,
  compact = false,
  hideMeta = false,
  className,
  listClassName,
  buttonClassName,
}: SegmentedControlProps<T>) {
  return (
    <div className={`space-y-2 ${className ?? ""}`.trim()}>
      {label ? (
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      ) : null}
      <div
        className={`inline-flex max-w-full gap-2 rounded-[1.35rem] border border-[color:var(--line)] bg-[linear-gradient(135deg,rgba(255,255,255,0.82),rgba(239,246,255,0.86))] p-1.5 shadow-[var(--card-shadow-soft)] backdrop-blur-sm ${
          compact ? "flex-nowrap overflow-x-auto" : "flex-wrap"
        } ${listClassName ?? ""}`.trim()}
      >
        {options.map((option) => {
          const active = option.value === value;
          const featured = option.featured === true;

          return (
            <button
              key={option.value}
              className={`shrink-0 rounded-[1rem] text-left transition duration-200 ${
                compact ? "px-3.5 py-2 text-sm" : "px-4 py-2.5"
              } ${
                active
                  ? featured
                    ? "bg-[linear-gradient(135deg,rgba(253,246,178,0.98),rgba(252,231,150,0.98))] text-amber-950 shadow-[0_12px_28px_rgba(180,138,34,0.24)] ring-1 ring-amber-200"
                    : "bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-[color:var(--brand-deep)] shadow-[0_10px_24px_rgba(148,163,184,0.18)] ring-1 ring-blue-100"
                  : featured
                    ? "bg-[linear-gradient(135deg,rgba(255,251,235,0.9),rgba(254,243,199,0.9))] text-amber-900 ring-1 ring-amber-100 hover:bg-[linear-gradient(135deg,rgba(255,247,214,0.96),rgba(253,230,138,0.96))]"
                    : "bg-transparent text-[color:var(--muted)] hover:bg-white/80 hover:text-[color:var(--ink)]"
              } ${buttonClassName ?? ""}`.trim()}
              onClick={() => onChange(option.value)}
              type="button"
            >
              <div className={compact ? "text-xs font-semibold uppercase tracking-[0.14em]" : "text-sm font-semibold"}>
                {option.label}
              </div>
              {!hideMeta && option.meta ? (
                <div className={`text-[11px] ${active ? "text-slate-500" : "text-[color:var(--muted)]"}`}>{option.meta}</div>
              ) : null}
            </button>
          );
        })}
      </div>
    </div>
  );
}
