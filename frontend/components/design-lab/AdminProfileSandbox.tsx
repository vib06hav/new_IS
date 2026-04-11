"use client";

import { motion } from "motion/react";
import { Camera, KeyRound, Mail, ShieldCheck, UserRound } from "lucide-react";
import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
  display: "swap",
});

export function AdminProfileSandbox() {
  return (
    <div
      className={`${libreFranklin.variable} ${ibmPlexSans.variable} min-h-screen text-slate-900`}
      style={pageCanvasStyle}
    >
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen text-slate-900"
        initial={{ opacity: 0, y: 26 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <AdminDesignLabNavbar activeItem="Profile" />

        <div className="mx-auto max-w-[72rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-6">
            <section className="rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
              <div className="flex flex-col items-center text-center">
                <Avatar className="size-24 border border-slate-200 bg-slate-100">
                  <AvatarFallback className="bg-slate-200 text-2xl font-semibold text-slate-700">
                    IS
                  </AvatarFallback>
                </Avatar>
                <button
                  className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                  type="button"
                >
                  <Camera className="size-4" />
                  Change profile image
                </button>

                <h1
                  className="mt-6 text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Ishani S.
                </h1>
                <p className="mt-2 text-base leading-[1.6] text-slate-600" style={{ fontFamily: "var(--font-body)" }}>
                  Personal account details for the admin workspace.
                </p>
              </div>

              <div className="mt-8 grid gap-4">
                <ProfileField
                  icon={UserRound}
                  label="Display name"
                  value="Ishani S."
                  editable={false}
                  note="Admin identity is shown across the admin workspace."
                />
                <ProfileField
                  icon={Mail}
                  label="Email"
                  value="admin@interviewstandardiser.internal"
                  editable={false}
                  note="Email is backend-managed during admin onboarding and remains read-only."
                />
                <ProfileField
                  icon={ShieldCheck}
                  label="Role"
                  value="Admin"
                  editable={false}
                  note="Primary control-layer access for uploads, reports, and interviewer assignment."
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
                <SecurityField label="Current password" value="Enter current password" />
                <SecurityField label="New password" value="Enter new password" />
                <SecurityField label="Confirm new password" value="Confirm new password" />
              </div>

              <div className="mt-6 flex justify-end">
                <button className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-800" type="button">
                  <KeyRound className="size-4" />
                  Update password
                </button>
              </div>
            </section>
          </div>
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
  editable,
}: {
  icon: typeof UserRound;
  label: string;
  value: string;
  note: string;
  editable: boolean;
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
            {!editable ? (
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                Read only
              </span>
            ) : null}
          </div>
          <div className="mt-3 rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            {value}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">{note}</p>
        </div>
      </div>
    </div>
  );
}

function SecurityField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.3rem] border border-slate-200 bg-white/70 p-4">
      <p className="text-sm font-semibold text-slate-800">{label}</p>
      <div className="mt-3 rounded-[1rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-400">
        {value}
      </div>
    </div>
  );
}

const pageCanvasStyle: React.CSSProperties = {
  backgroundColor: "#f8fafc",
  backgroundImage: "radial-gradient(#e2e8f0 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
  fontFamily: "var(--font-body)",
};
