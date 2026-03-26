const statusClasses: Record<string, string> = {
  UPLOADED: "bg-stone-200 text-stone-800",
  PROCESSING: "bg-amber-100 text-amber-800",
  READY: "bg-blue-100 text-blue-800",
  FAILED: "bg-red-100 text-red-800",
  ASSIGNED: "bg-violet-100 text-violet-800",
  DRAFT: "bg-orange-100 text-orange-800",
  PUBLISHED: "bg-emerald-100 text-emerald-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusClasses[status] || "bg-stone-200 text-stone-700"}`}>
      {status}
    </span>
  );
}
