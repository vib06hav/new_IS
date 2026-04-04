"use client";

import { useEffect, useState } from "react";
import { changeMyPassword } from "@/lib/api";
import { getSession } from "@/lib/auth";
import type { SessionResponse } from "@/lib/types";
import { InterviewerShell } from "@/components/layout/InterviewerShell";
import { Loader } from "@/components/ui/Loader";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export default function InterviewerSettingsPage() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      const data = await getSession();
      if (cancelled) {
        return;
      }
      setSession(data);
      setLoading(false);
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handlePasswordChange() {
    if (form.newPassword !== form.confirmPassword) {
      setError("New password confirmation does not match.");
      return;
    }

    if (!window.confirm("Change your password now?")) {
      return;
    }

    setSubmitting(true);
    setError(null);
    setMessage(null);
    try {
      await changeMyPassword({
        current_password: form.currentPassword,
        new_password: form.newPassword,
      });
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
      setMessage("Password updated.");
    } catch (changeError) {
      setError(changeError instanceof Error ? changeError.message : "Failed to update password.");
    } finally {
      setSubmitting(false);
    }
  }

  const mismatch =
    Boolean(form.newPassword || form.confirmPassword) && form.newPassword !== form.confirmPassword;

  return (
    <InterviewerShell>
      <div className="space-y-6">
        <section className="hero-panel p-6">
          <div className="space-y-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Account settings</p>
            <h1 className="text-4xl font-semibold tracking-[-0.05em] text-[color:var(--ink)]">Settings</h1>
            <p className="max-w-3xl text-sm leading-7 text-[color:var(--muted)]">
              Your profile details stay admin-managed. This screen only lets you update your own password.
            </p>
          </div>
        </section>

        {loading ? (
          <Loader label="Loading settings..." />
        ) : (
          <>
            {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

            <section className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
              <article className="rounded-[1.6rem] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.92),rgba(239,246,255,0.82),rgba(233,225,255,0.6))] p-5 shadow-[0_18px_38px_rgba(148,163,184,0.12)]">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Account</p>
                <p className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{session?.user.name}</p>
                <p className="mt-2 text-sm text-[color:var(--muted)]">{session?.user.email}</p>
                <p className="mt-4 text-sm leading-6 text-[color:var(--muted)]">
                  Name and email are controlled by the admin team. Contact them if those details need to change.
                </p>
              </article>

              <article className="rounded-[1.6rem] border border-white/80 bg-[linear-gradient(145deg,rgba(255,255,255,0.92),rgba(239,246,255,0.82),rgba(233,225,255,0.6))] p-5 shadow-[0_18px_38px_rgba(148,163,184,0.12)]">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">Security</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">Change password</h2>
                <p className="mt-2 text-sm leading-6 text-[color:var(--muted)]">
                  Enter your current password first, then confirm the new one before saving.
                </p>

                <div className="mt-6 space-y-4">
                  <Input
                    label="Current password"
                    type="password"
                    value={form.currentPassword}
                    onChange={(event) => setForm((current) => ({ ...current, currentPassword: event.target.value }))}
                  />
                  <Input
                    label="New password"
                    type="password"
                    minLength={8}
                    value={form.newPassword}
                    onChange={(event) => setForm((current) => ({ ...current, newPassword: event.target.value }))}
                  />
                  <Input
                    label="Confirm new password"
                    type="password"
                    minLength={8}
                    value={form.confirmPassword}
                    onChange={(event) => setForm((current) => ({ ...current, confirmPassword: event.target.value }))}
                  />
                  {mismatch ? <p className="text-sm text-red-700">New password confirmation does not match.</p> : null}
                  <div className="flex justify-end">
                    <Button
                      disabled={
                        submitting ||
                        !form.currentPassword ||
                        !form.newPassword ||
                        !form.confirmPassword ||
                        mismatch
                      }
                      onClick={() => void handlePasswordChange()}
                    >
                      {submitting ? "Saving..." : "Update password"}
                    </Button>
                  </div>
                </div>
              </article>
            </section>
          </>
        )}
      </div>
    </InterviewerShell>
  );
}
