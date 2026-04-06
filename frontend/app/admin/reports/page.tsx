"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, EyeOff, Eye, PencilLine } from "lucide-react";
import {
  assignApplication,
  fetchApplications,
  fetchInterviewers,
  hideApplication,
  reassignApplication,
  unhideApplication,
  updateApplicationDisplayId,
} from "@/lib/api";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { HeroPanel } from "@/components/ui/HeroPanel";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
} from "@/components/shadcn/select";

const REPORT_STATUSES = ["ALL", "READY", "ASSIGNED", "DRAFT", "PUBLISHED", "HIDDEN"] as const;

export default function AdminReportsPage() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<(typeof REPORT_STATUSES)[number]>("ALL");
  const [loading, setLoading] = useState(true);
  const [busyAppId, setBusyAppId] = useState<string | null>(null);
  const [hiddenBusyAppId, setHiddenBusyAppId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedInterviewerByApp, setSelectedInterviewerByApp] = useState<Record<string, string>>({});
  const [editingDisplayIdAppId, setEditingDisplayIdAppId] = useState<string | null>(null);
  const [draftDisplayIdByApp, setDraftDisplayIdByApp] = useState<Record<string, string>>({});
  const [savingDisplayIdAppId, setSavingDisplayIdAppId] = useState<string | null>(null);

  async function loadData() {
    try {
      const [applications, interviewerList] = await Promise.all([
        fetchApplications(statusFilter === "ALL" ? undefined : statusFilter),
        fetchInterviewers(),
      ]);
      setItems(
        applications.filter((item) => item.status !== "UPLOADED" && item.status !== "PROCESSING" && item.status !== "FAILED"),
      );
      setInterviewers(interviewerList);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load reports.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void loadData();
  }, [statusFilter]);

  usePolling(loadData, 5000, !loading);

  async function mutateAssignment(applicationId: string, mode: "assign" | "reassign") {
    const interviewerId = selectedInterviewerByApp[applicationId];
    if (!interviewerId) {
      setError("Choose an interviewer first.");
      return;
    }

    setBusyAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      if (mode === "assign") {
        await assignApplication(applicationId, interviewerId);
        setMessage("Application assigned.");
      } else {
        await reassignApplication(applicationId, interviewerId);
        setMessage("Application reassigned.");
      }
      await loadData();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Assignment update failed.");
    } finally {
      setBusyAppId(null);
    }
  }

  async function toggleHidden(applicationId: string, nextHidden: boolean) {
    setHiddenBusyAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      if (nextHidden) {
        await hideApplication(applicationId);
        setMessage("Published report hidden.");
      } else {
        await unhideApplication(applicationId);
        setMessage("Hidden report restored.");
      }
      await loadData();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Failed to update report visibility.");
    } finally {
      setHiddenBusyAppId(null);
    }
  }

  function startEditingDisplayId(item: ApplicationListItem) {
    setEditingDisplayIdAppId(item.id);
    setDraftDisplayIdByApp((current) => ({ ...current, [item.id]: item.display_id }));
    setMessage(null);
    setError(null);
  }

  function cancelEditingDisplayId(applicationId: string) {
    setEditingDisplayIdAppId((current) => (current === applicationId ? null : current));
    setDraftDisplayIdByApp((current) => {
      const next = { ...current };
      delete next[applicationId];
      return next;
    });
  }

  async function saveDisplayId(applicationId: string) {
    const displayId = draftDisplayIdByApp[applicationId];
    if (!displayId) {
      setError("Display ID cannot be empty.");
      return;
    }

    setSavingDisplayIdAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      await updateApplicationDisplayId(applicationId, { display_id: displayId });
      setEditingDisplayIdAppId(null);
      setMessage("Application ID updated.");
      await loadData();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update application ID.");
    } finally {
      setSavingDisplayIdAppId(null);
    }
  }

  const metrics = useMemo(
    () => ({
      ready: items.filter((item) => item.status === "READY").length,
      assigned: items.filter((item) => item.status === "ASSIGNED").length,
      draft: items.filter((item) => item.status === "DRAFT").length,
      published: items.filter((item) => item.status === "PUBLISHED").length,
    }),
    [items],
  );

  return (
    <AdminShell>
      <div className="space-y-6">
        <HeroPanel
          eyebrow="Admin review desk"
          title="Generated Reports"
          metrics={[
            { label: "Ready", value: String(metrics.ready) },
            { label: "Assigned", value: String(metrics.assigned) },
            { label: "Draft", value: String(metrics.draft) },
            { label: "Published", value: String(metrics.published) },
          ]}
        />

        <div>
          <SegmentedControl
            label="Report Status"
            value={statusFilter}
            onChange={setStatusFilter}
            options={REPORT_STATUSES.map((status) => ({ value: status, label: status }))}
          />
        </div>

        {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading reports..." />
        ) : items.length === 0 ? (
          <EmptyState title="No processed applications yet." description="READY and later states will appear here." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
            {items.map((item) => {
              const isBusy = busyAppId === item.id;
              const isHiddenBusy = hiddenBusyAppId === item.id;
              const isEditingDisplayId = editingDisplayIdAppId === item.id;
              const isSavingDisplayId = savingDisplayIdAppId === item.id;
              const canAssign = item.status === "READY";
              const canReassign = item.status === "ASSIGNED" || item.status === "DRAFT";
              const canHide = item.status === "PUBLISHED" && !item.is_hidden;
              const canUnhide = item.status === "PUBLISHED" && item.is_hidden;
              const isPublished = item.status === "PUBLISHED";
              const selectedInterviewer = interviewers.find(
                (interviewer) => interviewer.id === selectedInterviewerByApp[item.id],
              );

              return (
                <article
                  key={item.id}
                  className="fade-rise flex flex-col gap-5 rounded-[1.6rem] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.92),rgba(239,246,255,0.82),rgba(233,225,255,0.6))] p-5 shadow-[0_18px_38px_rgba(148,163,184,0.12)]"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2">
                      {isEditingDisplayId ? (
                        <div className="space-y-2">
                          <Input
                            label="Application ID"
                            autoFocus
                            className="mt-0"
                            value={draftDisplayIdByApp[item.id] ?? ""}
                            onChange={(event) =>
                              setDraftDisplayIdByApp((current) => ({ ...current, [item.id]: event.target.value }))
                            }
                          />
                          <div className="flex flex-wrap gap-2">
                            <Button
                              size="sm"
                              disabled={isSavingDisplayId}
                              onClick={() => void saveDisplayId(item.id)}
                            >
                              {isSavingDisplayId ? "Saving..." : "Save ID"}
                            </Button>
                            <Button
                              size="sm"
                              variant="secondary"
                              disabled={isSavingDisplayId}
                              onClick={() => cancelEditingDisplayId(item.id)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="display-font break-all text-lg font-semibold text-[color:var(--ink)]">
                            {item.display_id}
                          </p>
                          <Button size="sm" variant="ghost" onClick={() => startEditingDisplayId(item)}>
                            <PencilLine className="size-4" />
                            Edit
                          </Button>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <StatusBadge status={item.status} />
                        {item.assigned_interviewer && !isPublished ? (
                          <Badge variant="secondary">{item.assigned_interviewer.name}</Badge>
                        ) : null}
                        {item.is_hidden ? <Badge variant="outline">Hidden</Badge> : null}
                      </div>
                    </div>
                    <Link
                      className="inline-flex items-center gap-1 text-sm font-semibold text-[color:var(--accent)] underline underline-offset-4"
                      href={`/admin/applications/${item.id}`}
                    >
                      Open
                      <ArrowUpRight className="size-4" />
                    </Link>
                  </div>

                  <div className="rounded-2xl border border-white/75 bg-white/70 p-4 shadow-sm">
                    {canAssign || canReassign ? (
                      <>
                        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Assignment</p>
                        <div className="mt-3 space-y-3">
                          <Select
                            value={selectedInterviewerByApp[item.id] || ""}
                            onValueChange={(value) =>
                              setSelectedInterviewerByApp((current) => ({ ...current, [item.id]: value ?? "" }))
                            }
                          >
                            <SelectTrigger className="h-auto w-full rounded-xl border-[color:var(--surface-border)] bg-white px-3 py-3">
                              {selectedInterviewer ? (
                                <div className="flex min-w-0 flex-1 items-center gap-2">
                                  <Avatar size="sm">
                                    <AvatarFallback>{getInitials(selectedInterviewer.name)}</AvatarFallback>
                                  </Avatar>
                                  <span className="min-w-0 flex-1">
                                    <span className="block truncate font-medium text-[color:var(--ink)]">
                                      {selectedInterviewer.name}
                                    </span>
                                    <span className="block truncate text-xs text-[color:var(--muted)]">
                                      {selectedInterviewer.email}
                                    </span>
                                  </span>
                                </div>
                              ) : (
                                <span className="text-sm text-[color:var(--muted)]">
                                  {canAssign ? "Choose interviewer" : "Choose new interviewer"}
                                </span>
                              )}
                            </SelectTrigger>
                            <SelectContent className="rounded-2xl border border-[color:var(--surface-border)] shadow-[0_18px_38px_rgba(148,163,184,0.18)]">
                              <SelectGroup>
                                <SelectLabel>Available interviewers</SelectLabel>
                                {interviewers.map((interviewer) => (
                                  <SelectItem key={interviewer.id} value={interviewer.id}>
                                    <Avatar size="sm">
                                      <AvatarFallback>{getInitials(interviewer.name)}</AvatarFallback>
                                    </Avatar>
                                    <span className="min-w-0 flex-1">
                                      <span className="truncate font-medium text-[color:var(--ink)]">{interviewer.name}</span>
                                      <span className="truncate text-xs text-[color:var(--muted)]">{interviewer.email}</span>
                                    </span>
                                    <Badge variant="secondary">{interviewer.active_assignment_count} active</Badge>
                                  </SelectItem>
                                ))}
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                          <Button
                            className="w-full"
                            disabled={isBusy || !selectedInterviewerByApp[item.id]}
                            onClick={() => void mutateAssignment(item.id, canAssign ? "assign" : "reassign")}
                          >
                            {isBusy ? "Saving..." : canAssign ? "Assign interviewer" : "Reassign interviewer"}
                          </Button>
                        </div>
                      </>
                    ) : isPublished ? (
                      <AssignedInterviewerArtifact interviewer={item.assigned_interviewer} />
                    ) : (
                      <>
                        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Assignment</p>
                        <p className="mt-2 text-sm text-[color:var(--muted)]">No action available</p>
                      </>
                    )}
                  </div>

                  {canHide || canUnhide ? (
                    <div className="mt-auto flex justify-end">
                      <Button
                        variant="secondary"
                        disabled={isHiddenBusy}
                        onClick={() => void toggleHidden(item.id, canHide)}
                      >
                        {canHide ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                        {isHiddenBusy ? "Saving..." : canHide ? "Hide report" : "Unhide report"}
                      </Button>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </div>
    </AdminShell>
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

function AssignedInterviewerArtifact({
  interviewer,
}: {
  interviewer: ApplicationListItem["assigned_interviewer"];
}) {
  if (!interviewer) {
    return (
      <>
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Assigned interviewer</p>
        <p className="mt-2 text-sm text-[color:var(--muted)]">No interviewer information available</p>
      </>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Assigned interviewer</p>
      <div className="flex items-center gap-3 rounded-[1rem] border border-white/80 bg-white/82 px-3 py-3 shadow-sm">
        <Avatar size="sm">
          <AvatarFallback>{getInitials(interviewer.name)}</AvatarFallback>
        </Avatar>
        <div className="min-w-0 space-y-1">
          <p className="truncate text-sm font-semibold text-[color:var(--ink)]">{interviewer.name}</p>
          <p className="truncate text-xs text-[color:var(--muted)]">{interviewer.email}</p>
        </div>
      </div>
    </div>
  );
}
