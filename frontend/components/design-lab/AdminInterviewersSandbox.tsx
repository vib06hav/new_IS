"use client";

import { motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
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
import {
  Cormorant_Garamond,
  IBM_Plex_Sans,
  Space_Grotesk,
} from "next/font/google";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { adminInterviewersSandboxState } from "@/lib/design-lab/adminInterviewersMock";
import type { InterviewerAssignmentSummaryItem, InterviewerListItem } from "@/lib/types";

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

const sessionLogEntries = [
  {
    id: "interviewer-log-1",
    action: "Created",
    subject: "Aarav Desai",
    detail: "New interviewer account added and made available for assignment.",
    time: "Just now",
    accent: "#D7FF53",
    badgeText: "#111111",
  },
  {
    id: "interviewer-log-2",
    action: "Reassigned",
    subject: "PLK-2026-0184",
    detail: "Moved from Aanya Sen to Rhea Kapoor after workload review.",
    time: "4 min ago",
    accent: "#198FF0",
    badgeText: "#F7F7F1",
  },
  {
    id: "interviewer-log-3",
    action: "Edited",
    subject: "Nisha Rao",
    detail: "Display name and account email updated in the manager.",
    time: "11 min ago",
    accent: "#7CF0FF",
    badgeText: "#111111",
  },
  {
    id: "interviewer-log-4",
    action: "Password",
    subject: "Kabir Mehta",
    detail: "Password reset requested through the edit sheet.",
    time: "18 min ago",
    accent: "#FFB347",
    badgeText: "#111111",
  },
  {
    id: "interviewer-log-5",
    action: "Blocked",
    subject: "Remove interviewer",
    detail: "Deletion prevented while active assignments were still attached.",
    time: "27 min ago",
    accent: "#FF6B9D",
    badgeText: "#111111",
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
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        cormorant.variable,
        "min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen bg-[#D8DBE2] text-[#111111]"
        initial={{ opacity: 0, y: 26 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <AdminDesignLabNavbar activeItem="Interviewers" />

        <div className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]">
            <div className="space-y-6">
              <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
                <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6 xl:h-full">
                  <div className="flex h-full flex-col justify-between gap-6">
                    <div>
                      <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                        <span className="inline-flex items-center gap-2 text-[#111111]">
                          <Stars className="size-3.5" />
                          Interview operations
                        </span>
                      </div>
                      <div className="mt-5 space-y-4">
                        <h1
                          className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.85rem]"
                          style={{ fontFamily: "var(--font-reports-cormorant)" }}
                        >
                          Interviewer Manager
                        </h1>
                        <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                          Review the active interviewer roster, open assignment buckets when work needs to move, and
                          manage interviewer account details without leaving the page context.
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        className="inline-flex items-center gap-2 rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444]"
                        onClick={() => setCreateModalOpen(true)}
                        type="button"
                      >
                        <Plus className="size-4" />
                        Add interviewer
                      </button>
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 xl:h-full">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Status totals</p>
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
              <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-5">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Session log</p>
                <p className="mt-3 text-sm leading-6 text-[#49536B]">
                  Actions taken during this session appear here in order.
                </p>
                <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0]">
                  <div className="border-b border-[#727D97] px-4 py-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">
                      Current session
                    </p>
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
                              <p className="text-sm font-semibold text-[#111111]">{entry.subject}</p>
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

        {createModalOpen ? (
          <CenteredOverlay onClose={() => setCreateModalOpen(false)}>
            <div className="rounded-[1.9rem] border border-[#727D97] bg-[#F7F7F1] p-6 shadow-[0_24px_70px_rgba(114,125,151,0.24)]">
              <SurfaceHeader
                eyebrow="Create interviewer"
                title="Add interviewer"
                onClose={() => setCreateModalOpen(false)}
              />
              <p className="mt-4 max-w-2xl text-sm leading-7 text-[#49536B]">
                Create a new interviewer account with the same core fields used in the live frontend.
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <FieldPreview label="Display name" value={adminInterviewersSandboxState.createDraft.name} icon={UserRound} />
                <FieldPreview label="Email" value={adminInterviewersSandboxState.createDraft.email} icon={Mail} />
                <FieldPreview label="Password" value="••••••••" icon={KeyRound} />
                <FieldPreview label="Confirm password" value="••••••••" icon={KeyRound} />
              </div>
              <div className="mt-6 flex justify-end">
                <Button>Create interviewer</Button>
              </div>
            </div>
          </CenteredOverlay>
        ) : null}

        {manageAssignmentsOpen ? (
          <CenteredOverlay onClose={() => setManageAssignmentsOpen(false)}>
            <div className="rounded-[1.9rem] border border-[#727D97] bg-[#F7F7F1] p-6 shadow-[0_24px_70px_rgba(114,125,151,0.24)]">
              <SurfaceHeader
                eyebrow="Assignment buckets"
                title={`Manage assignments · ${selectedInterviewer.name}`}
                onClose={() => setManageAssignmentsOpen(false)}
              />
              <p className="mt-4 max-w-3xl text-sm leading-7 text-[#49536B]">
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
              <div className="mt-6 flex items-center justify-end gap-3 border-t border-[#727D97]/45 pt-5">
                <button
                  className="inline-flex items-center justify-center rounded-full border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm font-semibold text-[#111111] transition hover:bg-[#E6E9F0]"
                  onClick={() => setManageAssignmentsOpen(false)}
                  type="button"
                >
                  Close
                </button>
                <button
                  className="inline-flex items-center justify-center rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444]"
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
            <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[#F7F7F1] shadow-[0_28px_80px_rgba(114,125,151,0.28)]">
              <div className="interviewer-sheet-scroll max-h-[calc(100vh-3rem)] overflow-y-auto px-6 py-6">
                <SurfaceHeader
                  eyebrow="Edit interviewer"
                  title={selectedInterviewer.name}
                  onClose={() => setEditSheetOpen(false)}
                />
                <div className="mt-5 flex items-center gap-4 rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-4">
                  <InterviewerAvatar item={selectedInterviewer} sizeClassName="size-14" />
                  <div className="min-w-0">
                    <p className="truncate text-lg font-semibold text-[#111111]">{selectedInterviewer.name}</p>
                    <p className="truncate text-sm text-[#49536B]">{selectedInterviewer.email}</p>
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

                <div className="mt-6 rounded-[1.4rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] p-4">
                  <div className="flex items-start gap-3">
                    <span className="inline-flex rounded-full bg-[#FF6B9D]/18 p-2 text-[#9A315A]">
                      <ShieldAlert className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-semibold text-[#7F2247]">Danger zone</p>
                      <p className="mt-2 text-sm leading-6 text-[#9A315A]">
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
          scrollbar-color: #8a94a6 transparent;
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
          background-color: #8a94a6;
        }

        .interviewer-sheet-scroll::-webkit-scrollbar-thumb:hover {
          background-color: #727d97;
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
      className="rounded-[1.8rem] border border-[#727D97] bg-white text-[#121212] shadow-[0_18px_50px_rgba(114,125,151,0.14)]"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <div className="flex items-start justify-between gap-4 border-b border-[#111111]/10 px-5 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <InterviewerAvatar item={item} sizeClassName="size-12" />
          <div className="min-w-0" />
        </div>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div className="space-y-2">
          <h4
            className="text-[2rem] leading-none tracking-[-0.07em] text-[#111111]"
            style={{ fontFamily: "var(--font-reports-space)" }}
          >
            {item.name}
          </h4>
          <p className="truncate text-sm text-[#66685D]">{item.email}</p>
        </div>

        <div className="rounded-[1.3rem] border border-[#111111]/10 bg-[#FAFAF6] p-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#6C6C64]">Active assignments</p>
          <p className="mt-3 text-3xl font-semibold tracking-[-0.05em] text-[#111111]">
            {item.active_assignment_count}
          </p>
        </div>

        <div className="grid gap-2">
          <button
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444]"
            onClick={onManageAssignments}
            type="button"
          >
            <ArrowLeftRight className="size-4" />
            Manage assignments
          </button>
          <button
            className="inline-flex items-center justify-center gap-2 rounded-full border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm font-semibold text-[#111111] transition hover:bg-[#E6E9F0]"
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
    <Avatar className={`${sizeClassName} overflow-hidden border border-[#727D97] bg-[#E6E9F0]`}>
      {photo ? <img alt={item.name} className="h-full w-full object-cover" src={photo} /> : null}
      <AvatarFallback className="bg-[#AAB4C8] text-[#111111]">{getInitials(item.name)}</AvatarFallback>
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
      className="fixed inset-0 z-40 grid place-items-center bg-[#111111]/42 px-5 py-8 backdrop-blur-[10px]"
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
      className="fixed inset-0 z-40 overflow-y-auto bg-[#111111]/34 backdrop-blur-[8px]"
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
        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">{eyebrow}</p>
        <h2
          className="mt-3 text-[2.4rem] leading-[0.96] tracking-[-0.06em] text-[#111111]"
          style={{ fontFamily: "var(--font-reports-cormorant)" }}
        >
          {title}
        </h2>
      </div>
      <button
        className="grid size-10 place-items-center rounded-full border border-[#727D97] bg-[#E6E9F0] text-[#111111] transition hover:bg-[#D8DBE2]"
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
    <div className="rounded-[1.3rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <div className="flex items-center gap-2">
        <span className="inline-flex rounded-full bg-[#198FF0]/14 p-2 text-[#198FF0]">
          <Icon className="size-4" />
        </span>
        <p className="text-sm font-semibold text-[#111111]">{label}</p>
      </div>
      <div className="mt-4 rounded-[1rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm text-[#49536B]">
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
    <div className="rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <div className="flex items-start gap-3">
        <span className="inline-flex rounded-full bg-[#198FF0]/14 p-2 text-[#198FF0]">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold text-[#111111]">{title}</p>
          <div className="mt-3 rounded-[1rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm text-[#49536B]">
            {value}
          </div>
          <div className="mt-4 flex justify-end">
            <Button>{action}</Button>
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
    <section className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 shadow-[0_12px_34px_rgba(114,125,151,0.12)]">
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-lg font-semibold tracking-[-0.03em] text-[#111111]">{title}</p>
        <Badge variant="outline">{items.length}</Badge>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.application_id} className={getAssignmentClassName(item)}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <p className="text-sm font-semibold text-[#111111]">{item.application_display_id}</p>
                </div>
                {showCurrentOwner && item.current_interviewer ? (
                  <p className="text-sm text-[#49536B]">
                    Current interviewer: {item.current_interviewer.name}
                  </p>
                ) : null}
              </div>
              <Button variant="secondary">{actionLabel}</Button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function MetricStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-[#CBD2DE] px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
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
    return "rounded-[1.15rem] border border-[#FFB347]/45 bg-[#FFF1DF] px-4 py-3";
  }

  if (item.source === "reassign") {
    return "rounded-[1.15rem] border border-[#198FF0]/28 bg-[#EAF4FD] px-4 py-3";
  }

  return "rounded-[1.15rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-3";
}

function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}
