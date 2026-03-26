export function Loader({ label, fullscreen = false }: { label: string; fullscreen?: boolean }) {
  return (
    <div className={`${fullscreen ? "flex min-h-screen" : "flex min-h-[12rem]"} items-center justify-center`}>
      <div className="space-y-2 text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-line border-t-ink" />
        <p className="text-sm text-muted">{label}</p>
      </div>
    </div>
  );
}
