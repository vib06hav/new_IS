"use client";

import { useEffect, useMemo, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { motion } from "motion/react";
import {
  Camera,
  KeyRound,
  LoaderCircle,
  Mail,
  PencilLine,
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { changeMyPassword, updateMyProfile } from "@/lib/api";
import { getSession } from "@/lib/auth";
import type { SessionResponse, UserRole } from "@/lib/types";
import { AdminShell } from "@/components/layout/AdminShell";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Button } from "@/components/ui/Button";
import { Loader } from "@/components/ui/Loader";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

export default function AdminProfilePage() {
  return (
    <AdminShell>
      <AdminProfileContent />
    </AdminShell>
  );
}

function AdminProfileContent() {
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [profileName, setProfileName] = useState("");
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
      setProfileName(data?.user.name ?? "");
      setLoading(false);
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const initials = useMemo(() => {
    const name = session?.user.name?.trim();
    if (!name) {
      return "IS";
    }

    return name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("");
  }, [session?.user.name]);

  const roleLabel = useMemo(() => formatRole(session?.user.role), [session?.user.role]);

  const mismatch =
    Boolean(form.newPassword || form.confirmPassword) && form.newPassword !== form.confirmPassword;

  async function handlePasswordChange() {
    if (mismatch) {
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

  async function handleProfileSave() {
    const nextName = profileName.trim();
    if (!nextName) {
      setError("Display name cannot be empty.");
      return;
    }

    if (nextName === session?.user.name) {
      setMessage("Display name is already up to date.");
      setError(null);
      return;
    }

    setSavingProfile(true);
    setError(null);
    setMessage(null);

    try {
      const updated = await updateMyProfile({ name: nextName });
      setSession(updated);
      setProfileName(updated.user.name);
      setMessage("Display name updated.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to update display name.");
    } finally {
      setSavingProfile(false);
    }
  }

  return (
    <div
      className={[
        plexSans.variable,
        libreFranklin.variable,
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        initial={{ opacity: 0, y: 26 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <div className="mx-auto max-w-[72rem] px-0 py-0">
          {loading ? (
            <Loader label="Loading profile..." />
          ) : (
            <div className="space-y-6">
              {message ? (
                <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
                  {message}
                </p>
              ) : null}
              {error ? (
                <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
                  {error}
                </p>
              ) : null}

              <section className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                <div className="flex flex-col items-center text-center">
                  <Avatar className="size-24 border border-slate-200 bg-slate-100">
                    <AvatarFallback className="bg-slate-200 text-2xl font-semibold text-slate-700">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <button
                    className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 opacity-75 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                    disabled
                    title="Profile image upload will be enabled when MinIO storage is added."
                    type="button"
                  >
                    <Camera className="size-4" />
                    Change profile image
                  </button>

                  <h1
                    className="mt-6 text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {session?.user.name ?? "Admin"}
                  </h1>
                  <p className="mt-2 text-base leading-[1.6] text-slate-600">
                    Personal account details for the admin workspace.
                  </p>
                </div>

                <div className="mt-8 grid gap-4">
                  <ProfileField
                    icon={UserRound}
                    label="Display name"
                    note="Admin identity is shown across the admin workspace."
                  >
                    <div className="space-y-3">
                      <input
                        className="w-full rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-200/70"
                        onChange={(event) => setProfileName(event.target.value)}
                        value={profileName}
                      />
                      <div className="flex justify-end">
                        <Button
                          disabled={savingProfile || !profileName.trim() || profileName.trim() === session?.user.name}
                          onClick={() => void handleProfileSave()}
                        >
                          {savingProfile ? (
                            <LoaderCircle className="size-4 animate-spin" />
                          ) : (
                            <PencilLine className="size-4" />
                          )}
                          {savingProfile ? "Saving..." : "Save display name"}
                        </Button>
                      </div>
                    </div>
                  </ProfileField>
                  <ProfileField
                    icon={Mail}
                    label="Email"
                    note="Email is backend-managed during admin onboarding and remains read-only."
                    value={session?.user.email ?? "Not available"}
                  />
                  <ProfileField
                    icon={ShieldCheck}
                    label="Role"
                    note="Primary control-layer access for uploads, reports, and interviewer assignment."
                    value={roleLabel}
                  />
                </div>
              </section>

              <section className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Security</p>
                <h2
                  className="mt-4 text-[2.4rem] font-black leading-[0.98] tracking-tight text-slate-800"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Change password
                </h2>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
                  Update your password without changing the backend-managed admin email or role assignment.
                </p>

                <div className="mt-6 grid gap-4">
                  <SecurityField
                    autoComplete="current-password"
                    label="Current password"
                    onChange={(event) =>
                      setForm((current) => ({ ...current, currentPassword: event.target.value }))
                    }
                    type="password"
                    value={form.currentPassword}
                  />
                  <SecurityField
                    autoComplete="new-password"
                    label="New password"
                    minLength={8}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, newPassword: event.target.value }))
                    }
                    type="password"
                    value={form.newPassword}
                  />
                  <SecurityField
                    autoComplete="new-password"
                    label="Confirm new password"
                    minLength={8}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, confirmPassword: event.target.value }))
                    }
                    type="password"
                    value={form.confirmPassword}
                  />
                </div>

                {mismatch ? (
                  <p className="mt-4 text-sm text-rose-800">New password confirmation does not match.</p>
                ) : null}

                <div className="mt-6 flex justify-end">
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
                    {submitting ? <LoaderCircle className="size-4 animate-spin" /> : <KeyRound className="size-4" />}
                    {submitting ? "Saving..." : "Update password"}
                  </Button>
                </div>
              </section>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function ProfileField({
  icon: Icon,
  label,
  value,
  note,
  children,
}: {
  icon: typeof UserRound;
  label: string;
  value?: string;
  note: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-[1.4rem] border border-slate-200 bg-white/70 p-4">
      <div className="flex items-start gap-3">
        <span className="inline-flex rounded-full bg-blue-50 p-2 text-blue-700">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="text-base font-semibold text-slate-800">{label}</p>
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
              {children ? "Editable" : "Read only"}
            </span>
          </div>
          {children ? (
            <div className="mt-3">{children}</div>
          ) : (
            <div className="mt-3 rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
              {value}
            </div>
          )}
          <p className="mt-3 text-sm leading-6 text-slate-600">{note}</p>
        </div>
      </div>
    </div>
  );
}

function SecurityField({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
      <p className="text-sm font-semibold text-slate-800">{label}</p>
      <input
        className="mt-3 w-full rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-200/70"
        {...props}
      />
    </label>
  );
}

function formatRole(role?: UserRole) {
  if (!role) {
    return "Not available";
  }

  return role.charAt(0).toUpperCase() + role.slice(1);
}
