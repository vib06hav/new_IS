"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  ChevronLeft,
  ChevronRight,
  KeyRound,
  Mail,
  PencilLine,
  Plus,
  ShieldAlert,
  Stars,
  UserRound,
  X,
} from "lucide-react";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";
import {
  createInterviewer,
  deleteInterviewer,
  fetchApplications,
  fetchInterviewerAssignmentSummary,
  fetchInterviewers,
  saveInterviewerAssignments,
  updateInterviewer,
  updateInterviewerPassword,
} from "@/lib/api";
import type {
  InterviewerAssignmentSummary,
  InterviewerAssignmentSummaryItem,
  InterviewerListItem,
} from "@/lib/types";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AdminShell } from "@/components/layout/AdminShell";

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
  const [selectedInterviewer, setSelectedInterviewer] = useState<InterviewerListItem | null>(null);
  const [assignmentInterviewer, setAssignmentInterviewer] = useState<InterviewerListItem | null>(null);
  const [assignmentSummary, setAssignmentSummary] = useState<InterviewerAssignmentSummary | null>(null);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false);
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assignmentOriginalIds, setAssignmentOriginalIds] = useState<string[]>([]);
  const [stagedAssignedIds, setStagedAssignedIds] = useState<string[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [profileSubmitting, setProfileSubmitting] = useState(false);
  const [accountSubmitting, setAccountSubmitting] = useState(false);
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [removeSubmitting, setRemoveSubmitting] = useState(false);
  const [readyPoolCount, setReadyPoolCount] = useState(0);
  const [createForm, setCreateForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [profileForm, setProfileForm] = useState({ name: "" });
  const [accountForm, setAccountForm] = useState({ email: "" });
  const [passwordForm, setPasswordForm] = useState({ password: "", confirmPassword: "" });


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

  const hasOverlayOpen = createOpen || assignmentInterviewer !== null || selectedInterviewer !== null;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    if (hasOverlayOpen) document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [hasOverlayOpen]);

  function openEditSheet(interviewer: InterviewerListItem) {
    setSelectedInterviewer(interviewer);
    setProfileForm({ name: interviewer.name });
    setAccountForm({ email: interviewer.email });
    setPasswordForm({ password: "", confirmPassword: "" });
    setError(null);
    setMessage(null);
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

  function closeEditSheet() {
    if (profileSubmitting || accountSubmitting || passwordSubmitting || removeSubmitting) return;
    setSelectedInterviewer(null);
  }

  function closeAssignmentModal() {
    if (assignmentSubmitting) return;
    setAssignmentInterviewer(null);
    setAssignmentSummary(null);
    setAssignmentError(null);
    setAssignmentOriginalIds([]);
    setStagedAssignedIds([]);
  }

  async function handleCreate() {
    if (createForm.password !== createForm.confirmPassword) {
      setError("Create password confirmation does not match.");
      return;
    }

    const interviewerName = createForm.name.trim();
    setCreateSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await createInterviewer({
        name: interviewerName,
        email: createForm.email.trim(),
        password: createForm.password,
      });
      setCreateOpen(false);
      setCreateForm({ name: "", email: "", password: "", confirmPassword: "" });
      setMessage("Interviewer created.");
      await loadInterviewers();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create interviewer.");
    } finally {
      setCreateSubmitting(false);
    }
  }

  async function handleProfileUpdate() {
    if (!selectedInterviewer) return;
    const nextName = profileForm.name.trim();
    if (!window.confirm(`Change interviewer name to "${nextName}"?`)) return;

    setProfileSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await updateInterviewer(selectedInterviewer.id, {
        name: nextName,
        email: selectedInterviewer.email,
      });
      setMessage("Interviewer name updated.");
      await loadInterviewers();
      setSelectedInterviewer((current) => (current ? { ...current, name: nextName } : current));
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Failed to update interviewer name.");
    } finally {
      setProfileSubmitting(false);
    }
  }

  async function handleEmailUpdate() {
    if (!selectedInterviewer) return;
    const nextEmail = accountForm.email.trim();
    if (!window.confirm(`Change interviewer email to "${nextEmail}"?`)) return;

    setAccountSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await updateInterviewer(selectedInterviewer.id, {
        name: selectedInterviewer.name,
        email: nextEmail,
      });
      setMessage("Interviewer email updated.");
      await loadInterviewers();
      setSelectedInterviewer((current) => (current ? { ...current, email: nextEmail } : current));
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Failed to update interviewer email.");
    } finally {
      setAccountSubmitting(false);
    }
  }

  async function handlePasswordUpdate() {
    if (!selectedInterviewer) return;
    if (passwordForm.password !== passwordForm.confirmPassword) {
      setError("Password confirmation does not match.");
      return;
    }
    if (!window.confirm(`Reset the password for ${selectedInterviewer.name}?`)) return;

    setPasswordSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await updateInterviewerPassword(selectedInterviewer.id, {
        new_password: passwordForm.password,
      });
      setPasswordForm({ password: "", confirmPassword: "" });
      setMessage("Interviewer password updated.");
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Failed to update interviewer password.");
    } finally {
      setPasswordSubmitting(false);
    }
  }

  async function handleRemove() {
    if (!selectedInterviewer) return;
    if (
      !window.confirm(
        `Remove ${selectedInterviewer.name}? This action is irreversible and only works when they have no active assignments.`,
      )
    ) {
      return;
    }

    setRemoveSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await deleteInterviewer(selectedInterviewer.id);
      setSelectedInterviewer(null);
      setMessage("Interviewer removed.");
      await loadInterviewers();
    } catch (removeError) {
      const detail = removeError instanceof Error ? removeError.message : "Failed to remove interviewer.";
      setError(detail);
    } finally {
      setRemoveSubmitting(false);
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

  const createPasswordMismatch =
    Boolean(createForm.password || createForm.confirmPassword) &&
    createForm.password !== createForm.confirmPassword;
  const updatePasswordMismatch =
    Boolean(passwordForm.password || passwordForm.confirmPassword) &&
    passwordForm.password !== passwordForm.confirmPassword;
  const profileChanged = selectedInterviewer ? profileForm.name.trim() !== selectedInterviewer.name : false;
  const emailChanged = selectedInterviewer ? accountForm.email.trim() !== selectedInterviewer.email : false;

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

      if (item.source === "assigned") {
        availableToAssign.push(item);
      } else if (item.source === "reassign") {
        availableToReassign.push(item);
      } else {
        availableToAssign.push(item);
      }
    }

    return {
      currentlyAssigned,
      availableToAssign,
      availableToReassign,
    };
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

  const stagedDraftReassignments = useMemo(
    () =>
      assignmentBuckets.currentlyAssigned.filter(
        (item) =>
          item.source === "reassign" &&
          item.status === "DRAFT" &&
          stagedAssignedSet.has(item.application_id),
      ),
    [assignmentBuckets.currentlyAssigned, stagedAssignedSet],
  );

  function addAssignment(applicationId: string) {
    setStagedAssignedIds((current) => (current.includes(applicationId) ? current : [...current, applicationId]));
  }

  function removeAssignment(applicationId: string) {
    setStagedAssignedIds((current) => current.filter((id) => id !== applicationId));
  }

  async function handleAssignmentSave() {
    if (!assignmentInterviewer) return;
    if (
      stagedDraftReassignments.length > 0 &&
      !window.confirm(
        `${stagedDraftReassignments.length} drafted report(s) will be reassigned. Their current drafts will be discarded and reset to ASSIGNED. Continue?`,
      )
    ) {
      return;
    }

    const reassignedApplications = assignmentBuckets.currentlyAssigned.filter(
      (item) =>
        item.source === "reassign" &&
        !assignmentItems.originalAssignedSet.has(item.application_id) &&
        stagedAssignedSet.has(item.application_id),
    );

    setAssignmentSubmitting(true);
    setAssignmentError(null);
    setMessage(null);
    try {
      const summary = await saveInterviewerAssignments(assignmentInterviewer.id, {
        assigned_application_ids: stagedAssignedIds,
      });
      setAssignmentInterviewer({ ...assignmentInterviewer, active_assignment_count: summary.active_assignment_count });
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
      <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_20rem] gap-6 items-stretch">
            <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
              <div className="relative flex flex-col h-full justify-between gap-6">
                <div className="space-y-3">
                  <h1
                    className="max-w-4xl text-3xl md:text-4xl font-black tracking-tight text-slate-800 leading-none"
                    style={{ fontFamily: "var(--font-reports-display)" }}
                  >
                    Interviewer Manager
                  </h1>
                  <p className="max-w-3xl text-sm text-slate-600 leading-relaxed">
                    Review the active interviewer roster, open assignment buckets when work needs to move, and manage
                    interviewer account details without leaving the page context.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    className="inline-flex items-center gap-2 rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-700 hover:shadow-md"
                    onClick={() => setCreateOpen(true)}
                    type="button"
                  >
                    <Plus className="size-4" />
                    Add interviewer
                  </button>
                </div>
              </div>
            </section>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col">
              <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mb-3 px-1">Status totals</p>
              <div className="flex flex-col justify-between flex-1">
                <MetricStrip label="Interviewers" value={metrics.interviewers} />
                <MetricStrip label="Active assignments" value={metrics.activeAssignments} />
                <MetricStrip label="Ready pool" value={metrics.readyPool} />
              </div>
            </div>
          </div>

          {message ? <p className="rounded-[1.2rem] border border-[#198FF0]/35 bg-[#EAF4FD] px-4 py-3 text-sm text-[#24527A]">{message}</p> : null}
          {error ? <p className="rounded-[1.2rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] px-4 py-3 text-sm text-[#9A315A]">{error}</p> : null}

          {loading ? (
            <Loader label="Loading interviewers..." />
          ) : items.length === 0 ? (
            <div className="rounded-[1.9rem] border border-[#727D97] bg-[#F7F7F1] px-6 py-10 text-center">
              <p className="text-base font-semibold text-[#111111]">No interviewers yet.</p>
              <p className="mt-2 text-sm text-[#5F6C86]">Add an interviewer to start assigning applications.</p>
            </div>
          ) : (
            <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {items.map((item) => (
                <InterviewerCard
                  key={item.id}
                  item={item}
                  onEdit={() => openEditSheet(item)}
                  onManageAssignments={() => void openAssignmentModal(item)}
                />
              ))}
            </section>
          )}
        </div>

      {createOpen ? (
        <CenteredOverlay onClose={() => !createSubmitting && setCreateOpen(false)}>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <SurfaceHeader eyebrow="Create interviewer" title="Add interviewer" onClose={() => setCreateOpen(false)} />
            <p className="mt-4 max-w-2xl text-base text-slate-600 leading-relaxed">
              Create a new interviewer account with the same core fields used in the live frontend.
            </p>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <FieldEditor icon={UserRound} label="Display name" value={createForm.name} onChange={(value) => setCreateForm((current) => ({ ...current, name: value }))} />
              <FieldEditor icon={Mail} label="Email" type="email" value={createForm.email} onChange={(value) => setCreateForm((current) => ({ ...current, email: value }))} />
              <FieldEditor icon={KeyRound} label="Password" type="password" value={createForm.password} onChange={(value) => setCreateForm((current) => ({ ...current, password: value }))} />
              <FieldEditor icon={KeyRound} label="Confirm password" type="password" value={createForm.confirmPassword} onChange={(value) => setCreateForm((current) => ({ ...current, confirmPassword: value }))} />
            </div>
            {createPasswordMismatch ? (
              <p className="mt-4 rounded-[1rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] px-4 py-3 text-sm text-[#9A315A]">
                Passwords must match before the interviewer can be created.
              </p>
            ) : null}
            <div className="mt-6 flex justify-end">
              <button
                className="inline-flex items-center justify-center rounded-full bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-700 disabled:opacity-60"
                disabled={createSubmitting || !createForm.name.trim() || !createForm.email.trim() || !createForm.password || createPasswordMismatch}
                onClick={() => void handleCreate()}
                type="button"
              >
                {createSubmitting ? "Creating..." : "Create interviewer"}
              </button>
            </div>
          </div>
        </CenteredOverlay>
      ) : null}

      {assignmentInterviewer ? (
        <CenteredOverlay onClose={closeAssignmentModal}>
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <SurfaceHeader eyebrow="Assignment buckets" title={`Manage assignments · ${assignmentInterviewer.name}`} onClose={closeAssignmentModal} />
            <p className="mt-4 max-w-3xl text-sm leading-7 text-[#49536B]">
              Keep the bucket logic from the real frontend, but present it inside the same mock system as the other admin pages.
            </p>
            {assignmentLoading ? (
              <div className="mt-6 rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] px-4 py-10">
                <Loader label="Loading assignment manager..." />
              </div>
            ) : assignmentSummary ? (
              <>
                {assignmentError ? <p className="mt-6 rounded-[1.2rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] px-4 py-3 text-sm text-[#9A315A]">{assignmentError}</p> : null}
                <div className="mt-6 flex flex-wrap items-center justify-end gap-2">
                  <Badge variant="secondary">{assignmentBuckets.currentlyAssigned.length} staged active</Badge>
                  <Badge variant="outline">{stagedChangeCount} pending change{stagedChangeCount === 1 ? "" : "s"}</Badge>
                </div>
                <div className="mt-6 grid gap-4 xl:grid-cols-3">
                  <AssignmentBucket title="Currently assigned" items={assignmentBuckets.currentlyAssigned} actionLabel="Remove" onAction={(applicationId) => removeAssignment(applicationId)} showCurrentOwner={false} />
                  <AssignmentBucket title="Available to assign" items={assignmentBuckets.availableToAssign} actionLabel="Add" onAction={(applicationId) => addAssignment(applicationId)} showCurrentOwner={false} />
                  <AssignmentBucket title="Available to reassign" items={assignmentBuckets.availableToReassign} actionLabel="Add" onAction={(applicationId) => addAssignment(applicationId)} showCurrentOwner />
                </div>
                <div className="mt-6 flex items-center justify-end gap-3 border-t border-[#727D97]/45 pt-5">
                  <button className="inline-flex items-center justify-center rounded-full border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm font-semibold text-[#111111] transition hover:bg-[#E6E9F0]" disabled={assignmentSubmitting} onClick={closeAssignmentModal} type="button">Close</button>
                  <button className="inline-flex items-center justify-center rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-60" disabled={assignmentSubmitting || stagedChangeCount === 0} onClick={() => void handleAssignmentSave()} type="button">
                    {assignmentSubmitting ? "Saving..." : `Save changes${stagedChangeCount > 0 ? ` (${stagedChangeCount})` : ""}`}
                  </button>
                </div>
              </>
            ) : (
              <div className="mt-6 rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] px-4 py-10 text-center">
                <p className="text-base font-semibold text-[#111111]">Assignment manager unavailable.</p>
                <p className="mt-2 text-sm text-[#5F6C86]">We couldn’t load the interviewer assignment summary just yet.</p>
              </div>
            )}
          </div>
        </CenteredOverlay>
      ) : null}

      {selectedInterviewer ? (
        <FloatingSheet onClose={closeEditSheet}>
          <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[#F7F7F1] shadow-[0_28px_80px_rgba(114,125,151,0.28)]">
            <div className="interviewer-sheet-scroll max-h-[calc(100vh-3rem)] overflow-y-auto px-6 py-6">
              <SurfaceHeader eyebrow="Edit interviewer" title={selectedInterviewer.name} onClose={closeEditSheet} />
              <div className="mt-5 flex items-center gap-4 rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-4">
                <InterviewerAvatar item={selectedInterviewer} sizeClassName="size-14" />
                <div className="min-w-0">
                  <p className="truncate text-lg font-semibold text-[#111111]">{selectedInterviewer.name}</p>
                  <p className="truncate text-sm text-[#49536B]">{selectedInterviewer.email}</p>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <EditSection icon={UserRound} title="Display name">
                  <Input label="Display name" value={profileForm.name} onChange={(event) => setProfileForm({ name: event.target.value })} />
                  <div className="mt-4 flex justify-end">
                    <button className="inline-flex items-center justify-center rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-60" disabled={profileSubmitting || !profileForm.name.trim() || !profileChanged} onClick={() => void handleProfileUpdate()} type="button">
                      {profileSubmitting ? "Saving..." : "Save name"}
                    </button>
                  </div>
                </EditSection>

                <EditSection icon={Mail} title="Email">
                  <Input label="Email" type="email" value={accountForm.email} onChange={(event) => setAccountForm({ email: event.target.value })} />
                  <div className="mt-4 flex justify-end">
                    <button className="inline-flex items-center justify-center rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-60" disabled={accountSubmitting || !accountForm.email.trim() || !emailChanged} onClick={() => void handleEmailUpdate()} type="button">
                      {accountSubmitting ? "Saving..." : "Update email"}
                    </button>
                  </div>
                </EditSection>

                <EditSection icon={KeyRound} title="Password">
                  <Input label="New password" type="password" minLength={8} value={passwordForm.password} onChange={(event) => setPasswordForm((current) => ({ ...current, password: event.target.value }))} />
                  <Input label="Confirm new password" type="password" minLength={8} value={passwordForm.confirmPassword} onChange={(event) => setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))} />
                  {updatePasswordMismatch ? <p className="mt-3 rounded-[1rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] px-4 py-3 text-sm text-[#9A315A]">Passwords must match before the update can be confirmed.</p> : null}
                  <div className="mt-4 flex justify-end">
                    <button className="inline-flex items-center justify-center rounded-full bg-[#111111] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#2B3444] disabled:cursor-not-allowed disabled:opacity-60" disabled={passwordSubmitting || !passwordForm.password || updatePasswordMismatch} onClick={() => void handlePasswordUpdate()} type="button">
                      {passwordSubmitting ? "Saving..." : "Change password"}
                    </button>
                  </div>
                </EditSection>
              </div>

              <div className="mt-6 rounded-[1.4rem] border border-[#FF6B9D]/35 bg-[#FFE7F0] p-4">
                <div className="flex items-start gap-3">
                  <span className="inline-flex rounded-full bg-[#FF6B9D]/18 p-2 text-[#9A315A]">
                    <ShieldAlert className="size-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-base font-semibold text-[#7F2247]">Danger zone</p>
                    <p className="mt-2 text-sm leading-6 text-[#9A315A]">Removal fails if this interviewer still has active assignments.</p>
                    <div className="mt-4">
                      <button className="inline-flex items-center justify-center rounded-full bg-[#AF3030] px-4 py-3 text-sm font-semibold text-[#F7F7F1] transition hover:bg-[#932626] disabled:cursor-not-allowed disabled:opacity-60" disabled={removeSubmitting} onClick={() => void handleRemove()} type="button">
                        {removeSubmitting ? "Removing..." : "Remove interviewer"}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </FloatingSheet>
      ) : null}

      <style jsx global>{`
        .interviewer-sheet-scroll {
          scrollbar-width: thin;
          scrollbar-color: #8a94a6 transparent;
          scrollbar-gutter: stable;
        }
        .interviewer-sheet-scroll::-webkit-scrollbar { width: 12px; }
        .interviewer-sheet-scroll::-webkit-scrollbar-button { display: none; height: 0; width: 0; }
        .interviewer-sheet-scroll::-webkit-scrollbar-track { background: transparent; margin: 16px 0; }
        .interviewer-sheet-scroll::-webkit-scrollbar-thumb {
          border: 3px solid transparent;
          border-radius: 999px;
          background-clip: padding-box;
          background-color: #8a94a6;
        }
        .interviewer-sheet-scroll::-webkit-scrollbar-thumb:hover { background-color: #727d97; }
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
    <article className="relative rounded-3xl border border-slate-200 bg-white text-slate-900 shadow-[0_10px_30px_rgba(2,12,32,0.05)] transition-all hover:shadow-md">
      <div className="absolute top-4 right-4">
        <div className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-600 border border-blue-100">
          {item.active_assignment_count} active
        </div>
      </div>
      <div className="flex flex-col items-center p-6 text-center">
        <InterviewerAvatar item={item} sizeClassName="size-20" />
        
        <div className="mt-5 w-full space-y-1">
          <h4 
            className="truncate text-xl font-black tracking-tight text-slate-800" 
            style={{ fontFamily: "var(--font-reports-display)" }}
            title={item.name}
          >
            {item.name}
          </h4>
          <p className="truncate text-xs text-slate-500" title={item.email}>{item.email}</p>
        </div>

        <div className="mt-6 w-full grid gap-2">
          <button className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-blue-700" onClick={onManageAssignments} type="button">
            <ArrowLeftRight className="size-4" />
            Manage assignments
          </button>
          <button className="inline-flex items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:border-blue-300 hover:text-blue-700" onClick={onEdit} type="button">
            <PencilLine className="size-4" />
            Edit interviewer
          </button>
        </div>
      </div>
    </article>
  );
}

function InterviewerAvatar({ item, sizeClassName }: { item: InterviewerListItem; sizeClassName: string }) {
  return (
    <Avatar className={`${sizeClassName} overflow-hidden border border-[#727D97] bg-[#E6E9F0]`}>
      {item.profile_image_url ? <AvatarImage src={item.profile_image_url} alt={`${item.name} profile image`} /> : null}
      <AvatarFallback className="bg-[#AAB4C8] text-[#111111]">{getInitials(item.name)}</AvatarFallback>
    </Avatar>
  );
}

function CenteredOverlay({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 grid place-items-center bg-[#111111]/42 px-5 py-8 backdrop-blur-[10px]" onClick={onClose} role="presentation">
      <div className="w-full max-w-[72rem]" onClick={(event) => event.stopPropagation()} role="presentation">
        {children}
      </div>
    </div>
  );
}

function FloatingSheet({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 overflow-y-auto bg-[#111111]/34 backdrop-blur-[8px]" onClick={onClose} role="presentation">
      <div className="flex min-h-screen justify-end p-4 md:p-6">
        <div className="w-full max-w-[34rem] self-start" onClick={(event) => event.stopPropagation()} role="presentation">
          {children}
        </div>
      </div>
    </div>
  );
}

function SurfaceHeader({ eyebrow, title, onClose }: { eyebrow: string; title: string; onClose: () => void }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">{eyebrow}</p>
        <h2 className="mt-3 text-[2.4rem] leading-[0.96] tracking-[-0.06em] text-[#111111]" style={{ fontFamily: "var(--font-reports-cormorant)" }}>
          {title}
        </h2>
      </div>
      <button className="grid size-10 place-items-center rounded-full border border-[#727D97] bg-[#E6E9F0] text-[#111111] transition hover:bg-[#D8DBE2]" onClick={onClose} type="button">
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
    <div className="rounded-[1.3rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <div className="mb-4 flex items-center gap-2">
        <span className="inline-flex rounded-full bg-[#198FF0]/14 p-2 text-[#198FF0]">
          <Icon className="size-4" />
        </span>
        <p className="text-sm font-semibold text-[#111111]">{label}</p>
      </div>
      <Input label={label} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function EditSection({ icon: Icon, title, children }: { icon: typeof UserRound; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <div className="mb-4 flex items-start gap-3">
        <span className="inline-flex rounded-full bg-[#198FF0]/14 p-2 text-[#198FF0]">
          <Icon className="size-4" />
        </span>
        <p className="text-base font-semibold text-[#111111]">{title}</p>
      </div>
      <div className="space-y-3">{children}</div>
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
                {showCurrentOwner && item.current_interviewer ? <p className="text-sm text-[#49536B]">Current interviewer: {item.current_interviewer.name}</p> : null}
              </div>
              <button className="inline-flex items-center justify-center rounded-full border border-[#727D97] bg-[#F7F7F1] px-3 py-2 text-sm font-semibold text-[#111111] transition hover:bg-[#E6E9F0]" onClick={() => onAction(item.application_id)} type="button">
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
    <div className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-1.5 transition-all hover:bg-white hover:shadow-sm">
      <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">{label}</span>
      <span className="text-xs font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function getAssignmentClassName(item: AssignmentModalItem) {
  if (item.source === "assigned") return "rounded-[1.15rem] border border-[#FFB347]/45 bg-[#FFF1DF] px-4 py-3";
  if (item.source === "reassign") return "rounded-[1.15rem] border border-[#198FF0]/28 bg-[#EAF4FD] px-4 py-3";
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
