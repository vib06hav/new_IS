"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Eye,
  EyeOff,
  MoreHorizontal,
  PencilLine,
  Trash2,
} from "lucide-react";
import { Libre_Franklin } from "next/font/google";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
} from "@/components/shadcn/select";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-reports-display",
});

export function AdminReportCard({
  item,
  interviewers,
  selectedInterviewerId,
  onSelectedInterviewerChange,
  onAssign,
  onToggleHidden,
  onDelete,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onDraftDisplayIdChange,
  draftDisplayId,
  isBusy,
  isHiddenBusy,
  isDeleting,
  isEditingDisplayId,
  isSavingDisplayId,
}: {
  item: ApplicationListItem;
  interviewers: InterviewerListItem[];
  selectedInterviewerId: string;
  onSelectedInterviewerChange: (value: string) => void;
  onAssign: (mode: "assign" | "reassign") => void;
  onToggleHidden: () => void;
  onDelete: () => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onDraftDisplayIdChange: (value: string) => void;
  draftDisplayId: string;
  isBusy: boolean;
  isHiddenBusy: boolean;
  isDeleting: boolean;
  isEditingDisplayId: boolean;
  isSavingDisplayId: boolean;
}) {
  const [overflowOpen, setOverflowOpen] = useState(false);
  const overflowRef = useRef<HTMLDivElement | null>(null);
  const selectedInterviewer = interviewers.find((interviewer) => interviewer.id === selectedInterviewerId);
  const canAssign = item.status === "READY";
  const canReassign = item.status === "ASSIGNED" || item.status === "DRAFT";
  const canMutateAssignment = canAssign || canReassign;

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
      className={`${libreFranklin.variable} rounded-3xl border border-slate-200 bg-white text-slate-900 shadow-[0_10px_30px_rgba(2,12,32,0.05)] transition-all hover:shadow-md`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {item.is_hidden ? <StatusMark status="HIDDEN" /> : null}
            <StatusMark status={item.status} />
          </div>
          {isEditingDisplayId ? (
            <div className="space-y-2">
              <Input
                label="Application ID"
                autoFocus
                className="mt-0"
                value={draftDisplayId}
                onChange={(event) => onDraftDisplayIdChange(event.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <Button size="sm" disabled={isSavingDisplayId} onClick={onSaveEdit}>
                  {isSavingDisplayId ? "Saving..." : "Save ID"}
                </Button>
                <Button size="sm" variant="secondary" disabled={isSavingDisplayId} onClick={onCancelEdit}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <h4 className="text-xl font-black tracking-tight text-slate-800" style={{ fontFamily: "var(--font-reports-display)" }}>
              {item.display_id}
            </h4>
          )}
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
            <div className="absolute right-0 z-20 mt-2 min-w-44 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl ring-1 ring-black ring-opacity-5">
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors duration-200 hover:bg-[#E6E9F0]" onClick={() => { setOverflowOpen(false); onStartEdit(); }} type="button">
                <span>Edit ID</span>
                <PencilLine className="size-4" />
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors duration-200 hover:bg-[#E6E9F0] disabled:opacity-55" disabled={isHiddenBusy} onClick={() => { setOverflowOpen(false); onToggleHidden(); }} type="button">
                <span>{isHiddenBusy ? "Saving..." : item.is_hidden ? "Unhide report" : "Hide report"}</span>
                {item.is_hidden ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
              <button className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-[#AF3030] transition-colors duration-200 hover:bg-[#F4DDDD] disabled:opacity-55" disabled={isDeleting} onClick={() => { setOverflowOpen(false); onDelete(); }} type="button">
                <span>{isDeleting ? "Deleting..." : "Delete report"}</span>
                <Trash2 className="size-4" />
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <BlacklineMeta label="Last updated" value={formatDateTime(item.last_activity_at)} />
          <div className="sm:pt-0.5">
            <PrimaryLink href={`/admin/applications/${item.id}`} label="Open" />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6c6c64]">Assigned interviewer</p>
          {item.assigned_interviewer ? (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-[#111111]/10">
                <AvatarFallback className="bg-[#111111] text-[#fafaf6]">{getInitials(item.assigned_interviewer.name)}</AvatarFallback>
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

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6c6c64]">Assignment</p>
          <div className="mt-3 space-y-3">
            {canMutateAssignment ? (
              <Select value={selectedInterviewerId} onValueChange={(value) => onSelectedInterviewerChange(value ?? "")}>
                <SelectTrigger className="h-auto w-full rounded-xl border-slate-200 bg-white px-3 py-3 transition-all duration-200 hover:border-blue-300 hover:shadow-sm">
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
                    <span className="text-sm text-slate-500">{canAssign ? "Choose interviewer" : "Choose new interviewer"}</span>
                  )}
                </SelectTrigger>
                <SelectContent className="rounded-2xl border border-slate-200 bg-white shadow-xl">
                  <SelectGroup>
                    <SelectLabel>Available interviewers</SelectLabel>
                    {interviewers.map((interviewer) => (
                      <SelectItem key={interviewer.id} value={interviewer.id}>
                        <Avatar className="size-8 self-center">
                          <AvatarFallback>{getInitials(interviewer.name)}</AvatarFallback>
                        </Avatar>
                        <span className="min-w-0 flex-1 flex-col justify-center space-y-0.5">
                          <span className="block truncate font-medium text-[#111111]">{interviewer.name}</span>
                          <span className="block truncate text-xs text-[#66685d]">{interviewer.email}</span>
                        </span>
                        <span className="rounded-full bg-[#D8DBE2] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#49536B]">{interviewer.active_assignment_count} active</span>
                      </SelectItem>
                    ))}
                  </SelectGroup>
                </SelectContent>
              </Select>
            ) : (
              <div className="flex w-full items-center rounded-xl border border-[#111111]/10 bg-[#fdfcf8] px-3 py-3 text-sm text-[#66685d]">Assignment locked</div>
            )}

            <button className="w-full rounded-full bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-blue-700 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-45" disabled={isBusy || !selectedInterviewerId || !canMutateAssignment} onClick={() => onAssign(canAssign ? "assign" : "reassign")} type="button">
              {isBusy ? "Saving..." : getAssignmentActionLabel(item)}
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function BlacklineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function PrimaryLink({ href, label }: { href: string; label: string }) {
  return (
    <Link className="inline-flex items-center gap-1 rounded-full bg-blue-600 px-4 py-2 text-xs font-bold uppercase tracking-widest text-white shadow-sm transition-all hover:bg-blue-700" href={href}>
      {label}
      <ArrowUpRight className="size-3.5" />
    </Link>
  );
}

function StatusMark({ status }: { status: string }) {
  const styles = {
    READY: "bg-[#d7ff53] text-[#111111]",
    ASSIGNED: "bg-[#7cf0ff] text-[#111111]",
    DRAFT: "bg-[#ffb347] text-[#111111]",
    PUBLISHED: "bg-[#ff6b9d] text-[#111111]",
    HIDDEN: "bg-[#8A94A6] text-[#111111]",
  };

  return <span className={`inline-flex rounded-full px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status as keyof typeof styles] ?? "bg-[#E6E9F0] text-[#111111]"}`}>{status}</span>;
}

function getInitials(name: string) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase() ?? "").join("");
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

function getAssignmentActionLabel(item: ApplicationListItem) {
  if (item.status === "READY") return "Assign interviewer";
  if (item.status === "ASSIGNED" || item.status === "DRAFT") return "Reassign interviewer";
  return "Assignment locked";
}
