"use client";

import { motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  Mail,
  PencilLine,
  Plus,
  ShieldAlert,
  UserRound,
  KeyRound,
  Stars,
  X,
} from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { adminInterviewersSandboxState } from "@/lib/design-lab/adminInterviewersMock";
import type { InterviewerAssignmentSummaryItem, InterviewerListItem } from "@/lib/types";

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

const sessionLogEntries = [
  {
    id: "interviewer-log-1",
    action: "Created",
    subject: "Aarav Desai",
    detail: "New interviewer account added and made available for assignment.",
    time: "Just now",
    accent: "#d9f99d",
    badgeText: "#365314",
  },
  {
    id: "interviewer-log-2",
    action: "Reassigned",
    subject: "PLK-2026-0184",
    detail: "Moved from Aanya Sen to Rhea Kapoor after workload review.",
    time: "4 min ago",
    accent: "#dbeafe",
    badgeText: "#1e3a8a",
  },
  {
    id: "interviewer-log-3",
    action: "Edited",
    subject: "Nisha Rao",
    detail: "Display name and account email updated in the manager.",
    time: "11 min ago",
    accent: "#e0f2fe",
    badgeText: "#0c4a6e",
  },
  {
    id: "interviewer-log-4",
    action: "Password",
    subject: "Kabir Mehta",
    detail: "Password reset requested through the edit sheet.",
    time: "18 min ago",
    accent: "#fef3c7",
    badgeText: "#92400e",
  },
  {
    id: "interviewer-log-5",
    action: "Blocked",
    subject: "Remove interviewer",
    detail: "Deletion prevented while active assignments were still attached.",
    time: "27 min ago",
    accent: "#fee2e2",
    badgeText: "#9f1239",
  },
] as const;

const avatarPhotos: Record<string, string> = {
  "intr-001": "https://i.pravatar.cc/160?img=32",
  "intr-004": "https://i.pravatar.cc/160?img=47",
};

type AssignmentSource = "assigned" | "available" | "reassign";
type AssignmentModalItem = InterviewerAssignmentSummaryItem & { source: AssignmentSource };

export function AdminInterviewersSandbox() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [manageAssignmentsOpen, setManageAssignmentsOpen] = useState(false);
  const [editSheetOpen, setEditSheetOpen] = useState(false);
  const [selectedInterviewerId, setSelectedInterviewerId] = useState(
    adminInterviewersSandboxState.selectedInterviewer.id,
  );

  const selectedInterviewer = useMemo(
    () =>
      adminInterviewersSandboxState.interviewers.find((item) => item.id === selectedInterviewerId) ??
      adminInterviewersSandboxState.selectedInterviewer,
    [selectedInterviewerId],
  );

  const assignmentSummary = adminInterviewersSandboxState.assignmentSummary;
  const assignmentItems = useMemo(
    () => ({
      assigned: mapAssignmentItems(assignmentSummary.currently_assigned, "assigned"),
      available: mapAssignmentItems(assignmentSummary.available_to_assign, "available"),
      reassign: mapAssignmentItems(assignmentSummary.available_to_reassign, "reassign"),
    }),
    [assignmentSummary],
  );

  const hasOverlayOpen = createModalOpen || manageAssignmentsOpen || editSheetOpen;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;

    if (hasOverlayOpen) {
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [hasOverlayOpen]);

  return (
    <div
      className={`${libreFranklin.variable} ${ibmPlexSans.variable} min-h-screen text-slate-900`}
      style={pageCanvasStyle}
    >
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen text-slate-900"
        initial={{ opacity: 0, y: 26 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <AdminDesignLabNavbar activeItem="Interviewers" />

        <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
            <div className="space-y-6">
              <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
                <div className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm xl:h-full">
                  <div className="flex h-full flex-col justify-between gap-6">
                    <div>
                      <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
                        <span className="inline-flex items-center gap-2 text-slate-800">
                          <Stars className="size-3.5" />
                          Interview operations
                        </span>
                      </div>
                      <div className="mt-5 space-y-4">
                        <h1
                          className="max-w-4xl text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                          style={{ fontFamily: "var(--font-display)" }}
                        >
                          Interviewer Manager
                        </h1>
                        <p className="max-w-3xl text-base leading-[1.6] text-slate-600" style={{ fontFamily: "var(--font-body)" }}>
                          Review the active interviewer roster, open assignment buckets when work needs to move, and
                          manage interviewer account details without leaving the page context.
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
                        onClick={() => setCreateModalOpen(true)}
                        type="button"
                      >
                        <Plus className="size-4" />
                        Add interviewer
                      </button>
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm xl:h-full">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Status totals</p>
                  <div className="mt-4 space-y-3">
                    <MetricStrip
                      label="Interviewers"
                      value={adminInterviewersSandboxState.metrics.interviewers}
                    />
                    <MetricStrip
                      label="Active assignments"
                      value={adminInterviewersSandboxState.metrics.activeAssignments}
                    />
                    <MetricStrip label="Ready pool" value={adminInterviewersSandboxState.metrics.readyPool} />
                  </div>
                </div>
              </section>

              <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {adminInterviewersSandboxState.interviewers.map((item) => (
                  <InterviewerCard
                    key={item.id}
                    item={item}
                    onEdit={() => {
                      setSelectedInterviewerId(item.id);
                      setEditSheetOpen(true);
                    }}
                    onManageAssignments={() => {
                      setSelectedInterviewerId(item.id);
                      setManageAssignmentsOpen(true);
                    }}
                  />
                ))}
              </section>
            </div>

            <aside className="grid gap-5 self-start">
              <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Session log</p>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  Actions taken during this session appear here in order.
                </p>
                <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white/70">
                  <div className="border-b border-slate-200 px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                      Current session
                    </p>
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
                              <p className="text-sm font-semibold text-slate-800">{entry.subject}</p>
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

        {createModalOpen ? (
          <CenteredOverlay onClose={() => setCreateModalOpen(false)}>
            <div className="rounded-[1.9rem] border border-slate-200 bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.16)]">
              <SurfaceHeader
                eyebrow="Create interviewer"
                title="Add interviewer"
                onClose={() => setCreateModalOpen(false)}
              />
              <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-600">
                Create a new interviewer account with the same core fields used in the live frontend.
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <FieldPreview label="Display name" value={adminInterviewersSandboxState.createDraft.name} icon={UserRound} />
                <FieldPreview label="Email" value={adminInterviewersSandboxState.createDraft.email} icon={Mail} />
                <FieldPreview label="Password" value="........" icon={KeyRound} />
                <FieldPreview label="Confirm password" value="........" icon={KeyRound} />
              </div>
              <div className="mt-6 flex justify-end">
                <button className="rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800" type="button">
                  Create interviewer
                </button>
              </div>
            </div>
          </CenteredOverlay>
        ) : null}

        {manageAssignmentsOpen ? (
          <CenteredOverlay onClose={() => setManageAssignmentsOpen(false)}>
            <div className="rounded-[1.9rem] border border-slate-200 bg-white p-6 shadow-[0_24px_70px_rgba(15,23,42,0.16)]">
              <SurfaceHeader
                eyebrow="Assignment buckets"
                title={`Manage assignments - ${selectedInterviewer.name}`}
                onClose={() => setManageAssignmentsOpen(false)}
              />
              <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">
                Keep the bucket logic from the real frontend, but present it inside the same mock system as the other
                admin pages.
              </p>
              <div className="mt-6 grid gap-4 xl:grid-cols-3">
                <AssignmentBucket
                  title="Currently assigned"
                  items={assignmentItems.assigned}
                  actionLabel="Remove"
                  showCurrentOwner={false}
                />
                <AssignmentBucket
                  title="Available to assign"
                  items={assignmentItems.available}
                  actionLabel="Add"
                  showCurrentOwner={false}
                />
                <AssignmentBucket
                  title="Available to reassign"
                  items={assignmentItems.reassign}
                  actionLabel="Add"
                  showCurrentOwner
                />
              </div>
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-200 pt-5">
                <button
                  className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  onClick={() => setManageAssignmentsOpen(false)}
                  type="button"
                >
                  Close
                </button>
                <button
                  className="inline-flex items-center justify-center rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
                  onClick={() => setManageAssignmentsOpen(false)}
                  type="button"
                >
                  Save changes
                </button>
              </div>
            </div>
          </CenteredOverlay>
        ) : null}

        {editSheetOpen ? (
          <FloatingSheet onClose={() => setEditSheetOpen(false)}>
            <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-[0_28px_80px_rgba(15,23,42,0.18)]">
              <div className="interviewer-sheet-scroll max-h-[calc(100vh-3rem)] overflow-y-auto px-6 py-6">
                <SurfaceHeader
                  eyebrow="Edit interviewer"
                  title={selectedInterviewer.name}
                  onClose={() => setEditSheetOpen(false)}
                />
                <div className="mt-5 flex items-center gap-4 rounded-[1.4rem] border border-slate-200 bg-white/80 p-4">
                  <InterviewerAvatar item={selectedInterviewer} sizeClassName="size-14" />
                  <div className="min-w-0">
                    <p className="truncate text-lg font-semibold text-slate-800">{selectedInterviewer.name}</p>
                    <p className="truncate text-sm text-slate-500">{selectedInterviewer.email}</p>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  <EditSection
                    icon={UserRound}
                    title="Display name"
                    value={selectedInterviewer.name}
                    action="Save name"
                  />
                  <EditSection
                    icon={Mail}
                    title="Email"
                    value={selectedInterviewer.email}
                    action="Update email"
                  />
                  <EditSection icon={KeyRound} title="Password" value="Generate new password" action="Change password" />
                </div>

                <div className="mt-6 rounded-[1.4rem] border border-rose-200 bg-rose-50 p-4">
                  <div className="flex items-start gap-3">
                    <span className="inline-flex rounded-full bg-rose-100 p-2 text-rose-700">
                      <ShieldAlert className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-semibold text-rose-800">Danger zone</p>
                      <p className="mt-2 text-sm leading-6 text-rose-700">
                        This interviewer still has active assignments, so removal is blocked in the current state.
                      </p>
                      <div className="mt-4">
                        <Button variant="danger">Remove interviewer</Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </FloatingSheet>
        ) : null}
      </motion.div>
      <style jsx global>{`
        .interviewer-sheet-scroll {
          scrollbar-width: thin;
          scrollbar-color: #cbd5e1 transparent;
          scrollbar-gutter: stable;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar {
          width: 12px;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar-button {
          display: none;
          height: 0;
          width: 0;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar-track {
          background: transparent;
          margin: 16px 0;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar-thumb {
          border: 3px solid transparent;
          border-radius: 999px;
          background-clip: padding-box;
          background-color: #cbd5e1;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar-thumb:hover {
          background-color: #94a3b8;
        }
      `}</style>
    </div>
  );
}

function InterviewerCard({
  item,
  onManageAssignments,
  onEdit,
}: {
  item: InterviewerListItem;
  onManageAssignments: () => void;
  onEdit: () => void;
}) {
  return (
    <motion.article
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[1.8rem] border border-slate-200 bg-white/80 text-slate-900 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <InterviewerAvatar item={item} sizeClassName="size-12" />
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="space-y-2">
          <h4
            className="text-[1.8rem] font-black leading-none tracking-tight text-slate-800"
            style={{ fontFamily: "var(--font-display)" }}
          >
            {item.name}
          </h4>
          <p className="truncate text-sm text-slate-500">{item.email}</p>
        </div>

        <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Active assignments</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-800">
            {item.active_assignment_count}
          </p>
        </div>

        <div className="grid gap-2">
          <button
            className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800"
            onClick={onManageAssignments}
            type="button"
          >
            <ArrowLeftRight className="size-4" />
            Manage assignments
          </button>
          <button
            className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            onClick={onEdit}
            type="button"
          >
            <PencilLine className="size-4" />
            Edit interviewer
          </button>
        </div>
      </div>
    </motion.article>
  );
}

function InterviewerAvatar({
  item,
  sizeClassName,
}: {
  item: InterviewerListItem;
  sizeClassName: string;
}) {
  const photo = avatarPhotos[item.id];

  return (
    <Avatar className={`${sizeClassName} overflow-hidden border border-slate-200 bg-slate-100`}>
      {photo ? <img alt={item.name} className="h-full w-full object-cover" src={photo} /> : null}
      <AvatarFallback className="bg-slate-200 text-slate-700">{getInitials(item.name)}</AvatarFallback>
    </Avatar>
  );
}

function CenteredOverlay({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-40 grid place-items-center bg-slate-900/24 px-5 py-8 backdrop-blur-[10px]"
      onClick={onClose}
      role="presentation"
    >
      <div className="w-full max-w-[72rem]" onClick={(event) => event.stopPropagation()} role="presentation">
        {children}
      </div>
    </div>
  );
}

function FloatingSheet({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-40 overflow-y-auto bg-slate-900/20 backdrop-blur-[8px]"
      onClick={onClose}
      role="presentation"
    >
      <div className="flex min-h-screen justify-end p-4 md:p-6">
        <div
          className="w-full max-w-[34rem] self-start"
          onClick={(event) => event.stopPropagation()}
          role="presentation"
        >
          {children}
        </div>
      </div>
    </div>
  );
}

function SurfaceHeader({
  eyebrow,
  title,
  onClose,
}: {
  eyebrow: string;
  title: string;
  onClose: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">{eyebrow}</p>
        <h2
          className="mt-3 text-[2.2rem] font-black leading-[0.98] tracking-tight text-slate-800"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {title}
        </h2>
      </div>
      <button
        className="grid size-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50"
        onClick={onClose}
        type="button"
      >
        <X className="size-4" />
      </button>
    </div>
  );
}

function FieldPreview({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof UserRound;
}) {
  return (
    <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
      <div className="flex items-center gap-2">
        <span className="inline-flex rounded-full bg-blue-50 p-2 text-blue-700">
          <Icon className="size-4" />
        </span>
        <p className="text-sm font-semibold text-slate-800">{label}</p>
      </div>
      <div className="mt-4 rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
        {value}
      </div>
    </div>
  );
}

function EditSection({
  icon: Icon,
  title,
  value,
  action,
}: {
  icon: typeof UserRound;
  title: string;
  value: string;
  action: string;
}) {
  return (
    <div className="rounded-[1.4rem] border border-slate-200 bg-white/70 p-4">
      <div className="flex items-start gap-3">
        <span className="inline-flex rounded-full bg-blue-50 p-2 text-blue-700">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold text-slate-800">{title}</p>
          <div className="mt-3 rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">
            {value}
          </div>
          <div className="mt-4 flex justify-end">
            <button className="rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800" type="button">
              {action}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AssignmentBucket({
  title,
  items,
  actionLabel,
  showCurrentOwner,
}: {
  title: string;
  items: AssignmentModalItem[];
  actionLabel: string;
  showCurrentOwner: boolean;
}) {
  return (
    <section className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)]">
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-lg font-semibold tracking-tight text-slate-800">{title}</p>
        <Badge variant="outline">{items.length}</Badge>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.application_id} className={getAssignmentClassName(item)}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <p className="text-sm font-semibold text-slate-800">{item.application_display_id}</p>
                </div>
                {showCurrentOwner && item.current_interviewer ? (
                  <p className="text-sm text-slate-600">
                    Current interviewer: {item.current_interviewer.name}
                  </p>
                ) : null}
              </div>
              <button className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50" type="button">
                {actionLabel}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function MetricStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-slate-200 bg-white px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function mapAssignmentItems(
  items: InterviewerAssignmentSummaryItem[],
  source: AssignmentSource,
): AssignmentModalItem[] {
  return items.map((item) => ({ ...item, source }));
}

function getAssignmentClassName(item: AssignmentModalItem) {
  if (item.source === "assigned") {
    return "rounded-[1.15rem] border border-amber-200 bg-amber-50 px-4 py-3";
  }

  if (item.source === "reassign") {
    return "rounded-[1.15rem] border border-blue-200 bg-blue-50 px-4 py-3";
  }

  return "rounded-[1.15rem] border border-slate-200 bg-white px-4 py-3";
}

function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

const pageCanvasStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  backgroundImage: "radial-gradient(#e2e8f0 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
  fontFamily: "var(--font-body)",
};
