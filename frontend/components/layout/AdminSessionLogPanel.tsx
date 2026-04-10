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
    <div className="rounded-[1.9rem] border border-[#727D97] bg-[#CBD2DE] p-5">
      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-[#5F6C86]">Session log</p>
      <p className="mt-3 text-sm leading-6 text-[#49536B]">Actions taken during this session appear here in order.</p>
      <div className="mt-5 rounded-[1.4rem] border border-[#727D97] bg-[#E6E9F0]">
        <div className="border-b border-[#727D97] px-4 py-3">
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[#5F6C86]">Current session</p>
        </div>
        {entries.length > 0 ? (
          <div className="divide-y divide-[#727D97]/45">
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
                      <p className="text-sm font-semibold text-[#111111]">{entry.reportId}</p>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-[#49536B]">{entry.detail}</p>
                  </div>
                  <p className="shrink-0 pt-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#5F6C86]">
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
  if (tone === "lime") return "bg-[#D7FF53] text-[#111111]";
  if (tone === "blue") return "bg-[#198FF0] text-[#F7F7F1]";
  if (tone === "cyan") return "bg-[#7CF0FF] text-[#111111]";
  if (tone === "orange") return "bg-[#FFB347] text-[#111111]";
  if (tone === "pink") return "bg-[#FF6B9D] text-[#111111]";
  return "bg-[#5F6C86] text-[#F7F7F1]";
}
