"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import { Stars } from "lucide-react";
import {
  IBM_Plex_Sans,
  Libre_Franklin,
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

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
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
      <div className={`${plexSans.variable} ${libreFranklin.variable} space-y-6`} style={{ fontFamily: "var(--font-reports-plex)" }}>
        <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_13rem] xl:items-stretch">
          <div className="space-y-4 xl:flex xl:h-full xl:flex-col xl:gap-4 xl:space-y-0">
            <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white/80 p-6 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm xl:flex-1">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
                <span className="inline-flex items-center gap-2 text-slate-800">
                  <Stars className="size-3.5" />
                  Interviewer workspace
                </span>
              </div>
              <div className="mt-5 space-y-4">
                <h3
                  className="max-w-4xl text-5xl font-black leading-[1.04] tracking-tight text-slate-800 md:text-[3.5rem]"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Your Reports
                </h3>
                <p className="max-w-3xl text-base leading-[1.6] text-slate-600">
                  Open your assigned reports and hide reports from your personal workspace when you need a cleaner queue.
                </p>
              </div>
            </div>

            <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm">
              <div className="rounded-[1.4rem] border border-slate-200 bg-white/70 p-1.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  {REPORT_STATUSES.map((status) => (
                    <button
                      key={status}
                      className={`rounded-[1rem] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-all duration-200 ${
                        statusFilter === status
                          ? getFilterActiveClasses(status)
                          : "border border-transparent bg-transparent text-slate-500 hover:border-slate-200 hover:bg-white hover:text-blue-700"
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

          <div className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-4 shadow-[0_12px_28px_rgba(15,23,42,0.06)] backdrop-blur-sm xl:flex xl:h-full xl:flex-col">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Status totals</p>
            <div className="mt-4 flex flex-1 flex-col gap-3">
              <StatusTotal className="flex-1" label="All" value={metrics.all} />
              <StatusTotal className="flex-1" label="Assigned" value={metrics.assigned} />
              <StatusTotal className="flex-1" label="Hidden" value={metrics.hidden} />
            </div>
          </div>
        </section>

        {message ? <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p> : null}
        {error ? <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

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
    <div className={`${className ?? ""} flex items-center justify-between gap-3 rounded-[1rem] border border-slate-200 bg-white px-3 py-3`}>
      <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <span className="text-sm font-semibold text-slate-800">{value}</span>
    </div>
  );
}

function getFilterActiveClasses(status: (typeof REPORT_STATUSES)[number]) {
  if (status === "ALL") return "border border-blue-100 bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-slate-800 shadow-[0_10px_22px_rgba(148,163,184,0.16)]";
  if (status === "ASSIGNED") return "border border-sky-200 bg-sky-100 text-sky-900 shadow-[0_8px_20px_rgba(186,230,253,0.28)]";
  return "border border-slate-200 bg-slate-100 text-slate-700 shadow-[0_8px_20px_rgba(226,232,240,0.24)]";
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
    <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 px-6 py-10 text-center shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
      <div className="mx-auto flex max-w-md flex-col items-center">
        <div className="grid size-16 place-items-center overflow-hidden rounded-2xl border border-blue-200 bg-blue-50 shadow-sm">
          <Image
            alt="Interview Standardiser logo"
            className="h-14 w-14 scale-[1.28] object-cover"
            height={56}
            src="/Logo-removebg-preview.png"
            width={56}
          />
        </div>
        <h4
          className="mt-5 text-[2.1rem] font-black leading-[0.98] tracking-tight text-slate-800"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {copy.title}
        </h4>
        <p className="mt-3 text-sm leading-7 text-slate-600">{copy.description}</p>
      </div>
    </div>
  );
}
