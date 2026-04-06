"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type HeroMetric = {
  label: string;
  value: string;
};

type HeroPanelProps = {
  eyebrow: string;
  title: string;
  metrics: HeroMetric[];
  action?: ReactNode;
  className?: string;
};

const HERO_METRIC_LAYOUT: Record<number, { desktopWidth: string; desktopColumns: string }> = {
  1: { desktopWidth: "xl:w-[10rem]", desktopColumns: "xl:grid-cols-1" },
  2: { desktopWidth: "xl:w-[20.75rem]", desktopColumns: "xl:grid-cols-2" },
  3: { desktopWidth: "xl:w-[31.5rem]", desktopColumns: "xl:grid-cols-3" },
  4: { desktopWidth: "xl:w-[42.25rem]", desktopColumns: "xl:grid-cols-4" },
};

export function HeroPanel({ eyebrow, title, metrics, action, className }: HeroPanelProps) {
  const layout = HERO_METRIC_LAYOUT[metrics.length] ?? {
    desktopWidth: "xl:w-full",
    desktopColumns: "xl:grid-cols-4",
  };

  return (
    <section className={cn("hero-panel p-6", className)}>
      <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
        <div className="space-y-4">
          <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">{eyebrow}</p>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">{title}</h1>
            {action ? <div className="pt-1">{action}</div> : null}
          </div>
        </div>

        <div className={cn("metric-strip grid-cols-2 xl:max-w-none", layout.desktopWidth, layout.desktopColumns)}>
          {metrics.map((metric) => (
            <div key={metric.label} className="metric-card px-4 py-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{metric.label}</p>
              <p className="text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{metric.value}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
