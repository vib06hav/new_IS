"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowLeftRight, Mail, Plus, ShieldAlert, UserRound, X } from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import {
  createInterviewer,
  deactivateInterviewer,
  deleteInterviewer,
  fetchApplications,
  fetchInterviewerAssignmentSummary,
  fetchInterviewers,
  reactivateInterviewer,
  saveInterviewerAssignments,
} from "@/lib/api";
import type {
  InterviewerAssignmentSummary,
  InterviewerAssignmentSummaryItem,
  InterviewerListItem,
} from "@/lib/types";
import { AdminShell } from "@/components/layout/AdminShell";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";

type AssignmentSource = "assigned" | "available" | "reassign";
type AssignmentModalItem = InterviewerAssignmentSummaryItem & { source: AssignmentSource };

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-reports-display",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

export default function AdminInterviewersPage() {
  return (
    <AdminShell>
      <AdminInterviewersContent />
    </AdminShell>
  );
}

function AdminInterviewersContent() {
  const [items, setItems] = useState<InterviewerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createForm, setCreateForm] = useState({ name: "", email: "" });
  const [readyPoolCount, setReadyPoolCount] = useState(0);
  const [selectedInterviewer, setSelectedInterviewer] = useState<InterviewerListItem | null>(null);
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [assignmentInterviewer, setAssignmentInterviewer] = useState<InterviewerListItem | null>(null);
  const [assignmentSummary, setAssignmentSummary] = useState<InterviewerAssignmentSummary | null>(null);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assignmentOriginalIds, setAssignmentOriginalIds] = useState<string[]>([]);
  const [stagedAssignedIds, setStagedAssignedIds] = useState<string[]>([]);

  async function loadInterviewers() {
    try {
      const [interviewers, readyApplications] = await Promise.all([
        fetchInterviewers(),
        fetchApplications("READY"),
      ]);
      setItems(interviewers);
      setReadyPoolCount(readyApplications.length);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load interviewers.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadInterviewers();
  }, []);

  async function handleCreate() {
    setCreateSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await createInterviewer({
        name: createForm.name.trim(),
        email: createForm.email.trim(),
      });
      setCreateForm({ name: "", email: "" });
      setCreateOpen(false);
      setMessage("Interviewer invited.");
      await loadInterviewers();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to invite interviewer.");
    } finally {
      setCreateSubmitting(false);
    }
  }

  async function openAssignmentModal(interviewer: InterviewerListItem) {
    setAssignmentInterviewer(interviewer);
    setAssignmentLoading(true);
    setAssignmentSubmitting(false);
    setAssignmentError(null);
    setAssignmentSummary(null);
    setAssignmentOriginalIds([]);
    setStagedAssignedIds([]);
    try {
      const summary = await fetchInterviewerAssignmentSummary(interviewer.id);
      const initialIds = summary.currently_assigned.map((item) => item.application_id);
      setAssignmentSummary(summary);
      setAssignmentOriginalIds(initialIds);
      setStagedAssignedIds(initialIds);
    } catch (loadError) {
      setAssignmentError(loadError instanceof Error ? loadError.message : "Failed to load assignment manager.");
    } finally {
      setAssignmentLoading(false);
    }
  }

  async function handleDeactivate() {
    if (!selectedInterviewer) return;
    if (!window.confirm(`Deactivate ${selectedInterviewer.name}? They will lose app access immediately.`)) return;

    setActionSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await deactivateInterviewer(selectedInterviewer.id);
      setSelectedInterviewer(null);
      setMessage("Interviewer deactivated.");
      await loadInterviewers();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to deactivate interviewer.");
    } finally {
      setActionSubmitting(false);
    }
  }

  async function handleReactivate() {
    if (!selectedInterviewer) return;
    if (!window.confirm(`Reactivate ${selectedInterviewer.name}? They will be able to sign in again.`)) return;

    setActionSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await reactivateInterviewer(selectedInterviewer.id);
      setSelectedInterviewer(null);
      setMessage("Interviewer reactivated.");
      await loadInterviewers();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to reactivate interviewer.");
    } finally {
      setActionSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!selectedInterviewer) return;
    if (
      !window.confirm(
        `Delete ${selectedInterviewer.name}? This only works if they have no assignments or other live references.`,
      )
    ) {
      return;
    }

    setActionSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await deleteInterviewer(selectedInterviewer.id);
      setSelectedInterviewer(null);
      setMessage("Interviewer deleted.");
      await loadInterviewers();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to delete interviewer.");
    } finally {
      setActionSubmitting(false);
    }
  }

  const metrics = useMemo(
    () => ({
      interviewers: items.length,
      activeAssignments: items.reduce((sum, item) => sum + item.active_assignment_count, 0),
      readyPool: readyPoolCount,
    }),
    [items, readyPoolCount],
  );

  const assignmentItems = useMemo(() => {
    if (!assignmentSummary) {
      return {
        byId: new Map<string, AssignmentModalItem>(),
        order: [] as string[],
        originalAssignedSet: new Set<string>(),
      };
    }

    const byId = new Map<string, AssignmentModalItem>();
    const order: string[] = [];

    for (const item of assignmentSummary.currently_assigned) {
      byId.set(item.application_id, { ...item, source: "assigned" });
      order.push(item.application_id);
    }
    for (const item of assignmentSummary.available_to_assign) {
      byId.set(item.application_id, { ...item, source: "available" });
      order.push(item.application_id);
    }
    for (const item of assignmentSummary.available_to_reassign) {
      byId.set(item.application_id, { ...item, source: "reassign" });
      order.push(item.application_id);
    }

    return {
      byId,
      order,
      originalAssignedSet: new Set(assignmentOriginalIds),
    };
  }, [assignmentOriginalIds, assignmentSummary]);

  const stagedAssignedSet = useMemo(() => new Set(stagedAssignedIds), [stagedAssignedIds]);

  const assignmentBuckets = useMemo(() => {
    const currentlyAssigned: AssignmentModalItem[] = [];
    const availableToAssign: AssignmentModalItem[] = [];
    const availableToReassign: AssignmentModalItem[] = [];

    for (const applicationId of assignmentItems.order) {
      const item = assignmentItems.byId.get(applicationId);
      if (!item) continue;

      if (stagedAssignedSet.has(applicationId)) {
        currentlyAssigned.push(item);
        continue;
      }

      if (item.source === "reassign") {
        availableToReassign.push(item);
      } else {
        availableToAssign.push(item);
      }
    }

    return { currentlyAssigned, availableToAssign, availableToReassign };
  }, [assignmentItems.byId, assignmentItems.order, stagedAssignedSet]);

  const stagedChangeCount = useMemo(() => {
    let count = 0;
    const allIds = new Set([...assignmentOriginalIds, ...stagedAssignedIds]);
    for (const applicationId of allIds) {
      const originallyAssigned = assignmentItems.originalAssignedSet.has(applicationId);
      const stagedAssigned = stagedAssignedSet.has(applicationId);
      if (originallyAssigned !== stagedAssigned) count += 1;
    }
    return count;
  }, [assignmentItems.originalAssignedSet, assignmentOriginalIds, stagedAssignedIds, stagedAssignedSet]);

  function addAssignment(applicationId: string) {
    setStagedAssignedIds((current) => (current.includes(applicationId) ? current : [...current, applicationId]));
  }

  function removeAssignment(applicationId: string) {
    setStagedAssignedIds((current) => current.filter((id) => id !== applicationId));
  }

  async function handleAssignmentSave() {
    if (!assignmentInterviewer) return;

    setAssignmentSubmitting(true);
    setAssignmentError(null);
    setMessage(null);
    try {
      const summary = await saveInterviewerAssignments(assignmentInterviewer.id, {
        assigned_application_ids: stagedAssignedIds,
      });
      setAssignmentSummary(summary);
      setAssignmentOriginalIds(summary.currently_assigned.map((item) => item.application_id));
      setStagedAssignedIds(summary.currently_assigned.map((item) => item.application_id));
      setMessage("Assignments updated.");
      await loadInterviewers();
    } catch (saveError) {
      setAssignmentError(saveError instanceof Error ? saveError.message : "Failed to update assignments.");
    } finally {
      setAssignmentSubmitting(false);
    }
  }

  return (
    <div
      className={`${libreFranklin.variable} ${plexSans.variable} space-y-6`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2">
              <div className="h-1.5 w-1.5 rounded-full bg-blue-700" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-blue-900">Access Manager</span>
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tight text-slate-800" style={{ fontFamily: "var(--font-reports-display)" }}>
                Interviewer Manager
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
                Invite interviewers by email, review their local access state, deactivate access when needed, and keep
                assignment management intact. Identity details now come from the authentication provider.
              </p>
            </div>
            <button
              className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              onClick={() => setCreateOpen(true)}
              type="button"
            >
              <Plus className="size-4" />
              Invite interviewer
            </button>
          </div>
        </section>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="mb-3 px-1 text-xs font-bold uppercase tracking-widest text-slate-400">Status totals</p>
          <div className="space-y-2">
            <MetricStrip label="Interviewers" value={metrics.interviewers} />
            <MetricStrip label="Active assignments" value={metrics.activeAssignments} />
            <MetricStrip label="Ready pool" value={metrics.readyPool} />
          </div>
        </div>
      </div>

      {message ? <p className="rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p> : null}
      {error ? <p className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}

      {loading ? (
        <Loader label="Loading interviewers..." />
      ) : items.length === 0 ? (
        <div className="rounded-3xl border border-slate-200 bg-white px-6 py-10 text-center">
          <p className="text-base font-semibold text-slate-900">No interviewers yet.</p>
          <p className="mt-2 text-sm text-slate-600">Invite an interviewer to start assigning applications.</p>
        </div>
      ) : (
        <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item) => (
            <InterviewerCard
              key={item.id}
              item={item}
              onManageAssignments={() => void openAssignmentModal(item)}
              onManageAccess={() => setSelectedInterviewer(item)}
            />
          ))}
        </section>
      )}

      {createOpen ? (
        <CenteredOverlay onClose={() => !createSubmitting && setCreateOpen(false)}>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <SurfaceHeader eyebrow="Invite interviewer" title="New interviewer invite" onClose={() => setCreateOpen(false)} />
            <p className="mt-4 text-sm leading-7 text-slate-600">
              This creates a local access record only. The interviewer activates on first successful AuthKit sign in.
            </p>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <FieldEditor icon={UserRound} label="Display name" value={createForm.name} onChange={(value) => setCreateForm((current) => ({ ...current, name: value }))} />
              <FieldEditor icon={Mail} label="Email" type="email" value={createForm.email} onChange={(value) => setCreateForm((current) => ({ ...current, email: value }))} />
            </div>
            <div className="mt-6 flex justify-end">
              <button
                className="inline-flex items-center justify-center rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
                disabled={createSubmitting || !createForm.name.trim() || !createForm.email.trim()}
                onClick={() => void handleCreate()}
                type="button"
              >
                {createSubmitting ? "Inviting..." : "Save invite"}
              </button>
            </div>
          </div>
        </CenteredOverlay>
      ) : null}

      {selectedInterviewer ? (
        <CenteredOverlay onClose={() => !actionSubmitting && setSelectedInterviewer(null)}>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <SurfaceHeader eyebrow="Access actions" title={selectedInterviewer.name} onClose={() => setSelectedInterviewer(null)} />
            <div className="mt-5 flex items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <InterviewerAvatar item={selectedInterviewer} sizeClassName="size-14" />
              <div className="min-w-0">
                <p className="truncate text-lg font-semibold text-slate-900">{selectedInterviewer.name}</p>
                <p className="truncate text-sm text-slate-600">{selectedInterviewer.email}</p>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
              <p className="text-sm font-semibold text-slate-900">Access status</p>
              <div className="mt-3">
                <AccessBadge status={selectedInterviewer.access_status} />
              </div>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                Email, password, MFA, and avatar are provider-managed. Admin controls here are limited to access state
                and safe deletion.
              </p>
            </div>

            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-3">
                <span className="inline-flex rounded-full bg-red-100 p-2 text-red-700">
                  <ShieldAlert className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-base font-semibold text-red-900">Danger zone</p>
                  <p className="mt-2 text-sm leading-7 text-red-800">
                    Deactivate blocks future sign-in. Delete is only available when this interviewer has no remaining
                    live references.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <button
                      className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-100 disabled:opacity-60"
                      disabled={actionSubmitting}
                      onClick={() =>
                        void (
                          selectedInterviewer.access_status === "deactivated"
                            ? handleReactivate()
                            : handleDeactivate()
                        )
                      }
                      type="button"
                    >
                      {actionSubmitting
                        ? "Processing..."
                        : selectedInterviewer.access_status === "deactivated"
                          ? "Reactivate access"
                          : "Deactivate access"}
                    </button>
                    <button
                      className="inline-flex items-center justify-center rounded-full bg-red-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-800 disabled:opacity-60"
                      disabled={actionSubmitting}
                      onClick={() => void handleDelete()}
                      type="button"
                    >
                      {actionSubmitting ? "Processing..." : "Delete interviewer"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CenteredOverlay>
      ) : null}

      {assignmentInterviewer ? (
        <CenteredOverlay onClose={() => !assignmentSubmitting && setAssignmentInterviewer(null)}>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <SurfaceHeader eyebrow="Assignment buckets" title={`Manage assignments · ${assignmentInterviewer.name}`} onClose={() => setAssignmentInterviewer(null)} />
            <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600">
              Assignment behavior stays exactly the same. This modal is unchanged in spirit; only identity management
              around it has been simplified.
            </p>
            {assignmentLoading ? (
              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10">
                <Loader label="Loading assignment manager..." />
              </div>
            ) : assignmentSummary ? (
              <>
                {assignmentError ? <p className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{assignmentError}</p> : null}
                <div className="mt-6 flex flex-wrap items-center justify-end gap-2">
                  <Badge variant="secondary">{assignmentBuckets.currentlyAssigned.length} staged active</Badge>
                  <Badge variant="outline">{stagedChangeCount} pending change{stagedChangeCount === 1 ? "" : "s"}</Badge>
                </div>
                <div className="mt-6 grid gap-4 xl:grid-cols-3">
                  <AssignmentBucket title="Currently assigned" items={assignmentBuckets.currentlyAssigned} actionLabel="Remove" onAction={removeAssignment} showCurrentOwner={false} />
                  <AssignmentBucket title="Available to assign" items={assignmentBuckets.availableToAssign} actionLabel="Add" onAction={addAssignment} showCurrentOwner={false} />
                  <AssignmentBucket title="Available to reassign" items={assignmentBuckets.availableToReassign} actionLabel="Add" onAction={addAssignment} showCurrentOwner />
                </div>
                <div className="mt-6 flex items-center justify-end gap-3 border-t border-slate-200 pt-5">
                  <button className="rounded-full border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-100" disabled={assignmentSubmitting} onClick={() => setAssignmentInterviewer(null)} type="button">
                    Close
                  </button>
                  <button className="rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60" disabled={assignmentSubmitting || stagedChangeCount === 0} onClick={() => void handleAssignmentSave()} type="button">
                    {assignmentSubmitting ? "Saving..." : `Save changes${stagedChangeCount > 0 ? ` (${stagedChangeCount})` : ""}`}
                  </button>
                </div>
              </>
            ) : (
              <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10 text-center">
                <p className="text-base font-semibold text-slate-900">Assignment manager unavailable.</p>
                <p className="mt-2 text-sm text-slate-600">We couldn’t load the interviewer assignment summary just yet.</p>
              </div>
            )}
          </div>
        </CenteredOverlay>
      ) : null}
    </div>
  );
}

function InterviewerCard({
  item,
  onManageAssignments,
  onManageAccess,
}: {
  item: InterviewerListItem;
  onManageAssignments: () => void;
  onManageAccess: () => void;
}) {
  return (
    <article className="relative rounded-3xl border border-slate-200 bg-white text-slate-900 shadow-[0_10px_30px_rgba(2,12,32,0.05)] transition-all hover:shadow-md">
      <div className="absolute right-4 top-4">
        <div className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-600 border border-blue-100">
          {item.active_assignment_count} active
        </div>
      </div>
      <div className="flex flex-col items-center p-6 text-center">
        <InterviewerAvatar item={item} sizeClassName="size-20" />
        <div className="mt-5 w-full space-y-2">
          <h4 className="truncate text-xl font-black tracking-tight text-slate-800" style={{ fontFamily: "var(--font-reports-display)" }} title={item.name}>
            {item.name}
          </h4>
          <p className="truncate text-xs text-slate-500" title={item.email}>
            {item.email}
          </p>
          <div className="flex justify-center">
            <AccessBadge status={item.access_status} />
          </div>
        </div>

        <div className="mt-6 grid w-full gap-2">
          <button className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-700" onClick={onManageAssignments} type="button">
            <ArrowLeftRight className="size-4" />
            Manage assignments
          </button>
          <button className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:text-blue-700" onClick={onManageAccess} type="button">
            <ShieldAlert className="size-4" />
            Manage access
          </button>
        </div>
      </div>
    </article>
  );
}

function InterviewerAvatar({ item, sizeClassName }: { item: InterviewerListItem; sizeClassName: string }) {
  return (
    <Avatar className={`${sizeClassName} overflow-hidden border border-slate-200 bg-slate-100`}>
      {item.profile_image_url ? <AvatarImage src={item.profile_image_url} alt={`${item.name} profile image`} /> : null}
      <AvatarFallback className="bg-slate-200 text-slate-700">{getInitials(item.name)}</AvatarFallback>
    </Avatar>
  );
}

function CenteredOverlay({ children, onClose }: { children: ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-slate-900/35 px-5 py-8 backdrop-blur-[8px]" onClick={onClose} role="presentation">
      <div className="w-full max-w-[72rem]" onClick={(event) => event.stopPropagation()} role="presentation">
        {children}
      </div>
    </div>
  );
}

function SurfaceHeader({ eyebrow, title, onClose }: { eyebrow: string; title: string; onClose: () => void }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-400">{eyebrow}</p>
        <h2 className="mt-3 text-4xl leading-[0.96] tracking-[-0.06em] text-slate-900" style={{ fontFamily: "var(--font-reports-display)" }}>
          {title}
        </h2>
      </div>
      <button className="grid size-10 place-items-center rounded-full border border-slate-200 bg-slate-50 text-slate-700 transition hover:bg-slate-100" onClick={onClose} type="button">
        <X className="size-4" />
      </button>
    </div>
  );
}

function FieldEditor({
  icon: Icon,
  label,
  value,
  onChange,
  type = "text",
}: {
  icon: typeof UserRound;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 flex items-center gap-2">
        <span className="inline-flex rounded-full bg-blue-50 p-2 text-blue-700">
          <Icon className="size-4" />
        </span>
        <p className="text-sm font-semibold text-slate-900">{label}</p>
      </div>
      <Input label={label} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function AssignmentBucket({
  title,
  items,
  actionLabel,
  onAction,
  showCurrentOwner,
}: {
  title: string;
  items: AssignmentModalItem[];
  actionLabel: string;
  onAction: (applicationId: string) => void;
  showCurrentOwner: boolean;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="text-lg font-semibold tracking-[-0.03em] text-slate-900">{title}</p>
        <Badge variant="outline">{items.length}</Badge>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.application_id} className={getAssignmentClassName(item)}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <p className="text-sm font-semibold text-slate-900">{item.application_display_id}</p>
                </div>
                {showCurrentOwner && item.current_interviewer ? <p className="text-sm text-slate-600">Current interviewer: {item.current_interviewer.name}</p> : null}
              </div>
              <button className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 transition hover:bg-slate-100" onClick={() => onAction(item.application_id)} type="button">
                {actionLabel}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function AccessBadge({ status }: { status: string }) {
  const copy: Record<string, string> = {
    invited: "Invited",
    active: "Active",
    deactivated: "Deactivated",
  };
  const tone =
    status === "active"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : status === "deactivated"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-amber-200 bg-amber-50 text-amber-800";

  return <span className={`rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${tone}`}>{copy[status] ?? status}</span>;
}

function MetricStrip({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-1.5 transition-all hover:bg-white hover:shadow-sm">
      <span className="text-xs font-bold uppercase tracking-widest text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function getAssignmentClassName(item: AssignmentModalItem) {
  if (item.source === "assigned") return "rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3";
  if (item.source === "reassign") return "rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3";
  return "rounded-2xl border border-slate-200 bg-white px-4 py-3";
}

function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}
