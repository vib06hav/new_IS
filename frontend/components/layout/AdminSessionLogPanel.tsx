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
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Session log</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">Actions taken during this session appear here in order.</p>
      <div className="mt-5 rounded-2xl border border-slate-100 bg-slate-50/50">
        <div className="border-b border-slate-200/60 px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Current session</p>
        </div>
        {entries.length > 0 ? (
          <div className="divide-y divide-slate-200/60">
            {entries.map((entry) => (
              <div key={entry.id} className="px-4 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest ${getSessionLogToneClasses(entry.tone)}`}
                      >
                        {entry.action}
                      </span>
                      <p className="text-sm font-semibold text-slate-800">{entry.reportId}</p>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-500">{entry.detail}</p>
                  </div>
                  <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-widest text-slate-400">
                    {formatSessionLogTime(entry.timestamp, now)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-4 py-5">
            <p className="text-sm leading-6 text-[#49536B]">No actions yet in this session.</p>
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
  if (tone === "lime") return "bg-lime-100 text-lime-700 border border-lime-200";
  if (tone === "blue") return "bg-blue-100 text-blue-700 border border-blue-200";
  if (tone === "cyan") return "bg-cyan-100 text-cyan-700 border border-cyan-200";
  if (tone === "orange") return "bg-orange-100 text-orange-700 border border-orange-200";
  if (tone === "pink") return "bg-pink-100 text-pink-700 border border-pink-200";
  return "bg-slate-100 text-slate-600 border border-slate-200";
}
