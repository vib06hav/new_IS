"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Eye, EyeOff, MoreHorizontal } from "lucide-react";
import { Space_Grotesk } from "next/font/google";
import type { ApplicationListItem } from "@/lib/types";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
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
      className={`${spaceGrotesk.variable} rounded-[1.8rem] border border-[#727D97] bg-white text-[#121212] shadow-[0_18px_50px_rgba(114,125,151,0.14)]`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-[#111111]/10 px-5 py-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_hidden_for_interviewer ? <StatusMark status="HIDDEN" /> : null}
            <StatusMark status={item.status} />
          </div>
          <h4
            className="text-[2rem] leading-none tracking-[-0.07em] text-[#111111]"
            style={{ fontFamily: "var(--font-reports-space)" }}
          >
            {item.display_id}
          </h4>
        </div>

        <div className="relative" ref={overflowRef}>
          <button
            className="grid size-10 place-items-center rounded-full border border-[#111111]/10 text-[#474747] transition-all duration-200 hover:border-[#727D97] hover:bg-[#E6E9F0] hover:text-[#111111]"
            onClick={() => setOverflowOpen((current) => !current)}
            type="button"
          >
            <MoreHorizontal className="size-4" />
          </button>
          {overflowOpen ? (
            <div className="absolute right-0 z-20 mt-2 min-w-44 rounded-[1rem] border border-[#727D97] bg-[#F7F7F1] p-2 shadow-[0_18px_44px_rgba(114,125,151,0.2)]">
              <button
                className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors duration-200 hover:bg-[#E6E9F0] disabled:opacity-55"
                disabled={isHiddenBusy}
                onClick={() => {
                  setOverflowOpen(false);
                  onToggleHidden();
                }}
                type="button"
              >
                <span>{isHiddenBusy ? "Saving..." : item.is_hidden_for_interviewer ? "Unhide report" : "Hide report"}</span>
                {item.is_hidden_for_interviewer ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <BlacklineMeta label="Last updated" value={formatDateTime(item.last_activity_at)} />

        <div className="flex justify-end">
          <PrimaryLink href={`/interviewer/applications/${item.id}`} label="Open" />
        </div>
      </div>
    </article>
  );
}

function BlacklineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-[#111111]/10 bg-[#f7f7f1] px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#6a6a62]">{label}</p>
      <p className="mt-2 text-sm font-semibold text-[#111111]">{value}</p>
    </div>
  );
}

function PrimaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link className="inline-flex items-center gap-1 rounded-full bg-[#111111] px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-[#f7f8ec]" href={href}>
      {label}
      <ArrowUpRight className="size-3.5" />
    </Link>
  );
}

function StatusMark({ status }: { status: string }) {
  const styles = {
    ASSIGNED: "bg-[#7CF0FF] text-[#111111]",
    HIDDEN: "bg-[#8A94A6] text-[#111111]",
  };

  return <span className={`inline-flex rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status as keyof typeof styles] ?? "bg-[#E6E9F0] text-[#111111]"}`}>{status}</span>;
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
