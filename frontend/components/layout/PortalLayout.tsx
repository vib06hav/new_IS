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
    <div className="min-h-screen bg-[#fafaf9]">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted">AG Interview Standardiser</p>
            <h1 className="text-xl font-semibold text-ink">{title}</h1>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <nav className="flex flex-wrap gap-2 text-sm">
              {navItems.map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`rounded px-3 py-2 ${active ? "bg-ink text-white" : "bg-surface text-muted"}`}
                    href={item.href}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <button className="text-sm text-muted underline" onClick={() => void handleSignOut()} type="button">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
