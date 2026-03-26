import Link from "next/link";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
};

const buttonClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-ink text-white hover:bg-black",
  secondary: "bg-surface text-ink hover:bg-stone-200",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

export function Button({ className = "", variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded border border-transparent px-4 py-2 text-sm transition disabled:cursor-not-allowed disabled:opacity-60 ${buttonClasses[variant]} ${className}`}
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
      className={`inline-flex items-center justify-center rounded px-4 py-2 text-sm transition ${buttonClasses[variant]}`}
      href={href}
    >
      {children}
    </Link>
  );
}
