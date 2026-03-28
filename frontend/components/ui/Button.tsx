import Link from "next/link";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
};

const buttonClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "clay-button-primary border border-blue-800/10 text-white",
  secondary:
    "border border-slate-200 bg-white/90 text-[color:var(--brand-deep)] shadow-[var(--nav-pill-shadow)] hover:bg-white",
  danger:
    "border border-red-700/10 bg-red-600 text-white shadow-[0_12px_24px_rgba(220,38,38,0.18)] hover:bg-red-700",
};

export function Button({ className = "", variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 disabled:cursor-not-allowed disabled:opacity-60 ${buttonClasses[variant]} ${className}`}
      {...props}
    />
  );
}

export function ButtonLink({
  href,
  children,
  variant = "primary",
}: {
  href: string;
  children: React.ReactNode;
  variant?: "primary" | "secondary";
}) {
  return (
    <Link
      className={`inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition duration-200 ${buttonClasses[variant]}`}
      href={href}
    >
      {children}
    </Link>
  );
}
