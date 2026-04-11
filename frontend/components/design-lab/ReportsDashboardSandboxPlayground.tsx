"use client";

import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import Link from "next/link";
import {
  ArrowUpRight,
  Eye,
  EyeOff,
  MoreHorizontal,
  PencilLine,
  Stars,
  Trash2,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
} from "@/components/shadcn/select";
import {
  reportsDashboardInterviewers,
  reportsDashboardItems,
  reportsDashboardMetrics,
  reportsDashboardStatuses,
} from "@/lib/design-lab/reportsDashboardMock";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import type { ApplicationListItem } from "@/lib/types";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
  display: "swap",
});

const dashboardCards = reportsDashboardItems;

const sessionLogEntries = [
  {
    id: "log-1",
    action: "Assigned",
    reportId: "PLK-2026-0171",
    detail: "Priya Sharma added as first interviewer",
    time: "Just now",
    accent: "#d9f99d",
    badgeText: "#365314",
  },
  {
    id: "log-2",
    action: "Reassigned",
    reportId: "PLK-2026-0169",
    detail: "Rhea Kapoor -> Aanya Sen",
    time: "2 min ago",
    accent: "#dbeafe",
    badgeText: "#1e3a8a",
  },
  {
    id: "log-3",
    action: "Updated ID",
    reportId: "PLK-2026-0148",
    detail: "Revised reporting identifier to match export record",
    time: "6 min ago",
    accent: "#e0f2fe",
    badgeText: "#0c4a6e",
  },
  {
    id: "log-4",
    action: "Hidden",
    reportId: "PLK-2026-0163",
    detail: "Removed from visible list while review is pending",
    time: "9 min ago",
    accent: "#f1f5f9",
    badgeText: "#475569",
  },
  {
    id: "log-5",
    action: "Completed",
    reportId: "PLK-2026-0157",
    detail: "Pages 4-5 generated and report moved to assignment-ready",
    time: "14 min ago",
    accent: "#fef3c7",
    badgeText: "#92400e",
  },
  {
    id: "log-6",
    action: "Deleted",
    reportId: "PLK-2026-0142",
    detail: "Removed duplicate report from current session",
    time: "21 min ago",
    accent: "#fee2e2",
    badgeText: "#9f1239",
  },
] as const;

export function ReportsDashboardSandboxPlayground() {
  return (
    <div
      className={`${libreFranklin.variable} ${ibmPlexSans.variable} min-h-screen text-slate-900`}
      style={pageCanvasStyle}
    >
      <div className="min-h-screen">
        <LandingStyledReviewDashboard />
      </div>
    </div>
  );
}

function LandingStyledReviewDashboard() {
  const [statusFilter, setStatusFilter] = useState<(typeof reportsDashboardStatuses)[number]>("ALL");
  const filteredCards =
    statusFilter === "ALL"
      ? dashboardCards
      : dashboardCards.filter((item) => {
          if (statusFilter === "HIDDEN") return item.is_hidden;
          return !item.is_hidden && item.status === statusFilter;
        });

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen text-slate-900"
      initial={{ opacity: 0, y: 26 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
    >
      <AdminDesignLabNavbar activeItem="Reports" />

      <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_22rem]">
          <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
              <div className="space-y-4">
                <div className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
                    <span className="inline-flex items-center gap-2 text-slate-800">
                      <Stars className="size-3.5" />
                      Admin review desk
                    </span>
                  </div>
                  <div className="mt-5 space-y-4">
                    <h3
                      className="max-w-4xl text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                      style={{ fontFamily: "var(--font-display)" }}
                    >
                      Generated Reports
                    </h3>
                    <p className="max-w-3xl text-base leading-[1.6] text-slate-600" style={{ fontFamily: "var(--font-body)" }}>
                      Open generated reports, update report IDs, assign or reassign interviewers, manage visibility, and
                      remove reports when necessary.
                    </p>
                  </div>
                </div>

                <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm">
                  <div className="rounded-[1.4rem] border border-slate-200 bg-white/70 p-1.5">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {reportsDashboardStatuses.map((status) => (
                        <button
                          key={status}
                          className={`rounded-[1rem] border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-200 ${
                            statusFilter === status
                              ? getFilterActiveClasses(status)
                              : "border-transparent bg-transparent text-slate-500 hover:border-slate-200 hover:bg-white hover:text-blue-700"
                          }`}
                          onClick={() => setStatusFilter(status)}
                          type="button"
                        >
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm xl:h-full">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Status totals</p>
                <div className="mt-4 space-y-3">
                  <DashboardMetric label="Ready" value={reportsDashboardMetrics.ready} />
                  <DashboardMetric label="Complete" value={reportsDashboardMetrics.complete} />
                  <DashboardMetric label="Assigned" value={reportsDashboardMetrics.assigned} />
                </div>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {filteredCards.map((item) => (
                <DashboardCard key={item.id} item={item} />
              ))}
            </section>
          </div>

          <aside className="grid gap-5 self-start">
            <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Session log</p>
              <p className="mt-3 text-sm leading-6 text-slate-600">Actions taken during this session appear here in order.</p>
              <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white/70">
                <div className="border-b border-slate-200 px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Current session</p>
                </div>
                <div className="divide-y divide-slate-200">
                  {sessionLogEntries.map((entry) => (
                    <div key={entry.id} className="px-4 py-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className="inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em]"
                              style={{ backgroundColor: entry.accent, color: entry.badgeText }}
                            >
                              {entry.action}
                            </span>
                            <p className="text-sm font-semibold text-slate-800">{entry.reportId}</p>
                          </div>
                          <p className="mt-2 text-sm leading-6 text-slate-600">{entry.detail}</p>
                        </div>
                        <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                          {entry.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </motion.div>
  );
}

function DashboardCard({ item }: { item: ApplicationListItem }) {
  const [overflowOpen, setOverflowOpen] = useState(false);
  const [selectedInterviewerId, setSelectedInterviewerId] = useState("");
  const overflowRef = useRef<HTMLDivElement | null>(null);
  const selectedInterviewer = reportsDashboardInterviewers.find((interviewer) => interviewer.id === selectedInterviewerId);
  const assignmentActionLabel = item.assigned_interviewer ? "Reassign interviewer" : "Assign interviewer";

  useEffect(() => {
    if (!overflowOpen) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (overflowRef.current?.contains(target)) return;
      setOverflowOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [overflowOpen]);

  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[1.8rem] border border-slate-200 bg-white/80 text-slate-900 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_hidden ? <StatusMark status="HIDDEN" /> : null}
            <StatusMark status={item.status} />
          </div>
          <h4 className="text-[1.8rem] font-black leading-none tracking-tight text-slate-800" style={{ fontFamily: "var(--font-display)" }}>
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
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50" type="button">
                <span>Edit ID</span>
                <PencilLine className="size-4" />
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50" type="button">
                <span>{item.is_hidden ? "Unhide report" : "Hide report"}</span>
                {item.is_hidden ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-rose-700 transition-colors duration-200 hover:bg-rose-50" type="button">
                <span>Delete report</span>
                <Trash2 className="size-4" />
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <DashboardMeta label="Created" value={formatShortDate(item.created_at)} />
          <div className="sm:pt-0.5">
            <PrimaryLink href={`/admin/applications/${item.id}`} label="Open" />
          </div>
        </div>

        <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Assigned interviewer</p>
          {item.assigned_interviewer ? (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-slate-200 bg-slate-100">
                <AvatarFallback className="bg-slate-800 text-white">
                  {getInitials(item.assigned_interviewer.name)}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-800">{item.assigned_interviewer.name}</p>
                <p className="truncate text-xs text-slate-500">{item.assigned_interviewer.email}</p>
              </div>
            </div>
          ) : (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-slate-200 bg-slate-100">
                <AvatarFallback className="bg-slate-100 text-slate-500">UN</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-800">Unassigned</p>
                <p className="truncate text-xs text-slate-500">No interviewer selected yet</p>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Assignment</p>
          <div className="mt-3 space-y-3">
            <Select
              value={selectedInterviewerId}
              onValueChange={(value) => {
                setSelectedInterviewerId(value ?? "");
                setOverflowOpen(false);
              }}
            >
              <SelectTrigger
                className="h-auto w-full rounded-xl border-slate-200 bg-white px-3 py-3 transition-all duration-200 hover:border-blue-200 hover:bg-blue-50/40"
                onClick={() => setOverflowOpen(false)}
              >
                {selectedInterviewer ? (
                  <div className="flex min-w-0 flex-1 items-center gap-2">
                    <Avatar className="size-8">
                      <AvatarFallback>{getInitials(selectedInterviewer.name)}</AvatarFallback>
                    </Avatar>
                    <span className="min-w-0 flex-1 space-y-0.5">
                      <span className="block truncate font-medium text-slate-800">{selectedInterviewer.name}</span>
                      <span className="block truncate text-xs text-slate-500">{selectedInterviewer.email}</span>
                    </span>
                  </div>
                ) : (
                  <span className="text-sm text-slate-500">
                    {item.assigned_interviewer ? "Choose new interviewer" : "Choose interviewer"}
                  </span>
                )}
              </SelectTrigger>
              <SelectContent className="rounded-2xl border border-slate-200 bg-white shadow-[0_18px_38px_rgba(15,23,42,0.12)]">
                <SelectGroup>
                  <SelectLabel>Available interviewers</SelectLabel>
                  {reportsDashboardInterviewers.map((interviewer) => (
                    <SelectItem key={interviewer.id} value={interviewer.id}>
                      <Avatar className="size-8 self-center">
                        <AvatarFallback>{getInitials(interviewer.name)}</AvatarFallback>
                      </Avatar>
                      <span className="min-w-0 flex-1 flex-col justify-center space-y-0.5">
                        <span className="block truncate font-medium text-slate-800">{interviewer.name}</span>
                        <span className="block truncate text-xs text-slate-500">{interviewer.email}</span>
                      </span>
                      <span className="rounded-full bg-blue-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-blue-800">
                        {interviewer.active_assignment_count} active
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            <button
              className="w-full rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition-all duration-200 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-45"
              disabled={!selectedInterviewerId}
              onClick={() => setOverflowOpen(false)}
              type="button"
            >
              {assignmentActionLabel}
            </button>
          </div>
        </div>
      </div>
    </motion.article>
  );
}

function DashboardMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-slate-200 bg-white px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function DashboardMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-slate-200 bg-white px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function PrimaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      className="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white shadow-sm transition-colors duration-200 hover:bg-blue-800"
      href={href}
    >
      {label}
      <ArrowUpRight className="size-3.5" />
    </Link>
  );
}

function StatusMark({ status }: { status: string }) {
  const styles = {
    READY: "border-lime-200 bg-lime-100 text-lime-900",
    COMPLETE: "border-amber-200 bg-amber-100 text-amber-900",
    ASSIGNED: "border-sky-200 bg-sky-100 text-sky-900",
    HIDDEN: "border-slate-200 bg-slate-100 text-slate-700",
  };

  const className = styles[status as keyof typeof styles] ?? "border-slate-200 bg-slate-100 text-slate-700";

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${className}`}>
      {status}
    </span>
  );
}

function getFilterActiveClasses(status: (typeof reportsDashboardStatuses)[number]) {
  if (status === "ALL") return "border-blue-100 bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-slate-800 shadow-[0_10px_22px_rgba(148,163,184,0.16)]";
  if (status === "READY") return "border-lime-200 bg-lime-100 text-lime-900 shadow-[0_8px_20px_rgba(190,242,100,0.28)]";
  if (status === "COMPLETE") return "border-amber-200 bg-amber-100 text-amber-900 shadow-[0_8px_20px_rgba(253,230,138,0.26)]";
  if (status === "ASSIGNED") return "border-sky-200 bg-sky-100 text-sky-900 shadow-[0_8px_20px_rgba(186,230,253,0.28)]";
  return "border-slate-200 bg-slate-100 text-slate-700 shadow-[0_8px_20px_rgba(226,232,240,0.24)]";
}

function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function formatShortDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

const pageCanvasStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  backgroundImage: "radial-gradient(#e2e8f0 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
  fontFamily: "var(--font-body)",
};
