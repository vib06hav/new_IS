"use client";

import { motion } from "motion/react";
import { Camera, KeyRound, Mail, ShieldCheck, UserRound } from "lucide-react";
import { Cormorant_Garamond, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import { Button } from "@/components/ui/Button";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-reports-cormorant",
});

export function AdminProfileSandbox() {
  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        cormorant.variable,
        "min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="min-h-screen bg-[#D8DBE2] text-[#111111]"
        initial={{ opacity: 0, y: 26 }}
        transition={{ duration: 0.55, ease: "easeOut" }}
      >
        <AdminDesignLabNavbar activeItem="Profile" />

        <div className="mx-auto max-w-[72rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-6">
            <section className="rounded-[2rem] border border-[#727D97] bg-[#F7F7F1] p-6 shadow-[0_18px_50px_rgba(114,125,151,0.14)]">
              <div className="flex flex-col items-center text-center">
                <Avatar className="size-24 border border-[#727D97] bg-[#E6E9F0]">
                  <AvatarFallback className="bg-[#AAB4C8] text-2xl font-semibold text-[#111111]">
                    IS
                  </AvatarFallback>
                </Avatar>
                <button
                  className="mt-4 inline-flex items-center gap-2 rounded-full border border-[#727D97] bg-[#E6E9F0] px-4 py-2 text-sm font-semibold text-[#111111] transition hover:bg-[#D8DBE2]"
                  type="button"
                >
                  <Camera className="size-4" />
                  Change profile image
                </button>

                <h1
                  className="mt-6 text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.4rem]"
                  style={{ fontFamily: "var(--font-reports-cormorant)" }}
                >
                  Ishani S.
                </h1>
                <p className="mt-2 text-sm leading-7 text-[#49536B]">
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

            <section className="rounded-[2rem] border border-[#727D97] bg-[#F7F7F1] p-6 shadow-[0_18px_50px_rgba(114,125,151,0.14)]">
              <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Security</p>
              <h2
                className="mt-4 text-[2.4rem] leading-[0.96] tracking-[-0.06em] text-[#111111]"
                style={{ fontFamily: "var(--font-reports-cormorant)" }}
              >
                Change password
              </h2>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-[#49536B]">
                Update your password without changing the backend-managed admin email or role assignment.
              </p>

              <div className="mt-6 grid gap-4">
                <SecurityField label="Current password" value="Enter current password" />
                <SecurityField label="New password" value="Enter new password" />
                <SecurityField label="Confirm new password" value="Confirm new password" />
              </div>

              <div className="mt-6 flex justify-end">
                <Button>
                  <KeyRound className="size-4" />
                  Update password
                </Button>
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
    <div className="rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <div className="flex items-start gap-3">
        <span className="inline-flex rounded-full bg-[#198FF0]/14 p-2 text-[#198FF0]">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="text-base font-semibold text-[#111111]">{label}</p>
            {!editable ? (
              <span className="rounded-full border border-[#727D97] bg-[#F7F7F1] px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-[#49536B]">
                Read only
              </span>
            ) : null}
          </div>
          <div className="mt-3 rounded-[1rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm text-[#49536B]">
            {value}
          </div>
          <p className="mt-3 text-sm leading-6 text-[#49536B]">{note}</p>
        </div>
      </div>
    </div>
  );
}

function SecurityField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.3rem] border border-[#727D97] bg-[#E6E9F0] p-4">
      <p className="text-sm font-semibold text-[#111111]">{label}</p>
      <div className="mt-3 rounded-[1rem] border border-[#727D97] bg-[#F7F7F1] px-4 py-3 text-sm text-[#7A8395]">
        {value}
      </div>
    </div>
  );
}
