"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  KeyRound,
  Mail,
  PencilLine,
  Plus,
  ShieldAlert,
  UserRound,
} from "lucide-react";
import {
  createInterviewer,
  deleteInterviewer,
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
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { AdminShell } from "@/components/layout/AdminShell";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogDrawerContent,
  DialogHeader,
  DialogTitle,
} from "@/components/shadcn/dialog";

type AssignmentSource = "assigned" | "available" | "reassign";
type AssignmentModalItem = InterviewerAssignmentSummaryItem & { source: AssignmentSource };

export default function AdminInterviewersPage() {
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
  const [createForm, setCreateForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [profileForm, setProfileForm] = useState({ name: "" });
  const [accountForm, setAccountForm] = useState({ email: "" });
  const [passwordForm, setPasswordForm] = useState({ password: "", confirmPassword: "" });

  async function loadInterviewers() {
    try {
      const data = await fetchInterviewers();
      setItems(data);
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

  function openManageDrawer(interviewer: InterviewerListItem) {
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

  function closeManageDrawer() {
    if (profileSubmitting || accountSubmitting || passwordSubmitting || removeSubmitting) {
      return;
    }
    setSelectedInterviewer(null);
  }

  function closeAssignmentModal() {
    if (assignmentSubmitting) {
      return;
    }
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

    setCreateSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await createInterviewer({
        name: createForm.name.trim(),
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
    if (!window.confirm(`Change interviewer name to "${profileForm.name.trim()}"?`)) return;

    setProfileSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await updateInterviewer(selectedInterviewer.id, {
        name: profileForm.name.trim(),
        email: selectedInterviewer.email,
      });
      setMessage("Interviewer name updated.");
      await loadInterviewers();
      setSelectedInterviewer((current) =>
        current ? { ...current, name: profileForm.name.trim() } : current,
      );
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Failed to update interviewer name.");
    } finally {
      setProfileSubmitting(false);
    }
  }

  async function handleEmailUpdate() {
    if (!selectedInterviewer) return;
    if (!window.confirm(`Change interviewer email to "${accountForm.email.trim()}"?`)) return;

    setAccountSubmitting(true);
    setMessage(null);
    setError(null);
    try {
      await updateInterviewer(selectedInterviewer.id, {
        name: selectedInterviewer.name,
        email: accountForm.email.trim(),
      });
      setMessage("Interviewer email updated.");
      await loadInterviewers();
      setSelectedInterviewer((current) =>
        current ? { ...current, email: accountForm.email.trim() } : current,
      );
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
      setError(removeError instanceof Error ? removeError.message : "Failed to remove interviewer.");
    } finally {
      setRemoveSubmitting(false);
    }
  }

  const metrics = useMemo(
    () => ({
      interviewers: items.length,
      activeAssignments: items.reduce((sum, item) => sum + item.active_assignment_count, 0),
    }),
    [items],
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
        continue;
      }

      if (item.source === "reassign") {
        availableToReassign.push(item);
        continue;
      }

      availableToAssign.push(item);
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
      if (originallyAssigned !== stagedAssigned) {
        count += 1;
      }
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

    setAssignmentSubmitting(true);
    setAssignmentError(null);
    setMessage(null);
    try {
      const summary = await saveInterviewerAssignments(assignmentInterviewer.id, {
        assigned_application_ids: stagedAssignedIds,
      });
      const refreshedInterviewer = {
        ...assignmentInterviewer,
        active_assignment_count: summary.active_assignment_count,
      };
      setAssignmentInterviewer(refreshedInterviewer);
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
    <AdminShell>
      <div className="space-y-6">
        <section className="hero-panel p-6">
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr] xl:items-start">
            <div className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">People management</p>
                  <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Interviewer Manager</h1>
                  <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                    Review the active roster, manage ownership without leaving the page, and keep identity edits separate from assignment operations.
                  </p>
                </div>
                <Button className="shrink-0" onClick={() => setCreateOpen(true)}>
                  <Plus className="size-4" />
                  Add interviewer
                </Button>
              </div>
            </div>
            <div className="metric-strip sm:grid-cols-2 xl:self-start">
              <MetricCard label="Interviewers" value={String(metrics.interviewers)} />
              <MetricCard label="Active assignments" value={String(metrics.activeAssignments)} />
            </div>
          </div>
        </section>

        {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading interviewers..." />
        ) : items.length === 0 ? (
          <EmptyState title="No interviewers yet." description="Add an interviewer to start assigning applications." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {items.map((item) => (
              <article
                key={item.id}
                className="fade-rise flex h-full flex-col gap-4 rounded-[1.6rem] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.92),rgba(239,246,255,0.82),rgba(233,225,255,0.6))] p-5 shadow-[0_18px_38px_rgba(148,163,184,0.12)]"
              >
                <div className="flex min-w-0 items-center gap-4">
                  <Avatar size="lg">
                    <AvatarFallback>{getInitials(item.name)}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 space-y-1">
                    <p className="display-font text-lg font-semibold text-[color:var(--ink)]">{item.name}</p>
                    <p className="truncate text-sm text-[color:var(--muted)]">{item.email}</p>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/75 bg-white/70 px-4 py-3 text-sm shadow-sm">
                  <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Active assignments</p>
                  <p className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">
                    {item.active_assignment_count}
                  </p>
                </div>

                <div className="mt-auto grid gap-2">
                  <Button className="w-full min-w-0 justify-center" variant="secondary" onClick={() => void openAssignmentModal(item)}>
                    <ArrowLeftRight className="size-4" />
                    Manage assignments
                  </Button>
                  <Button className="w-full min-w-0 justify-center" variant="outline" onClick={() => openManageDrawer(item)}>
                    <PencilLine className="size-4" />
                    Edit interviewer
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[color:var(--muted)]">New interviewer</p>
              <DialogTitle>Add interviewer</DialogTitle>
              <DialogDescription>Create a new interviewer account without leaving the roster.</DialogDescription>
            </DialogHeader>

            <div className="mt-6 space-y-4">
              <Input label="Name" value={createForm.name} onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))} />
              <Input label="Email" type="email" value={createForm.email} onChange={(event) => setCreateForm((current) => ({ ...current, email: event.target.value }))} />
              <Input
                label="Password"
                type="password"
                minLength={8}
                value={createForm.password}
                onChange={(event) => setCreateForm((current) => ({ ...current, password: event.target.value }))}
              />
              <Input
                label="Confirm password"
                type="password"
                minLength={8}
                value={createForm.confirmPassword}
                onChange={(event) => setCreateForm((current) => ({ ...current, confirmPassword: event.target.value }))}
              />
              {createPasswordMismatch ? (
                <p className="text-sm text-red-700">Passwords must match before the interviewer can be created.</p>
              ) : null}
              <div className="flex justify-end">
                <Button
                  disabled={
                    createSubmitting ||
                    !createForm.name.trim() ||
                    !createForm.email.trim() ||
                    !createForm.password ||
                    createPasswordMismatch
                  }
                  onClick={() => void handleCreate()}
                >
                  {createSubmitting ? "Creating..." : "Create interviewer"}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={assignmentInterviewer !== null} onOpenChange={(open) => !open && closeAssignmentModal()}>
          <DialogContent className="max-w-[72rem] overflow-hidden p-0 sm:p-0">
            <div className="flex max-h-[min(88dvh,56rem)] flex-col">
              <div className="border-b border-white/80 px-6 py-6 sm:px-7">
                <DialogHeader>
                  <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[color:var(--muted)]">Assignment manager</p>
                  <DialogTitle>{assignmentInterviewer ? `Manage assignments for ${assignmentInterviewer.name}` : "Manage assignments"}</DialogTitle>
                  <DialogDescription>
                    Stage assignment changes across three buckets, then save once when the mix looks right. Published reports never appear here.
                  </DialogDescription>
                </DialogHeader>
              </div>

              {assignmentLoading ? (
                <div className="px-6 py-10 sm:px-7">
                  <Loader label="Loading assignment manager..." />
                </div>
              ) : assignmentSummary && assignmentInterviewer ? (
                <>
                  <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 sm:px-7">
                    <div className="space-y-5">
                      {assignmentError ? (
                        <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{assignmentError}</p>
                      ) : null}

                      <div className="flex flex-wrap items-center justify-end gap-2">
                        <Badge variant="secondary">{assignmentBuckets.currentlyAssigned.length} staged active</Badge>
                        <Badge variant="outline">{stagedChangeCount} pending change{stagedChangeCount === 1 ? "" : "s"}</Badge>
                      </div>

                      <div className="grid min-h-0 gap-4 xl:grid-cols-3">
                        <AssignmentBucket
                          title="Currently assigned"
                          description=""
                          items={assignmentBuckets.currentlyAssigned}
                          emptyTitle="No active reports here."
                          emptyDescription="Use the right-hand lists to add new work or pull reports from another interviewer."
                          actionLabel="Remove"
                          onAction={(applicationId) => removeAssignment(applicationId)}
                          className="xl:h-[28rem]"
                          showCurrentOwner
                        />

                        <AssignmentBucket
                          title="Available to assign"
                          description=""
                          items={assignmentBuckets.availableToAssign}
                          emptyTitle="Nothing ready right now."
                          emptyDescription="READY reports will appear here when they are unassigned."
                          actionLabel="Add"
                          onAction={(applicationId) => addAssignment(applicationId)}
                          className="xl:h-[28rem]"
                          listClassName="xl:max-h-[18.5rem]"
                        />

                        <AssignmentBucket
                          title="Available to reassign"
                          description=""
                          items={assignmentBuckets.availableToReassign}
                          emptyTitle="No other owned reports available."
                          emptyDescription="ASSIGNED and DRAFT work from other interviewers will show up here."
                          actionLabel="Add"
                          onAction={(applicationId) => addAssignment(applicationId)}
                          showCurrentOwner
                          className="xl:h-[28rem]"
                          listClassName="xl:max-h-[18.5rem]"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-white/80 px-6 py-4 sm:px-7">
                    <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                      <Button variant="secondary" disabled={assignmentSubmitting} onClick={closeAssignmentModal}>
                        Close
                      </Button>
                      <Button disabled={assignmentSubmitting || stagedChangeCount === 0} onClick={() => void handleAssignmentSave()}>
                        {assignmentSubmitting ? "Saving..." : `Save changes${stagedChangeCount > 0 ? ` (${stagedChangeCount})` : ""}`}
                      </Button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="px-6 py-6 sm:px-7">
                  <EmptyState
                    title="Assignment manager unavailable."
                    description="We couldn’t load the interviewer assignment summary just yet."
                  />
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        <Dialog open={selectedInterviewer !== null} onOpenChange={(open) => !open && closeManageDrawer()}>
          <DialogDrawerContent>
            {selectedInterviewer ? (
              <div className="space-y-8">
                <DialogHeader className="space-y-3 pr-12">
                  <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[color:var(--muted)]">Manage interviewer</p>
                  <DialogTitle>{selectedInterviewer.name}</DialogTitle>
                  <DialogDescription>
                    Update account details carefully. Identity, security, and removal are kept behind this drawer instead of the roster itself.
                  </DialogDescription>
                </DialogHeader>

                <section className="rounded-[1.4rem] border border-white/80 bg-white/72 p-5 shadow-sm">
                  <div className="flex items-center gap-4">
                    <Avatar size="lg">
                      <AvatarFallback>{getInitials(selectedInterviewer.name)}</AvatarFallback>
                    </Avatar>
                    <div className="min-w-0 flex-1">
                      <p className="display-font text-lg font-semibold text-[color:var(--ink)]">{selectedInterviewer.name}</p>
                      <p className="truncate text-sm text-[color:var(--muted)]">{selectedInterviewer.email}</p>
                    </div>
                    <Badge variant="secondary">{selectedInterviewer.active_assignment_count} active</Badge>
                  </div>
                </section>

                <DrawerSection
                  icon={<UserRound className="size-4" />}
                  title="Profile"
                  description="Name is the only profile field editable from this section."
                >
                  <Input
                    label="Name"
                    value={profileForm.name}
                    onChange={(event) => setProfileForm({ name: event.target.value })}
                  />
                  <div className="flex justify-end">
                    <Button disabled={profileSubmitting || !profileForm.name.trim() || !profileChanged} onClick={() => void handleProfileUpdate()}>
                      {profileSubmitting ? "Saving..." : "Save name"}
                    </Button>
                  </div>
                </DrawerSection>

                <DrawerSection
                  icon={<Mail className="size-4" />}
                  title="Account"
                  description="Email changes require explicit confirmation because they affect how the interviewer signs in."
                >
                  <Input
                    label="Email"
                    type="email"
                    value={accountForm.email}
                    onChange={(event) => setAccountForm({ email: event.target.value })}
                  />
                  <div className="flex justify-end">
                    <Button disabled={accountSubmitting || !accountForm.email.trim() || !emailChanged} onClick={() => void handleEmailUpdate()}>
                      {accountSubmitting ? "Saving..." : "Update email"}
                    </Button>
                  </div>
                </DrawerSection>

                <DrawerSection
                  icon={<KeyRound className="size-4" />}
                  title="Security"
                  description="Admin-triggered password change requires a matching confirmation before it can be submitted."
                >
                  <Input
                    label="New password"
                    type="password"
                    minLength={8}
                    value={passwordForm.password}
                    onChange={(event) => setPasswordForm((current) => ({ ...current, password: event.target.value }))}
                  />
                  <Input
                    label="Confirm new password"
                    type="password"
                    minLength={8}
                    value={passwordForm.confirmPassword}
                    onChange={(event) => setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))}
                  />
                  {updatePasswordMismatch ? (
                    <p className="text-sm text-red-700">Passwords must match before the update can be confirmed.</p>
                  ) : null}
                  <div className="flex justify-end">
                    <Button
                      disabled={passwordSubmitting || !passwordForm.password || updatePasswordMismatch}
                      onClick={() => void handlePasswordUpdate()}
                    >
                      {passwordSubmitting ? "Saving..." : "Change password"}
                    </Button>
                  </div>
                </DrawerSection>

                <section className="rounded-[1.4rem] border border-red-200 bg-red-50/88 p-5 shadow-sm">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 inline-flex rounded-full bg-red-100 p-2 text-red-700">
                      <ShieldAlert className="size-4" />
                    </span>
                    <div className="min-w-0 flex-1 space-y-3">
                      <div>
                        <p className="text-lg font-semibold text-red-900">Danger zone</p>
                        <p className="mt-1 text-sm leading-6 text-red-800">
                          Removing an interviewer stays hidden here. The deletion still fails if they have active assignments.
                        </p>
                      </div>
                      <Button variant="danger" disabled={removeSubmitting} onClick={() => void handleRemove()}>
                        {removeSubmitting ? "Removing..." : "Remove interviewer"}
                      </Button>
                    </div>
                  </div>
                </section>
              </div>
            ) : null}
          </DialogDrawerContent>
        </Dialog>
      </div>
    </AdminShell>
  );
}

function AssignmentBucket({
  title,
  description,
  items,
  emptyTitle,
  emptyDescription,
  actionLabel,
  onAction,
  showCurrentOwner = false,
  className,
  listClassName,
}: {
  title: string;
  description: string;
  items: AssignmentModalItem[];
  emptyTitle: string;
  emptyDescription: string;
  actionLabel: string;
  onAction: (applicationId: string) => void;
  showCurrentOwner?: boolean;
  className?: string;
  listClassName?: string;
}) {
  return (
    <section className={`rounded-[1.4rem] border border-white/80 bg-white/74 p-5 shadow-sm ${className ?? ""}`}>
      <div className="mb-4 space-y-1">
        <div className="flex items-center justify-between gap-3">
          <p className="text-lg font-semibold text-[color:var(--ink)]">{title}</p>
          <Badge variant="outline">{items.length}</Badge>
        </div>
        {description ? <p className="text-sm leading-6 text-[color:var(--muted)]">{description}</p> : null}
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-[color:var(--line)] bg-white/60 px-4 py-8 text-center">
          <p className="text-sm font-semibold text-[color:var(--ink)]">{emptyTitle}</p>
          <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">{emptyDescription}</p>
        </div>
      ) : (
        <div className={`space-y-3 xl:overflow-y-auto xl:pr-1 ${listClassName ?? "xl:max-h-[calc(100%-4.75rem)]"}`}>
          {items.map((item) => (
            <div
              key={item.application_id}
              className={getAssignmentItemClassName(item)}
            >
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={item.status} />
                  <p className="truncate text-sm font-semibold text-[color:var(--ink)]" title={item.application_id}>
                    {formatApplicationLabel(item.application_id)}
                  </p>
                </div>
                {showCurrentOwner && item.current_interviewer ? (
                  <p className="truncate text-sm text-[color:var(--muted)]">
                    Current interviewer: {item.current_interviewer.name}
                  </p>
                ) : null}
              </div>
              <Button size="sm" variant="secondary" onClick={() => onAction(item.application_id)}>
                {actionLabel}
              </Button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function DrawerSection({
  icon,
  title,
  description,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[1.4rem] border border-white/80 bg-white/72 p-5 shadow-sm">
      <div className="mb-4 flex items-start gap-3">
        <span className="inline-flex rounded-full bg-[color:var(--accent-soft)] p-2 text-[color:var(--accent)]">{icon}</span>
        <div className="space-y-1">
          <p className="text-lg font-semibold text-[color:var(--ink)]">{title}</p>
          <p className="text-sm leading-6 text-[color:var(--muted)]">{description}</p>
        </div>
      </div>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function formatApplicationLabel(applicationId: string) {
  return applicationId.length > 12 ? `${applicationId.slice(0, 8)}...${applicationId.slice(-4)}` : applicationId;
}

function getAssignmentItemClassName(item: AssignmentModalItem) {
  if (item.source === "assigned") {
    return "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-3 shadow-[inset_0_0_0_1px_rgba(251,191,36,0.14)]";
  }

  if (item.source === "reassign") {
    return "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-violet-200 bg-violet-50/70 px-4 py-3";
  }

  return "flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/80 bg-[color:var(--surface)]/72 px-4 py-3";
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
