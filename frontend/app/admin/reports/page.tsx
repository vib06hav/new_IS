"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { assignApplication, fetchApplications, fetchInterviewers, reassignApplication } from "@/lib/api";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Badge } from "@/components/shadcn/badge";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/shadcn/select";

const REPORT_STATUSES = ["ALL", "READY", "ASSIGNED", "DRAFT", "PUBLISHED"] as const;

export default function AdminReportsPage() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [interviewers, setInterviewers] = useState<InterviewerListItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<(typeof REPORT_STATUSES)[number]>("ALL");
  const [loading, setLoading] = useState(true);
  const [busyAppId, setBusyAppId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedInterviewerByApp, setSelectedInterviewerByApp] = useState<Record<string, string>>({});

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

  const metrics = useMemo(
    () => ({
      total: items.length,
      ready: items.filter((item) => item.status === "READY").length,
      live: items.filter((item) => item.status === "ASSIGNED" || item.status === "DRAFT").length,
    }),
    [items],
  );

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="hero-panel p-6">
          <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Admin review desk</p>
              <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Generated Reports</h1>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                A compact lifecycle board for every review-ready application. Filter fast, assign inline, and open the
                full workspace only when you need to go deep.
              </p>
            </div>
            <div className="metric-strip">
              <MetricCard label="Visible" value={String(metrics.total)} />
              <MetricCard label="Ready to assign" value={String(metrics.ready)} />
              <MetricCard label="In reviewer hands" value={String(metrics.live)} />
            </div>
          </div>
        </section>

        <div>
          <SegmentedControl
            label="Report lifecycle"
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
          <div className="data-table">
            <div className="data-table-header md:grid-cols-[1.2fr_0.8fr_0.8fr_1.2fr_0.7fr]">
              <span>Application</span>
              <span>Status</span>
              <span>Created</span>
              <span>Assignment</span>
              <span>Open</span>
            </div>
            {items.map((item) => {
              const isBusy = busyAppId === item.id;
              const canAssign = item.status === "READY";
              const canReassign = item.status === "ASSIGNED" || item.status === "DRAFT";

              return (
                <div key={item.id} className="data-table-row md:grid-cols-[1.2fr_0.8fr_0.8fr_1.2fr_0.7fr]">
                  <div>
                    <p className="display-font text-base font-semibold text-[color:var(--ink)]">{item.id}</p>
                    <p className="mt-1 text-xs text-[color:var(--muted)]">
                      {item.assigned_interviewer ? item.assigned_interviewer.email : "No interviewer attached yet"}
                    </p>
                  </div>
                  <div>
                    <StatusBadge status={item.status} />
                  </div>
                  <p className="text-sm text-[color:var(--muted)]">{new Date(item.created_at).toLocaleString()}</p>
                  <div className="flex flex-col gap-2">
                    {canAssign || canReassign ? (
                      <>
                        <div className="rounded-2xl border border-white/80 bg-white/75 p-2 shadow-sm">
                          <p className="mb-2 px-1 text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">
                            {canAssign ? "Assign interviewer" : "Reassign interviewer"}
                          </p>
                          <Select
                            value={selectedInterviewerByApp[item.id] || ""}
                            onValueChange={(value) =>
                              setSelectedInterviewerByApp((current) => ({ ...current, [item.id]: value ?? "" }))
                            }
                          >
                            <SelectTrigger className="h-auto w-full rounded-xl border-[color:var(--surface-border)] bg-white px-3 py-3">
                              <SelectValue placeholder="Choose interviewer" />
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
                                    <Badge variant="secondary">{interviewer.active_assignment_count} live</Badge>
                                  </SelectItem>
                                ))}
                              </SelectGroup>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button
                          className="w-full"
                          disabled={isBusy || !selectedInterviewerByApp[item.id]}
                          onClick={() => void mutateAssignment(item.id, canAssign ? "assign" : "reassign")}
                        >
                          <ArrowUpRight />
                          {isBusy ? "Saving..." : canAssign ? "Assign" : "Reassign"}
                        </Button>
                      </>
                    ) : (
                      <p className="text-sm text-[color:var(--muted)]">
                        {item.assigned_interviewer ? `Owned by ${item.assigned_interviewer.name}` : "No action available"}
                      </p>
                    )}
                  </div>
                  <Link
                    className="display-font text-sm font-semibold text-[color:var(--accent)] underline underline-offset-4"
                    href={`/admin/applications/${item.id}`}
                  >
                    Open
                  </Link>
                </div>
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

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
