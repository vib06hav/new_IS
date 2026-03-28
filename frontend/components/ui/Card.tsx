type CardProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function Card({ title, description, children }: CardProps) {
  return (
    <section className="fade-rise clay-card rounded-2xl p-6 shadow-[var(--card-shadow-soft)]">
      <div className="mb-4 space-y-1">
        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[color:var(--muted)]/80">Interview Standardiser</p>
        <h2 className="text-lg font-semibold tracking-tight text-[color:var(--brand-deep)]">{title}</h2>
        {description ? <p className="text-sm text-[color:var(--muted)]">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
