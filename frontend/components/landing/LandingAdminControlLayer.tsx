"use client";

import { IBM_Plex_Sans, Libre_Franklin } from "next/font/google";
import { AdminReportCard } from "@/components/admin/AdminReportCard";
import type { ApplicationListItem, InterviewerListItem } from "@/lib/types";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-reports-display",
});

const interviewers: InterviewerListItem[] = [
  {
    id: "int-1",
    name: "Maya Chen",
    email: "maya@example.com",
    access_status: "active",
    active_assignment_count: 3,
    profile_image_url: null,
  },
  {
    id: "int-2",
    name: "Rohan Shah",
    email: "rohan@example.com",
    access_status: "active",
    active_assignment_count: 2,
    profile_image_url: null,
  },
];

const reportCards: Array<{ item: ApplicationListItem; selectedInterviewerId?: string }> = [
  {
    item: {
      id: "rep-processed",
      display_id: "APPLICATION-20426",
      status: "PROCESSED",
      is_hidden: false,
      is_hidden_for_interviewer: false,
      created_at: "2026-05-01T08:15:00.000Z",
      last_activity_at: "2026-05-02T09:20:00.000Z",
      assigned_interviewer: null,
    },
  },
  {
    item: {
      id: "rep-ready",
      display_id: "APPLICATION-20526",
      status: "READY",
      is_hidden: false,
      is_hidden_for_interviewer: false,
      created_at: "2026-05-01T09:30:00.000Z",
      last_activity_at: "2026-05-02T11:05:00.000Z",
      assigned_interviewer: null,
    },
    selectedInterviewerId: "int-1",
  },
  {
    item: {
      id: "rep-complete",
      display_id: "APPLICATION-20626",
      status: "COMPLETE",
      is_hidden: false,
      is_hidden_for_interviewer: false,
      created_at: "2026-04-29T10:00:00.000Z",
      last_activity_at: "2026-05-02T16:45:00.000Z",
      assigned_interviewer: {
        id: "int-2",
        name: "Rohan Shah",
        email: "rohan@example.com",
        profile_image_url: null,
      },
    },
  },
];

export function LandingAdminControlLayer() {
  return (
    <div className={`${plexSans.variable} ${libreFranklin.variable}`} style={{ fontFamily: "var(--font-reports-plex)" }}>
      <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-3">
          <h3
            className="max-w-4xl text-3xl font-black leading-none tracking-tight text-slate-800 md:text-4xl"
            style={{ fontFamily: "var(--font-reports-display)" }}
          >
            Applications Dashboard
          </h3>
          <p className="max-w-3xl text-sm leading-relaxed text-slate-600">
            Assign interviewers, generate Pages 4-5, and review completed evaluations from one control layer.
          </p>
        </div>
      </section>

      <section className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {reportCards.map(({ item, selectedInterviewerId }) => (
          <AdminReportCard
            key={item.id}
            item={item}
            interviewers={interviewers}
            selectedInterviewerId={selectedInterviewerId ?? ""}
            onSelectedInterviewerChange={() => { }}
            onAssign={() => { }}
            onGenerate={() => { }}
            onToggleHidden={() => { }}
            onDelete={() => { }}
            onStartEdit={() => { }}
            onCancelEdit={() => { }}
            onSaveEdit={() => { }}
            onPendingDisplayIdChange={() => { }}
            pendingDisplayId={item.display_id}
            isBusy={false}
            isGenerating={false}
            generationCapacityFull={false}
            isHiddenBusy={false}
            isDeleting={false}
            isEditingDisplayId={false}
            isSavingDisplayId={false}
          />
        ))}
      </section>
    </div>
  );
}
