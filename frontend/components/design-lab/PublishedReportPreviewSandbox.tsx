"use client";

import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { Cormorant_Garamond, IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { ReviewPackageSection, type ReviewPageTab } from "@/components/ReviewPackageSection";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { mockPublishedInterviewerApplication } from "@/lib/design-lab/interviewerMock";

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

export function PublishedReportPreviewSandbox() {
  const item = mockPublishedInterviewerApplication;
  const [activePageTab, setActivePageTab] = useState<ReviewPageTab>("page1");
  const lastUpdatedAt = new Date(item.last_activity_at).toLocaleString();
  const pageOptions: Array<{ value: ReviewPageTab; label: string; meta: string }> = [
    { value: "page1", label: "Overview", meta: "Applicant profile" },
    { value: "page2", label: "Academics & Activities", meta: "Study and engagement" },
    { value: "page3", label: "Writing", meta: "Essays and excerpts" },
    { value: "page4", label: "Focus Areas", meta: "Themes and signals" },
    { value: "page5", label: "Questions", meta: "Interview prompts" },
  ];

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
      <div className="min-h-screen bg-[#D8DBE2] text-[#111111]">
        <AdminDesignLabNavbar activeItem="Reports" />

        <main className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-6">
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
              <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6">
                <div className="flex h-full flex-col justify-between gap-6">
                  <div className="space-y-4">
                    <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                      <span className="inline-flex items-center gap-2 text-[#111111]">Design lab preview</span>
                    </div>
                    <div className="space-y-4">
                      <h1
                        className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.7rem]"
                        style={{ fontFamily: "var(--font-reports-cormorant)" }}
                      >
                        Published report mock
                      </h1>
                      <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                        Frontend-only preview of the final interviewer report presentation using mock published data assigned
                        to vib.
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2.5">
                    <StatusBadge status={item.status} />
                    <InlineMeta label="Application ID" value={item.display_id} />
                    <InlineMeta label="Last updated" value={lastUpdatedAt} />
                    <InlineMeta label="Interviewer" value={item.assigned_interviewer?.name || "Unassigned"} />
                  </div>
                </div>
              </div>

              <aside className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Preview notes</p>
                <div className="mt-4 space-y-3">
                  <MetricStrip label="Status" value="Published" />
                  <MetricStrip label="Assigned to" value="vib" />
                  <MetricStrip label="Pages" value="1-5 visible" />
                </div>
                <button
                  className="mt-5 inline-flex items-center gap-1 rounded-full bg-[#111111] px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-[#f7f8ec] transition-all duration-200 hover:bg-[#2B3444]"
                  type="button"
                >
                  Open source PDF
                  <ArrowUpRight className="size-3.5" />
                </button>
              </aside>
            </section>

            <section className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 shadow-[0_18px_36px_rgba(114,125,151,0.12)]">
              <div className="space-y-1">
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Report pages</p>
                <h2 className="text-[1.05rem] font-semibold tracking-[-0.03em] text-[#111111]">Published navigation</h2>
              </div>
              <div className="mt-3 rounded-[1.1rem] border border-[#727D97] bg-[#F7F7F1] p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
                <SegmentedControl value={activePageTab} onChange={setActivePageTab} options={pageOptions} />
              </div>
            </section>

            {item.review_package ? (
              <ReviewPackageSection
                reviewPackage={item.review_package}
                annotationSource={item.latest_draft?.content}
                activeTab={activePageTab}
                onActiveTabChange={setActivePageTab}
              />
            ) : null}
          </div>
        </main>
      </div>
    </div>
  );
}

function InlineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-[#727D97] bg-[#F7F7F1] px-3 py-2 shadow-[0_10px_24px_rgba(114,125,151,0.1)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#5F6C86]">{label}: </span>
      <span className="text-sm text-[#111111]">{value}</span>
    </div>
  );
}

function MetricStrip({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-[#CBD2DE] px-3 py-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
    </div>
  );
}
