"use client";

import { useEffect, useMemo, useRef, useState, type ChangeEvent, type InputHTMLAttributes, type ReactNode } from "react";
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
import { changeMyPassword, updateMyProfile, uploadMyProfileImage } from "@/lib/api";
import { getSession } from "@/lib/auth";
import type { SessionResponse, UserRole } from "@/lib/types";
import { AdminShell } from "@/components/layout/AdminShell";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shadcn/avatar";
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
  const [uploadingImage, setUploadingImage] = useState(false);
  const [form, setForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const profileImageInputRef = useRef<HTMLInputElement | null>(null);

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

  async function handleProfileImageChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0];
    event.target.value = "";
    if (!nextFile) {
      return;
    }

    setUploadingImage(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await uploadMyProfileImage(nextFile);
      setSession(updated);
      setMessage("Profile image updated.");
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Failed to update profile image.");
    } finally {
      setUploadingImage(false);
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
        <div className="mx-auto max-w-[106rem] px-0 py-0">
          {loading ? (
            <Loader label="Loading profile..." />
          ) : (
            <div className="space-y-6">
              {message ? (
                <div className="flex items-center gap-3 rounded-2xl border border-blue-100 bg-blue-50/50 px-4 py-3 text-sm font-medium text-blue-900 backdrop-blur-sm">
                  <div className="size-2 rounded-full bg-blue-500 animate-pulse" />
                  {message}
                </div>
              ) : null}
              {error ? (
                <div className="flex items-center gap-3 rounded-2xl border border-rose-100 bg-rose-50/50 px-4 py-3 text-sm font-medium text-rose-900 backdrop-blur-sm">
                  <div className="size-2 rounded-full bg-rose-500" />
                  {error}
                </div>
              ) : null}

              {/* Identity Card: Stands alone at the top */}
              <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-[0_15px_30px_rgba(15,23,42,0.05)]">
                <div className="flex flex-col items-center text-center">
                  <Avatar className="size-24 border border-slate-200 bg-slate-100">
                    {session?.user.profile_image_url ? (
                      <AvatarImage src={session.user.profile_image_url} alt={`${session.user.name} profile image`} />
                    ) : null}
                    <AvatarFallback className="bg-slate-200 text-2xl font-semibold text-slate-700">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <button
                    className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 opacity-75 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                    disabled={uploadingImage}
                    onClick={() => profileImageInputRef.current?.click()}
                    type="button"
                  >
                    <Camera className="size-4" />
                    {uploadingImage ? "Uploading..." : "Change profile image"}
                  </button>
                  <input
                    ref={profileImageInputRef}
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={(event) => void handleProfileImageChange(event)}
                    type="file"
                  />

                  <h1
                    className="mt-4 text-3xl font-black leading-none tracking-tight text-slate-800"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {session?.user.name ?? "Admin"}
                  </h1>
                </div>
              </section>

              {/* Grid: Equal sized dual panes below */}
              <div className="grid gap-6 lg:grid-cols-2 items-start">
                {/* Profile Details Area */}
                <section className="h-full rounded-[2rem] border border-slate-200 bg-white/80 p-8 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="grid size-10 place-items-center rounded-xl border border-slate-200 bg-slate-50 text-slate-400">
                      <UserRound className="size-5" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">Settings</p>
                      <h2 className="mt-1 text-xl font-bold text-slate-800">Profile Information</h2>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <ProfileField
                      icon={UserRound}
                      label="Display name"
                    >
                      <div className="space-y-3">
                        <input
                          className="w-full rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
                          onChange={(event) => setProfileName(event.target.value)}
                          value={profileName}
                        />
                        <div className="flex justify-end">
                          <Button
                            className="h-9 px-6 text-xs font-bold"
                            disabled={savingProfile || !profileName.trim() || profileName.trim() === session?.user.name}
                            onClick={() => void handleProfileSave()}
                          >
                            {savingProfile ? (
                              <LoaderCircle className="size-3.5 animate-spin" />
                            ) : (
                              <PencilLine className="size-3.5" />
                            )}
                            {savingProfile ? "Saving..." : "Update Name"}
                          </Button>
                        </div>
                      </div>
                    </ProfileField>
                    <ProfileField
                      icon={Mail}
                      label="Email"
                      value={session?.user.email ?? "Not available"}
                    />
                    <ProfileField
                      icon={ShieldCheck}
                      label="Role"
                      value={roleLabel}
                    />
                  </div>
                </section>

                {/* Security Area */}
                <section className="h-full rounded-[2rem] border border-slate-200 bg-white/80 p-8 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="grid size-10 place-items-center rounded-xl border border-slate-200 bg-slate-50 text-slate-400">
                      <KeyRound className="size-5" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Security Credentials</h2>
                    </div>
                  </div>

                  <div className="space-y-6">
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

                    {mismatch ? (
                      <div className="flex items-center gap-2 rounded-xl bg-rose-50 px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-rose-800 border border-rose-100">
                        Passwords do not match
                      </div>
                    ) : null}

                    <div className="flex justify-end pt-2">
                      <Button
                        className="w-full lg:w-auto px-8"
                        disabled={
                          submitting ||
                          !form.currentPassword ||
                          !form.newPassword ||
                          !form.confirmPassword ||
                          mismatch
                        }
                        onClick={() => void handlePasswordChange()}
                      >
                        {submitting ? <LoaderCircle className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />}
                        {submitting ? "Processing..." : "Secure Account"}
                      </Button>
                    </div>
                  </div>
                </section>
              </div>

              <div className="rounded-[2rem] border border-slate-100 bg-white/50 p-6 text-center">
                <p className="text-[10px] font-medium uppercase tracking-[0.2em] text-slate-400">
                  Last session activity: {new Date().toLocaleDateString()} • Secure Admin Environment
                </p>
              </div>
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
  children,
}: {
  icon: typeof UserRound;
  label: string;
  value?: string;
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
    <label className="block space-y-2">
      <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 ml-1">{label}</p>
      <input
        className="block w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100 shadow-sm"
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
