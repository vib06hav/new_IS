"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, UserRound } from "lucide-react";
import { usePortalSession } from "@/components/auth/PortalSessionProvider";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/shadcn/avatar";

type AdminNavbarProps = {
  onSignOut: () => Promise<void> | void;
};

const navItems = [
  { label: "Reports", href: "/admin/reports" },
  { label: "Upload", href: "/admin/upload" },
  { label: "Interviewers", href: "/admin/interviewers" },
] as const;

export function AdminNavbar({ onSignOut }: AdminNavbarProps) {
  const pathname = usePathname();
  const { session } = usePortalSession();
  const [menuOpen, setMenuOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const navRef = useRef<HTMLDivElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const activeItem = useMemo(() => {
    const matchedItem = navItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
    return matchedItem?.label ?? null;
  }, [pathname]);

  const adminInitials = getInitials(session?.user.name);
  const profileImageUrl = session?.user.profile_image_url ?? null;

  useEffect(() => {
    if (!menuOpen) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (menuRef.current?.contains(target)) return;
      setMenuOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [menuOpen]);

  useEffect(() => {
    const navElement = navRef.current;
    if (!navElement) return;

    const updateNavHeight = () => {
      document.documentElement.style.setProperty("--admin-navbar-height", `${navElement.offsetHeight}px`);
    };

    updateNavHeight();

    const resizeObserver = new ResizeObserver(() => updateNavHeight());
    resizeObserver.observe(navElement);
    window.addEventListener("resize", updateNavHeight);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateNavHeight);
      document.documentElement.style.removeProperty("--admin-navbar-height");
    };
  }, []);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await onSignOut();
    } finally {
      setSigningOut(false);
      setMenuOpen(false);
    }
  }

  return (
    <div
      className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md"
      ref={navRef}
      style={{ fontFamily: "var(--font-body)" }}
    >
      <div className="mx-auto max-w-[106rem] px-5 py-4 md:px-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-5">
          <div className="flex items-center space-x-2">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 shadow-sm border border-blue-200/50">
              <svg
                aria-hidden="true"
                className="size-6 text-blue-900"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                />
              </svg>
              <span className="absolute -bottom-1 -right-1 rounded border border-blue-200 bg-white px-1 text-[10px] font-bold text-blue-900">
                IS
              </span>
            </div>
            <span className="text-xl font-semibold tracking-tight text-slate-800">
              Interview Standardiser
            </span>
          </div>
          </div>

          <div className="relative flex items-center gap-5 self-end xl:self-auto" ref={menuRef}>
            <nav className="hidden items-center gap-2 xl:flex">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-widest transition-colors duration-200 ${
                    item.label === activeItem
                      ? "bg-blue-50 text-blue-700 border border-blue-100"
                      : "text-slate-600 hover:text-blue-700"
                  }`}
                  href={item.href}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            <button
              className="rounded-full"
              onClick={() => setMenuOpen((current) => !current)}
              type="button"
            >
              <Avatar className="size-11 border border-slate-200 bg-slate-100 hover:border-blue-300 transition-colors">
                {profileImageUrl ? <AvatarImage src={profileImageUrl} alt="Admin profile image" /> : null}
                <AvatarFallback className="bg-slate-200 text-slate-600">{adminInitials}</AvatarFallback>
              </Avatar>
            </button>

            {menuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.6rem)] z-30 min-w-48 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg ring-1 ring-black ring-opacity-5">
                <Link
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-600 transition-colors hover:bg-slate-50 hover:text-blue-700"
                  href="/admin/profile"
                  onClick={() => setMenuOpen(false)}
                >
                  <span>View profile</span>
                  <UserRound className="size-4" />
                </Link>
                <button
                  className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm font-medium text-red-600 transition-colors hover:bg-red-50"
                  disabled={signingOut}
                  onClick={() => void handleSignOut()}
                  type="button"
                >
                  <span>{signingOut ? "Signing out" : "Sign out"}</span>
                  <LogOut className="size-4" />
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function getInitials(name?: string) {
  if (!name?.trim()) {
    return "IS";
  }

  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}
