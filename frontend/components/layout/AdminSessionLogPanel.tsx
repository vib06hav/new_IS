"use client";

import { useEffect, useState } from "react";
import type {
  AdminSessionHistoryEntry,
  AdminSessionHistoryTone,
} from "@/components/layout/AdminSessionHistory";

export function AdminSessionLogPanel({
  entries,
}: {
  entries: AdminSessionHistoryEntry[];
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const interval = window.setInterval(() => {
      setNow(Date.now());
    }, 30000);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="rounded-[1.9rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Session log</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">Actions taken during this session appear here in order.</p>
      <div className="mt-5 rounded-[1.4rem] border border-slate-200 bg-white/70">
        <div className="border-b border-slate-200 px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Current session</p>
        </div>
        {entries.length > 0 ? (
          <div className="divide-y divide-slate-200">
            {entries.map((entry) => (
              <div key={entry.id} className="px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getSessionLogToneClasses(entry.tone)}`}
                      >
                        {entry.action}
                      </span>
                      <p className="text-sm font-semibold text-slate-800">{entry.reportId}</p>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">{entry.detail}</p>
                  </div>
                  <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                    {formatSessionLogTime(entry.timestamp, now)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-5">
            <p className="text-sm leading-6 text-slate-600">No actions yet in this session.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function formatSessionLogTime(timestamp: number, now: number) {
  const elapsedMs = Math.max(0, now - timestamp);
  const elapsedMinutes = Math.floor(elapsedMs / 60000);

  if (elapsedMinutes <= 0) {
    return "Just now";
  }

  if (elapsedMinutes < 60) {
    return `${elapsedMinutes} min ago`;
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60);
  if (elapsedHours < 24) {
    return `${elapsedHours} hr ago`;
  }

  const elapsedDays = Math.floor(elapsedHours / 24);
  return `${elapsedDays} d ago`;
}

function getSessionLogToneClasses(tone: AdminSessionHistoryTone) {
  if (tone === "lime") return "bg-lime-100 text-lime-900";
  if (tone === "blue") return "bg-blue-100 text-blue-900";
  if (tone === "cyan") return "bg-sky-100 text-sky-900";
  if (tone === "orange") return "bg-amber-100 text-amber-900";
  if (tone === "pink") return "bg-rose-100 text-rose-800";
  return "bg-slate-100 text-slate-700";
}
