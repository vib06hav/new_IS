export function Loader({ label, fullscreen = false }: { label: string; fullscreen?: boolean }) {
  return (
    <div className={`${fullscreen ? "flex min-h-screen" : "flex min-h-[12rem]"} items-center justify-center`}>
      <div className="rounded-[1.75rem] border border-white/60 bg-white/72 px-8 py-8 text-center shadow-[var(--card-shadow)] backdrop-blur-md">
        <div className="mx-auto flex h-12 w-12 animate-spin items-center justify-center rounded-full border-2 border-[color:var(--line)] border-t-[color:var(--accent)]" />
        <p className="mt-4 text-sm font-medium text-[color:var(--muted)]">{label}</p>
      </div>
    </div>
  );
}
