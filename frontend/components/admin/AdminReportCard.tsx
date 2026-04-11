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
  variable: "--font-display",
  display: "swap",
});

export function AdminReportCard({
  item,
  interviewers,
  selectedInterviewerId,
  onSelectedInterviewerChange,
  onGenerate,
  onAssign,
  onToggleHidden,
  onDelete,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onPendingDisplayIdChange,
  pendingDisplayId,
  isGenerating,
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
  onGenerate: () => void;
  onAssign: (mode: "assign" | "reassign") => void;
  onToggleHidden: () => void;
  onDelete: () => void;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onSaveEdit: () => void;
  onPendingDisplayIdChange: (value: string) => void;
  pendingDisplayId: string;
  isGenerating: boolean;
  isBusy: boolean;
  isHiddenBusy: boolean;
  isDeleting: boolean;
  isEditingDisplayId: boolean;
  isSavingDisplayId: boolean;
}) {
  const [overflowOpen, setOverflowOpen] = useState(false);
  const overflowRef = useRef<HTMLDivElement | null>(null);
  const selectedInterviewer = interviewers.find((interviewer) => interviewer.id === selectedInterviewerId);
  const canGenerate = item.status === "READY";
  const canAssign = item.status === "COMPLETE";
  const canReassign = item.status === "ASSIGNED";
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
      className={`${libreFranklin.variable} rounded-[1.8rem] border border-slate-200 bg-white/80 text-slate-900 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
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
                value={pendingDisplayId}
                onChange={(event) => onPendingDisplayIdChange(event.target.value)}
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
            <h4
              className="text-[1.8rem] font-black leading-none tracking-tight text-slate-800"
              style={{ fontFamily: "var(--font-display)" }}
            >
              {item.display_id}
            </h4>
          )}
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
                className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50"
                onClick={() => {
                  setOverflowOpen(false);
                  onStartEdit();
                }}
                type="button"
              >
                <span>Edit ID</span>
                <PencilLine className="size-4" />
              </button>
              <button
                className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50 disabled:opacity-55"
                disabled={isHiddenBusy}
                onClick={() => {
                  setOverflowOpen(false);
                  onToggleHidden();
                }}
                type="button"
              >
                <span>{isHiddenBusy ? "Saving..." : item.is_hidden ? "Unhide report" : "Hide report"}</span>
                {item.is_hidden ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
              </button>
              <button
                className="flex w-full items-center justify-between rounded-[0.8rem] px-3 py-2 text-left text-sm font-medium text-rose-700 transition-colors duration-200 hover:bg-rose-50 disabled:opacity-55"
                disabled={isDeleting}
                onClick={() => {
                  setOverflowOpen(false);
                  onDelete();
                }}
                type="button"
              >
                <span>{isDeleting ? "Deleting..." : "Delete report"}</span>
                <Trash2 className="size-4" />
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <CardMeta label="Last updated" value={formatDateTime(item.last_activity_at)} />
          <div className="sm:pt-0.5">
            <PrimaryLink href={`/admin/applications/${item.id}`} label="Open" />
          </div>
        </div>

        <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Assigned interviewer</p>
          {item.assigned_interviewer ? (
            <div className="mt-3 flex items-center gap-3">
              <Avatar className="size-10 border border-slate-200 bg-slate-100">
                <AvatarFallback className="bg-slate-800 text-white">{getInitials(item.assigned_interviewer.name)}</AvatarFallback>
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
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
            {canGenerate ? "Report generation" : "Assignment"}
          </p>
          <div className="mt-3 space-y-3">
            {canGenerate ? (
              <div className="flex w-full items-center rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-500">
                Generate Pages 4-5 to unlock assignment.
              </div>
            ) : canMutateAssignment ? (
              <Select value={selectedInterviewerId} onValueChange={(value) => onSelectedInterviewerChange(value ?? "")}>
                <SelectTrigger className="h-auto w-full rounded-xl border-slate-200 bg-white px-3 py-3 transition-all duration-200 hover:border-blue-200 hover:bg-blue-50/40">
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
                <SelectContent className="rounded-2xl border border-slate-200 bg-white shadow-[0_18px_38px_rgba(15,23,42,0.12)]">
                  <SelectGroup>
                    <SelectLabel>Available interviewers</SelectLabel>
                    {interviewers.map((interviewer) => (
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
            ) : (
              <div className="flex w-full items-center rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm text-slate-500">
                Assignment locked
              </div>
            )}

            {canGenerate ? (
              <button
                className="w-full rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition-all duration-200 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-45"
                disabled={isGenerating}
                onClick={onGenerate}
                type="button"
              >
                {isGenerating ? "Generating..." : "Generate report"}
              </button>
            ) : (
              <button
                className="w-full rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition-all duration-200 hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-45"
                disabled={isBusy || !selectedInterviewerId || !canMutateAssignment}
                onClick={() => onAssign(canAssign ? "assign" : "reassign")}
                type="button"
              >
                {isBusy ? "Saving..." : getAssignmentActionLabel(item)}
              </button>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

function CardMeta({ label, value }: { label: string; value: string }) {
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
    READY: "border-lime-200 bg-lime-100 text-lime-900",
    COMPLETE: "border-amber-200 bg-amber-100 text-amber-900",
    ASSIGNED: "border-sky-200 bg-sky-100 text-sky-900",
    HIDDEN: "border-slate-200 bg-slate-100 text-slate-700",
  };

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status as keyof typeof styles] ?? "border-slate-200 bg-slate-100 text-slate-700"}`}>
      {status}
    </span>
  );
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
  if (item.status === "COMPLETE") return "Assign interviewer";
  if (item.status === "ASSIGNED") return "Reassign interviewer";
  return "Assignment locked";
}
