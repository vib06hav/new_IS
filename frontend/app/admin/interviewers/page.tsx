"use client";

import { useEffect, useState } from "react";
import { createInterviewer, deleteInterviewer, fetchInterviewers } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { InterviewerListItem } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { AdminShell } from "@/components/layout/AdminShell";

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
    const token = getToken();
    if (!token) {
      return;
    }
    try {
      const data = await fetchInterviewers(token);
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
    const token = getToken();
    if (!token) {
      return;
    }
    setBusyUserId(userId);
    try {
      await deleteInterviewer(token, userId);
      setMessage("Interviewer removed.");
      await loadInterviewers();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to remove interviewer.");
    } finally {
      setBusyUserId(null);
    }
  }

  return (
    <AdminShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Interviewer Manager</h1>
          <p className="text-sm text-muted">Create and remove interviewer accounts.</p>
        </div>

        <Card title="Create interviewer" description="This uses the existing register endpoint with role=interviewer.">
          <div className="grid gap-3 md:grid-cols-3">
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
          </div>
          <p className="mt-3 text-sm text-muted">Use at least 8 characters for the interviewer password.</p>
          <div className="mt-3">
            <Button
              disabled={submitting || !form.name || !form.email || !form.password}
              onClick={() => void handleCreate()}
            >
              {submitting ? "Creating..." : "Create"}
            </Button>
          </div>
        </Card>

        {message ? <p className="rounded border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading interviewers..." />
        ) : items.length === 0 ? (
          <EmptyState title="No interviewers yet." description="Create an interviewer to start assigning applications." />
        ) : (
          <div className="space-y-4">
            {items.map((item) => (
              <Card key={item.id} title={item.name} description={item.email}>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <span className="text-sm text-muted">Active assignments: {item.active_assignment_count}</span>
                  <Button
                    disabled={busyUserId === item.id}
                    variant="danger"
                    onClick={() => void handleDelete(item.id)}
                  >
                    {busyUserId === item.id ? "Removing..." : "Remove"}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AdminShell>
  );
}
