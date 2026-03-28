"use client";

import { useEffect, useMemo, useState } from "react";
import { createInterviewer, deleteInterviewer, fetchInterviewers } from "@/lib/api";
import type { InterviewerListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { AdminShell } from "@/components/layout/AdminShell";
import { Card } from "@/components/ui/Card";

export default function AdminInterviewersPage() {
  const [items, setItems] = useState<InterviewerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

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

  async function handleCreate() {
    setMessage(null);
    setError(null);
    setSubmitting(true);
    try {
      await createInterviewer(form);
      setForm({ name: "", email: "", password: "" });
      setMessage("Interviewer created.");
      await loadInterviewers();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Failed to create interviewer.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(userId: string) {
    const interviewer = items.find((item) => item.id === userId);
    const confirmed = window.confirm(
      interviewer
        ? `Remove ${interviewer.name}? This only works when they have no active assignments.`
        : "Remove this interviewer? This only works when they have no active assignments.",
    );
    if (!confirmed) {
      return;
    }

    setMessage(null);
    setError(null);
    setBusyUserId(userId);
    try {
      await deleteInterviewer(userId);
      setMessage("Interviewer removed.");
      await loadInterviewers();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to remove interviewer.");
    } finally {
      setBusyUserId(null);
    }
  }

  const assignedLoad = useMemo(() => items.reduce((sum, item) => sum + item.active_assignment_count, 0), [items]);

  return (
    <AdminShell>
      <div className="space-y-6">
        <section className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.94),rgba(231,238,246,0.9))] p-6 shadow-[var(--card-shadow)]">
          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr] xl:items-end">
            <div className="space-y-4">
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">People management</p>
              <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Interviewer Manager</h1>
              <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
                Create reviewer accounts and track assignment pressure in one tighter roster view instead of a long card stack.
              </p>
            </div>
            <div className="metric-strip">
              <MetricCard label="Interviewers" value={String(items.length)} />
              <MetricCard label="Active assignments" value={String(assignedLoad)} />
              <MetricCard label="Average load" value={items.length ? (assignedLoad / items.length).toFixed(1) : "0"} />
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
          <Card title="Create interviewer" description="Admin-only account creation">
            <div className="space-y-3">
              <Input
                label="Name"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              />
              <Input
                label="Email"
                type="email"
                value={form.email}
                onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
              />
              <Input
                label="Password"
                type="password"
                minLength={8}
                value={form.password}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
              />
              <p className="text-xs leading-6 text-[color:var(--muted)]">Use at least 8 characters for the interviewer password.</p>
              <Button
                className="w-full"
                disabled={submitting || !form.name || !form.email || !form.password}
                onClick={() => void handleCreate()}
              >
                {submitting ? "Creating..." : "Create interviewer"}
              </Button>
            </div>
          </Card>

          <div className="space-y-4">
            {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

            {loading ? (
              <Loader label="Loading interviewers..." />
            ) : items.length === 0 ? (
              <EmptyState title="No interviewers yet." description="Create an interviewer to start assigning applications." />
            ) : (
              <div className="data-table">
                <div className="data-table-header md:grid-cols-[1fr_0.8fr_0.75fr]">
                  <span>Interviewer</span>
                  <span>Load</span>
                  <span>Actions</span>
                </div>
                {items.map((item) => (
                  <div key={item.id} className="data-table-row md:grid-cols-[1fr_0.8fr_0.75fr]">
                    <div>
                      <p className="display-font text-base font-semibold text-[color:var(--ink)]">{item.name}</p>
                      <p className="mt-1 text-xs text-[color:var(--muted)]">{item.email}</p>
                    </div>
                    <p className="text-sm text-[color:var(--muted)]">{item.active_assignment_count} active assignments</p>
                    <Button
                      disabled={busyUserId === item.id}
                      variant="danger"
                      onClick={() => void handleDelete(item.id)}
                    >
                      {busyUserId === item.id ? "Removing..." : "Remove"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AdminShell>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/82 px-4 py-4 shadow-[var(--card-shadow-soft)]">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}
