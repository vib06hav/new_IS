"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { assignApplication, fetchApplications, fetchInterviewers, reassignApplication } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { SelectInput } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { usePolling } from "@/lib/usePolling";
import { AdminShell } from "@/components/layout/AdminShell";

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
    const token = getToken();
    if (!token) {
      return;
    }

    try {
      const [applications, interviewerList] = await Promise.all([
        fetchApplications(token, statusFilter === "ALL" ? undefined : statusFilter),
        fetchInterviewers(token),
      ]);
      setItems(
        applications.filter(
          (item) => item.status !== "UPLOADED" && item.status !== "PROCESSING" && item.status !== "FAILED",
        ),
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
    const token = getToken();
    if (!token) {
      return;
    }

    setBusyAppId(applicationId);
    try {
      if (mode === "assign") {
        await assignApplication(token, applicationId, interviewerId);
        setMessage("Application assigned.");
      } else {
        await reassignApplication(token, applicationId, interviewerId);
        setMessage("Application reassigned.");
      }
      await loadData();
    } catch (mutationError) {
      setError(mutationError instanceof Error ? mutationError.message : "Assignment update failed.");
    } finally {
      setBusyAppId(null);
    }
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-ink">Generated Reports</h1>
            <p className="text-sm text-muted">Processed applications and assignment state.</p>
          </div>
          <div className="w-full md:w-56">
            <SelectInput
              label="Filter by status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as (typeof REPORT_STATUSES)[number])}
              options={REPORT_STATUSES.map((status) => ({ value: status, label: status }))}
            />
          </div>
        </div>

        {message ? <p className="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading reports..." />
        ) : items.length === 0 ? (
          <EmptyState title="No processed applications yet." description="READY and later states will appear here." />
        ) : (
          <div className="space-y-4">
            {items.map((item) => {
              const isBusy = busyAppId === item.id;
              const canAssign = item.status === "READY";
              const canReassign = item.status === "ASSIGNED" || item.status === "DRAFT";

              return (
                <Card key={item.id} title={item.id} description={`Created ${new Date(item.created_at).toLocaleString()}`}>
                  <div className="space-y-4">
                    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                      <div className="flex items-center gap-3">
                        <StatusBadge status={item.status} />
                        <span className="text-sm text-muted">
                          {item.assigned_interviewer ? `Assigned to ${item.assigned_interviewer.name}` : "Unassigned"}
                        </span>
                      </div>
                      <Link className="text-sm text-accent underline" href={`/admin/applications/${item.id}`}>
                        View application
                      </Link>
                    </div>

                    {canAssign || canReassign ? (
                      <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                        <SelectInput
                          label={canAssign ? "Assign interviewer" : "Reassign interviewer"}
                          value={selectedInterviewerByApp[item.id] || ""}
                          onChange={(event) =>
                            setSelectedInterviewerByApp((current) => ({
                              ...current,
                              [item.id]: event.target.value,
                            }))
                          }
                          options={[
                            { value: "", label: "Choose interviewer" },
                            ...interviewers.map((interviewer) => ({
                              value: interviewer.id,
                              label: `${interviewer.name} (${interviewer.active_assignment_count})`,
                            })),
                          ]}
                        />
                        <div className="flex items-end">
                          <Button
                            disabled={isBusy || !selectedInterviewerByApp[item.id]}
                            onClick={() => void mutateAssignment(item.id, canAssign ? "assign" : "reassign")}
                          >
                            {isBusy ? "Saving..." : canAssign ? "Assign" : "Reassign"}
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </AdminShell>
  );
}
