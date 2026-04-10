"use client";

import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import {
  Cormorant_Garamond,
  IBM_Plex_Sans,
  Space_Grotesk,
} from "next/font/google";
import Image from "next/image";
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

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-reports-cormorant",
});

const blacklineCards = reportsDashboardItems;
const sessionLogEntries = [
  {
    id: "log-1",
    action: "Assigned",
    reportId: "PLK-2026-0171",
    detail: "Priya Sharma added as first interviewer",
    time: "Just now",
    accent: "#D7FF53",
    badgeText: "#111111",
  },
  {
    id: "log-2",
    action: "Reassigned",
    reportId: "PLK-2026-0169",
    detail: "Rhea Kapoor -> Aanya Sen",
    time: "2 min ago",
    accent: "#198FF0",
    badgeText: "#F7F7F1",
  },
  {
    id: "log-3",
    action: "Updated ID",
    reportId: "PLK-2026-0148",
    detail: "Revised reporting identifier to match export record",
    time: "6 min ago",
    accent: "#7CF0FF",
    badgeText: "#111111",
  },
  {
    id: "log-4",
    action: "Hidden",
    reportId: "PLK-2026-0163",
    detail: "Removed from visible list while review is pending",
    time: "9 min ago",
    accent: "#FFB347",
    badgeText: "#111111",
  },
  {
    id: "log-5",
    action: "Published",
    reportId: "PLK-2026-0157",
    detail: "Visibility restored and report returned to live set",
    time: "14 min ago",
    accent: "#FF6B9D",
    badgeText: "#111111",
  },
  {
    id: "log-6",
    action: "Deleted",
    reportId: "PLK-2026-0142",
    detail: "Removed duplicate report from current session",
    time: "21 min ago",
    accent: "#5F6C86",
    badgeText: "#F7F7F1",
  },
] as const;

export function ReportsDashboardSandboxPlayground() {
  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        cormorant.variable,
        "min-h-screen bg-white text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="min-h-screen">
        <BlacklineReviewDashboard />
      </div>
    </div>
  );
}

function BlacklineReviewDashboard() {
  const [statusFilter, setStatusFilter] = useState<(typeof reportsDashboardStatuses)[number]>("ALL");
  const filteredCards =
    statusFilter === "ALL"
      ? blacklineCards
      : blacklineCards.filter((item) => {
          if (statusFilter === "HIDDEN") return item.is_hidden;
          return !item.is_hidden && item.status === statusFilter;
        });

  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen bg-white text-[#111111]"
      initial={{ opacity: 0, y: 26 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
    >
      <AdminDesignLabNavbar activeItem="Reports" />

      <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_22rem]">
          <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
              <div className="space-y-4">
                <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#ffffff_0%,#f8fafc_38%,#f5f8fb_100%)] p-6">
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                    <span className="inline-flex items-center gap-2 text-[#111111]">
                      <Stars className="size-3.5" />
                      Admin review desk
                    </span>
                  </div>
                  <div className="mt-5 space-y-4">
                    <h3
                      className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.85rem]"
                      style={{ fontFamily: "var(--font-reports-space)" }}
                    >
                      Generated Reports
                    </h3>
                    <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                      Open generated reports, update report IDs, assign or reassign interviewers, manage visibility, and
                      remove reports when necessary.
                    </p>
                  </div>
                </div>

                <div className="rounded-[1.9rem] border border-[#727D97] bg-white p-4">
                  <div className="rounded-[1.4rem] border border-[#727D97] bg-white p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]">
                    <div className="flex flex-wrap items-center gap-1.5">
                      {reportsDashboardStatuses.map((status) => (
                        <button
                          key={status}
                          className={`rounded-[1rem] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-200 ${
                            statusFilter === status
                              ? getFilterActiveClasses(status)
                              : "border border-transparent bg-transparent text-[#49536B] hover:border-[#727D97] hover:bg-[#F7F7F1] hover:text-[#111111]"
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

              <div className="rounded-[1.6rem] border border-[#727D97] bg-white p-4 xl:h-full">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Status totals</p>
                <div className="mt-4 space-y-3">
                  <BlacklineMetric label="Ready" value={reportsDashboardMetrics.ready} />
                  <BlacklineMetric label="Assigned" value={reportsDashboardMetrics.assigned} />
                  <BlacklineMetric label="Draft" value={reportsDashboardMetrics.draft} />
                  <BlacklineMetric label="Published" value={reportsDashboardMetrics.published} />
                </div>
              </div>
            </section>

            <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {filteredCards.map((item, index) => (
                <BlacklineSheet key={item.id} item={item} priority={index === 0 ? "sharp" : "standard"} />
              ))}
            </section>
          </div>

          <aside className="grid gap-5 self-start">
            <div className="rounded-[1.9rem] border border-[#727D97] bg-white p-5">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Session log</p>
              <p className="mt-3 text-sm leading-6 text-[#49536B]">Actions taken during this session appear here in order.</p>
              <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-white">
                <div className="border-b border-[#727D97] px-4 py-3">
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">Current session</p>
                </div>
                <div className="divide-y divide-[#727D97]/45">
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
                            <p className="text-sm font-semibold text-[#111111]">{entry.reportId}</p>
                          </div>
                          <p className="mt-2 text-sm leading-6 text-[#49536B]">{entry.detail}</p>
                        </div>
                        <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F6C86]">
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

function BlacklineSheet({
  item,
  priority,
}: {
  item: ApplicationListItem;
  priority: "sharp" | "standard";
}) {
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
      className="rounded-[1.8rem] border border-[#727D97] bg-white text-[#121212] shadow-[0_18px_50px_rgba(114,125,151,0.14)]"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="flex items-start justify-between gap-4 border-b border-[#111111]/10 px-5 py-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_hidden ? <StatusMark status="HIDDEN" tone="blackline" /> : null}
            <StatusMark status={item.status} tone="blackline" />
          </div>
          <h4 className="text-[2rem] leading-none tracking-[-0.07em] text-[#111111]" style={{ fontFamily: "var(--font-reports-space)" }}>
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
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors duration-200 hover:bg-[#E6E9F0]" type="button">
                <span>Edit ID</span>
                <PencilLine className="size-4" />
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors duration-200 hover:bg-[#E6E9F0]" type="button">
                <span>{item.is_hidden ? "Unhide report" : "Hide report"}</span>
                {item.is_hidden ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#AF3030] transition-colors duration-200 hover:bg-[#F4DDDD]" type="button">
                <span>Delete report</span>
                <Trash2 className="size-4" />
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <BlacklineMeta label="Created" value={formatShortDate(item.created_at)} />
          <div className="sm:pt-0.5">
            <PrimaryLink href={`/admin/applications/${item.id}`} label="Open" tone="blackline" />
          </div>
        </div>

        <div className="rounded-[1.3rem] border border-[#111111]/10 bg-[#fafaf6] p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6c6c64]">Assigned interviewer</p>
          {item.assigned_interviewer ? (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-[#111111]/10">
                <AvatarFallback className="bg-[#111111] text-[#fafaf6]">
                  {getInitials(item.assigned_interviewer.name)}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[#111111]">{item.assigned_interviewer.name}</p>
                <p className="truncate text-xs text-[#66685d]">{item.assigned_interviewer.email}</p>
              </div>
            </div>
          ) : (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-[#111111]/10">
                <AvatarFallback className="bg-[#D8DBE2] text-[#49536B]">UN</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[#111111]">Unassigned</p>
                <p className="truncate text-xs text-[#66685d]">No interviewer selected yet</p>
              </div>
            </div>
          )}
        </div>

        <div className="rounded-[1.3rem] border border-[#111111]/10 bg-[#fafaf6] p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6c6c64]">Assignment</p>
          <div className="mt-3 space-y-3">
            <Select
              value={selectedInterviewerId}
              onValueChange={(value) => {
                setSelectedInterviewerId(value ?? "");
                setOverflowOpen(false);
              }}
            >
              <SelectTrigger
                className="h-auto w-full rounded-xl border-[#111111]/10 bg-[#fdfcf8] px-3 py-3 transition-all duration-200 hover:border-[#727D97] hover:bg-white"
                onClick={() => setOverflowOpen(false)}
              >
                {selectedInterviewer ? (
                  <div className="flex min-w-0 flex-1 items-center gap-2">
                    <Avatar className="size-8">
                      <AvatarFallback>{getInitials(selectedInterviewer.name)}</AvatarFallback>
                    </Avatar>
                    <span className="min-w-0 flex-1 space-y-0.5">
                      <span className="block truncate font-medium text-[#111111]">{selectedInterviewer.name}</span>
                      <span className="block truncate text-xs text-[#66685d]">{selectedInterviewer.email}</span>
                    </span>
                  </div>
                ) : (
                  <span className="text-sm text-[#66685d]">
                    {item.assigned_interviewer ? "Choose new interviewer" : "Choose interviewer"}
                  </span>
                )}
              </SelectTrigger>
              <SelectContent className="rounded-2xl border border-[#111111]/10 bg-[#fdfcf8] shadow-[0_18px_38px_rgba(114,125,151,0.18)]">
                <SelectGroup>
                  <SelectLabel>Available interviewers</SelectLabel>
                  {reportsDashboardInterviewers.map((interviewer) => (
                    <SelectItem key={interviewer.id} value={interviewer.id}>
                      <Avatar className="size-8 self-center">
                        <AvatarFallback>{getInitials(interviewer.name)}</AvatarFallback>
                      </Avatar>
                      <span className="min-w-0 flex-1 flex-col justify-center space-y-0.5">
                        <span className="block truncate font-medium text-[#111111]">{interviewer.name}</span>
                        <span className="block truncate text-xs text-[#66685d]">{interviewer.email}</span>
                      </span>
                      <span className="rounded-full bg-[#D8DBE2] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#49536B]">
                        {interviewer.active_assignment_count} active
                      </span>
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>

            <button
              className="w-full rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition-all duration-200 hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-45"
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


function BlacklineMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-white px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
    </div>
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

function GhostAction({
  label,
}: {
  label: string;
}) {
  return (
    <button className="rounded-full border border-[#111111]/10 bg-[#f6f6f1] px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#111111]" type="button">
      {label}
    </button>
  );
}

function PrimaryLink({
  href,
  label,
  tone,
}: {
  href: string;
  label: string;
  tone: "blackline";
}) {
  return (
    <Link
      className="inline-flex items-center gap-1 rounded-full bg-[#111111] px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-[#f7f8ec]"
      href={href}
    >
      {label}
      <ArrowUpRight className="size-3.5" />
    </Link>
  );
}

function ActionChip({
  label,
  tone,
  icon: Icon,
}: {
  label: string;
  tone: "blackline";
  icon?: typeof Eye;
}) {
  return (
    <button className="inline-flex items-center gap-1.5 rounded-full border border-[#d7ff53]/35 bg-[#d7ff53]/8 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#111111]" type="button">
      {Icon ? <Icon className="size-3.5" /> : null}
      {label}
    </button>
  );
}

function StatusMark({
  status,
  tone,
}: {
  status: string;
  tone: "blackline";
}) {
  const styles = {
    READY: "bg-[#d7ff53] text-[#111111]",
    ASSIGNED: "bg-[#7cf0ff] text-[#111111]",
    DRAFT: "bg-[#ffb347] text-[#111111]",
    PUBLISHED: "bg-[#ff6b9d] text-[#111111]",
    HIDDEN: "bg-[#8A94A6] text-[#111111]",
  };

  const className = styles[status as keyof typeof styles] ?? "bg-[#E6E9F0] text-[#111111]";

  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${className}`}>
      {status}
    </span>
  );
}

function getFilterActiveClasses(status: (typeof reportsDashboardStatuses)[number]) {
  if (status === "ALL") return "bg-[#198FF0] text-[#111111] shadow-[0_8px_20px_rgba(25,143,240,0.28)]";
  if (status === "READY") return "bg-[#d7ff53] text-[#111111] shadow-[0_8px_20px_rgba(215,255,83,0.28)]";
  if (status === "ASSIGNED") return "bg-[#7cf0ff] text-[#111111] shadow-[0_8px_20px_rgba(124,240,255,0.22)]";
  if (status === "DRAFT") return "bg-[#ffb347] text-[#111111] shadow-[0_8px_20px_rgba(255,179,71,0.24)]";
  if (status === "PUBLISHED") return "bg-[#ff6b9d] text-[#111111] shadow-[0_8px_20px_rgba(255,107,157,0.22)]";
  return "bg-[#8A94A6] text-[#111111] shadow-[0_8px_20px_rgba(138,148,166,0.24)]";
}

function getSuggestedInterviewer(item: ApplicationListItem) {
  if (item.status === "READY") return reportsDashboardInterviewers[0];
  if (item.status === "ASSIGNED") return reportsDashboardInterviewers[1];
  if (item.status === "DRAFT") return reportsDashboardInterviewers[2];
  return item.assigned_interviewer
    ? {
        ...item.assigned_interviewer,
        active_assignment_count: reportsDashboardInterviewers.find(
          (interviewer) => interviewer.id === item.assigned_interviewer?.id,
        )?.active_assignment_count ?? 0,
      }
    : reportsDashboardInterviewers[0];
}

function getAssignmentActionLabel(item: ApplicationListItem) {
  if (item.status === "READY") return "Assign interviewer";
  if (item.status === "ASSIGNED" || item.status === "DRAFT") return "Reassign interviewer";
  return "Assignment locked";
}

function getAssignmentCopy(item: ApplicationListItem) {
  if (item.status === "READY") return "Queue is ready for first assignment";
  if (item.status === "ASSIGNED") return "Can be reassigned if workload shifts";
  if (item.status === "DRAFT") return "Draft is in progress and can still move";
  if (item.status === "PUBLISHED") return "Published ownership remains visible";
  return "No assignment needed";
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
