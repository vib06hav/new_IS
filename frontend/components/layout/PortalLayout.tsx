"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getSession, signOut } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import { Loader } from "@/components/ui/Loader";

type PortalLayoutProps = {
  children: React.ReactNode;
  role: UserRole;
  loginHref: string;
  title: string;
  navItems: Array<{ href: string; label: string }>;
};

export function PortalLayout({ children, role, loginHref, title, navItems }: PortalLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function checkSession() {
      const session = await getSession();
      if (cancelled) {
        return;
      }
      if (!session || session.user.role !== role) {
        router.replace(loginHref);
        return;
      }
      setReady(true);
    }
    void checkSession();
    return () => {
      cancelled = true;
    };
  }, [loginHref, role, router]);

  async function handleSignOut() {
    await signOut();
    router.replace(loginHref);
  }

  if (!ready) {
    return <Loader label="Checking session..." fullscreen />;
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.72),transparent_26%),radial-gradient(circle_at_top_right,rgba(219,234,254,0.55),transparent_20%),radial-gradient(circle_at_50%_100%,rgba(254,242,242,0.28),transparent_24%)] text-[color:var(--ink)]">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(255,255,255,0.82))] px-6 py-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-[92rem] flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-accent to-brand-hover shadow-sm">
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                />
              </svg>
              <span className="absolute -bottom-1 -right-1 rounded border border-slate-200 bg-white px-1 text-[10px] font-bold text-brand-deep">
                IS
              </span>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-[color:var(--muted)]">Interview Standardiser</p>
              <h1 className="text-xl font-semibold tracking-tight text-brand-deep">{title}</h1>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <nav className="flex flex-wrap gap-2 text-sm">
              {navItems.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`rounded-xl px-4 py-2.5 font-semibold transition duration-200 ${
                      active
                        ? "border border-blue-100 bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-slate-800 shadow-[0_10px_22px_rgba(148,163,184,0.16)]"
                        : "border border-slate-200 bg-[linear-gradient(135deg,rgba(255,255,255,0.9),rgba(248,250,252,0.9))] text-slate-600 shadow-sm hover:text-brand-accent"
                    }`}
                    href={item.href}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <button
              className="rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-sm font-semibold text-slate-600 shadow-sm transition duration-200 hover:text-brand-accent"
              onClick={() => void handleSignOut()}
              type="button"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[92rem] px-6 py-8 md:py-10">{children}</main>
    </div>
  );
}
