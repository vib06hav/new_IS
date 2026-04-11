const statusClasses: Record<string, string> = {
  QUEUED: "border-sky-200 bg-sky-100/90 text-sky-800",
  UPLOADED: "border-stone-200 bg-stone-100/90 text-stone-700",
  PROCESSING: "border-amber-200 bg-amber-100/90 text-amber-800",
  PROCESSED: "border-violet-200 bg-violet-100/90 text-violet-800",
  READY: "border-blue-200 bg-blue-100/90 text-blue-800",
  COMPLETE: "border-emerald-200 bg-emerald-100/90 text-emerald-800",
  FAILED: "border-red-200 bg-red-100/90 text-red-700",
  ASSIGNED: "border-sky-200 bg-sky-100/90 text-sky-900",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${statusClasses[status] || "border-stone-200 bg-stone-100 text-stone-700"}`}
    >
      {status}
    </span>
  );
}
