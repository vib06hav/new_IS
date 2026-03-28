export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-[color:var(--line-strong)] bg-white/70 px-6 py-12 text-center shadow-[var(--card-shadow-soft)] backdrop-blur-md">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[color:var(--accent-soft)] text-[color:var(--accent-strong)]">
        <span className="text-lg font-bold">IS</span>
      </div>
      <h2 className="text-xl font-semibold text-[color:var(--ink)]">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-7 text-[color:var(--muted)]">{description}</p>
    </div>
  );
}
