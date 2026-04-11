"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { Stars } from "lucide-react";
import {
  Cormorant_Garamond,
  IBM_Plex_Sans,
} from "next/font/google";
import {
  fetchMyApplications,
  hideMyApplication,
  unhideMyApplication,
} from "@/lib/api";
import type { ApplicationListItem } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";
import { usePolling } from "@/lib/usePolling";
import { InterviewerShell } from "@/components/layout/InterviewerShell";
import { InterviewerReportCard } from "@/components/interviewer/InterviewerReportCard";

const REPORT_STATUSES = ["ALL", "ASSIGNED", "HIDDEN"] as const;

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

export default function InterviewerDashboardPage() {
  const [items, setItems] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<(typeof REPORT_STATUSES)[number]>("ALL");
  const [hiddenBusyAppId, setHiddenBusyAppId] = useState<string | null>(null);

  async function loadApplications() {
    try {
      const data = await fetchMyApplications();
      setItems(data);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load assignments.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadApplications();
  }, []);

  usePolling(loadApplications, 5000, !loading);

  const metrics = useMemo(
    () => ({
      all: items.filter((item) => !item.is_hidden_for_interviewer).length,
      assigned: items.filter((item) => !item.is_hidden_for_interviewer && item.status === "ASSIGNED").length,
      hidden: items.filter((item) => item.is_hidden_for_interviewer).length,
    }),
    [items],
  );

  const filteredItems = useMemo(() => {
    if (statusFilter === "ALL") {
      return items.filter((item) => !item.is_hidden_for_interviewer);
    }

    if (statusFilter === "HIDDEN") {
      return items.filter((item) => item.is_hidden_for_interviewer);
    }

    return items.filter((item) => !item.is_hidden_for_interviewer && item.status === statusFilter);
  }, [items, statusFilter]);

  async function toggleHidden(applicationId: string, nextHidden: boolean) {
    setHiddenBusyAppId(applicationId);
    setMessage(null);
    setError(null);
    try {
      if (nextHidden) {
        await hideMyApplication(applicationId);
        setMessage("Report hidden from your dashboard.");
      } else {
        await unhideMyApplication(applicationId);
        setMessage("Report restored to your dashboard.");
      }

      await loadApplications();
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Failed to update report visibility.");
    } finally {
      setHiddenBusyAppId(null);
    }
  }

  return (
    <InterviewerShell>
      <div className={`${plexSans.variable} ${cormorant.variable} space-y-6`} style={{ fontFamily: "var(--font-reports-plex)" }}>
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
          <div className="space-y-4 xl:flex xl:h-full xl:flex-col xl:gap-4 xl:space-y-0">
            <div className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6 xl:flex-1">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                <span className="inline-flex items-center gap-2 text-[#111111]">
                  <Stars className="size-3.5" />
                  Interviewer workspace
                </span>
              </div>
              <div className="mt-5 space-y-4">
                <h3
                  className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.85rem]"
                  style={{ fontFamily: "var(--font-reports-cormorant)" }}
                >
                  Your Reports
                </h3>
                <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                  Open your assigned reports and hide reports from your personal workspace when you need a cleaner queue.
                </p>
              </div>
            </div>

            <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-4">
              <div className="rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0] p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
                <div className="flex flex-wrap items-center gap-1.5">
                  {REPORT_STATUSES.map((status) => (
                    <button
                      key={status}
                      className={`rounded-[1rem] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-200 ${
                        statusFilter === status
                          ? getFilterActiveClasses(status)
                          : "border border-transparent bg-transparent text-[#49536B] hover:border-[#727D97] hover:bg-[#F7F7F1] hover:text-[#111111]"
                      }`}
                      onClick={() => setStatusFilter(status)}
                      type="button"
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[1.6rem] border border-[#727D97] bg-[#E6E9F0] p-4 xl:flex xl:h-full xl:flex-col">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#5F6C86]">Status totals</p>
            <div className="mt-4 flex flex-1 flex-col gap-3">
              <StatusTotal className="flex-1" label="All" value={metrics.all} />
              <StatusTotal className="flex-1" label="Assigned" value={metrics.assigned} />
              <StatusTotal className="flex-1" label="Hidden" value={metrics.hidden} />
            </div>
          </div>
        </section>

        {message ? <p className="rounded-xl border border-blue-200 bg-blue-50 px-3 py-3 text-sm text-blue-700">{message}</p> : null}
        {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <Loader label="Loading dashboard..." />
        ) : filteredItems.length === 0 ? (
          <ReportsEmptyState statusFilter={statusFilter} />
        ) : (
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredItems.map((item) => (
              <InterviewerReportCard
                key={item.id}
                item={item}
                onToggleHidden={() => void toggleHidden(item.id, !item.is_hidden_for_interviewer)}
                isHiddenBusy={hiddenBusyAppId === item.id}
              />
            ))}
          </section>
        )}
      </div>
    </InterviewerShell>
  );
}

function StatusTotal({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <div className={`${className ?? ""} flex items-center justify-between gap-3 rounded-[1rem] border border-[#727D97] bg-[#E6E9F0] px-3 py-3`}>
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">{label}</span>
      <span className="text-sm font-semibold text-[#111111]">{value}</span>
    </div>
  );
}

function getFilterActiveClasses(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") return "bg-[#198FF0] text-[#111111] shadow-[0_8px_20px_rgba(25,143,240,0.28)]";
  if (status === "ASSIGNED") return "bg-[#7cf0ff] text-[#111111] shadow-[0_8px_20px_rgba(124,240,255,0.22)]";
  return "bg-[#8A94A6] text-[#111111] shadow-[0_8px_20px_rgba(138,148,166,0.24)]";
}

function getEmptyStateCopy(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") {
    return {
      title: "No visible reports right now.",
      description: "Assigned reports will appear here once they are available.",
    };
  }

  if (status === "ASSIGNED") {
    return {
      title: "No assigned reports yet.",
      description: "Reports currently routed to you will appear here.",
    };
  }

  return {
    title: "No hidden reports yet.",
    description: "Reports you hide from the main view will appear here.",
  };
}

function ReportsEmptyState({ statusFilter }: { statusFilter: (typeof REPORT_STATUSES)[number] }) {
  const copy = getEmptyStateCopy(statusFilter);

  return (
    <div className="rounded-[1.9rem] border border-[#727D97] bg-[#F7F7F1] px-6 py-10 text-center shadow-[0_18px_44px_rgba(114,125,151,0.14)]">
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="grid size-16 place-items-center overflow-hidden rounded-2xl border border-[#198FF0]/25 bg-[#EAF4FD] shadow-[0_0_40px_rgba(25,143,240,0.2)]">
          <Image
            alt="Interview Standardiser logo"
            className="h-14 w-14 scale-[1.28] object-cover"
            height={56}
            src="/Logo-removebg-preview.png"
            width={56}
          />
        </div>
        <h4
          className="mt-5 text-[2.1rem] leading-[0.95] tracking-[-0.05em] text-[#111111]"
          style={{ fontFamily: "var(--font-reports-cormorant)" }}
        >
          {copy.title}
        </h4>
        <p className="mt-3 text-sm leading-7 text-[#49536B]">{copy.description}</p>
      </div>
    </div>
  );
}
