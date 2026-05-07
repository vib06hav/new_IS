"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Eye, EyeOff, MoreHorizontal } from "lucide-react";
import { Libre_Franklin } from "next/font/google";
import type { ApplicationListItem } from "@/lib/types";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

type InterviewerReportCardProps = {
  item: ApplicationListItem;
  onToggleHidden: () => void;
  isHiddenBusy: boolean;
};

export function InterviewerReportCard({
  item,
  onToggleHidden,
  isHiddenBusy,
}: InterviewerReportCardProps) {
  const [overflowOpen, setOverflowOpen] = useState(false);
  const overflowRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!overflowOpen) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }
      if (overflowRef.current?.contains(target)) {
        return;
      }
      setOverflowOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [overflowOpen]);

  return (
    <article
      className={`${libreFranklin.variable} rounded-[1.8rem] border border-slate-200 bg-white/80 text-slate-900 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_hidden_for_interviewer ? <StatusMark status="HIDDEN" /> : null}
            <StatusMark status={item.status} />
          </div>
          <h4
            className="text-[1.8rem] font-black leading-none tracking-tight text-slate-800"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {item.display_id}
          </h4>
        </div>

        <div className="relative" ref={overflowRef}>
          <button
            className="grid size-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-500 transition-all duration-200 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            onClick={() => setOverflowOpen((current) => !current)}
            type="button"
          >
            <MoreHorizontal className="size-4" />
          </button>
          {overflowOpen ? (
            <div className="absolute right-0 z-20 mt-2 min-w-44 rounded-[1rem] border border-slate-200 bg-white p-2 shadow-[0_18px_44px_rgba(15,23,42,0.12)]">
              <button
                className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50 disabled:opacity-55"
                disabled={isHiddenBusy}
                onClick={() => {
                  setOverflowOpen(false);
                  onToggleHidden();
                }}
                type="button"
              >
                <span>{isHiddenBusy ? "Saving..." : item.is_hidden_for_interviewer ? "Unhide application" : "Hide application"}</span>
                {item.is_hidden_for_interviewer ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <BlacklineMeta label="Last updated" value={formatDateTime(item.last_activity_at)} />

        <div className="flex justify-end">
          <PrimaryLink
            href={`/interviewer/applications/${item.id}`}
            label={item.status === "COMPLETE" ? "View evaluation summary" : "Open"}
          />
        </div>
      </div>
    </article>
  );
}

function BlacklineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-slate-200 bg-white px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function PrimaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link className="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white shadow-sm transition-colors duration-200 hover:bg-blue-800" href={href}>
      {label}
      <ArrowUpRight className="size-3.5" />
    </Link>
  );
}

function StatusMark({ status }: { status: string }) {
  const styles = {
    ASSIGNED: "border-sky-200 bg-sky-100 text-sky-900",
    COMPLETE: "border-emerald-200 bg-emerald-100 text-emerald-900",
    HIDDEN: "border-slate-200 bg-slate-100 text-slate-700",
  };

  return <span className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status as keyof typeof styles] ?? "border-slate-200 bg-slate-100 text-slate-700"}`}>{status}</span>;
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
