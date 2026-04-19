"use client";

import { useEffect, useMemo, useState } from "react";
import { Mail, ShieldCheck, UserRound } from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { getSession } from "@/lib/auth";
import type { SessionResponse, UserRole } from "@/lib/types";
import { AdminShell } from "@/components/layout/AdminShell";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shadcn/avatar";
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

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      const data = await getSession();
      if (!cancelled) {
        setSession(data);
        setLoading(false);
      }
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const initials = useMemo(() => {
    const name = session?.user.name?.trim();
    if (!name) return "IS";
    return name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part.charAt(0).toUpperCase())
      .join("");
  }, [session?.user.name]);

  return (
    <div className={`${plexSans.variable} ${libreFranklin.variable}`} style={{ fontFamily: "var(--font-reports-plex)" }}>
      {loading ? (
        <Loader label="Loading account..." />
      ) : (
        <div className="space-y-6">
          <section className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
            <div className="flex flex-col items-center text-center">
              <Avatar className="size-24 border border-slate-200 bg-slate-100">
                {session?.user.profile_image_url ? (
                  <AvatarImage src={session.user.profile_image_url} alt={`${session.user.name} profile image`} />
                ) : null}
                <AvatarFallback className="bg-slate-200 text-2xl font-semibold text-slate-700">{initials}</AvatarFallback>
              </Avatar>
              <h1 className="mt-4 text-3xl font-black leading-none tracking-tight text-slate-800" style={{ fontFamily: "var(--font-display)" }}>
                {session?.user.name ?? "Admin"}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600">
                Identity details are managed by your authentication provider. This page is now an account summary only.
              </p>
            </div>
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <SummaryCard icon={UserRound} label="Display name" value={session?.user.name ?? "Not available"} />
            <SummaryCard icon={Mail} label="Email" value={session?.user.email ?? "Not available"} />
            <SummaryCard icon={ShieldCheck} label="Role" value={formatRole(session?.user.role)} />
            <SummaryCard icon={ShieldCheck} label="Access status" value={formatStatus(session?.user.access_status)} />
          </div>

          <section className="rounded-[2rem] border border-slate-200 bg-slate-50 p-6 text-sm leading-7 text-slate-600">
            Passwords, MFA, email ownership, and profile image updates now live with WorkOS AuthKit. Local app access is
            still enforced by your role and access status, but identity management no longer happens inside this admin
            profile page.
          </section>
        </div>
      )}
    </div>
  );
}

function SummaryCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof UserRound;
  label: string;
  value: string;
}) {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
      <div className="flex items-start gap-3">
        <span className="inline-flex rounded-full bg-blue-50 p-2 text-blue-700">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</p>
          <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800">{value}</p>
        </div>
      </div>
    </section>
  );
}

function formatRole(role?: UserRole) {
  if (!role) return "Not available";
  return role.charAt(0).toUpperCase() + role.slice(1);
}

function formatStatus(status?: string) {
  if (!status) return "Not available";
  return status.charAt(0).toUpperCase() + status.slice(1);
}
