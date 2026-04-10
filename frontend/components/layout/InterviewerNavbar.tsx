"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut, UserRound } from "lucide-react";
import { IBM_Plex_Sans } from "next/font/google";
import { getSession } from "@/lib/auth";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

type InterviewerNavbarProps = {
  onSignOut: () => Promise<void> | void;
};

const navItems = [
  { label: "Dashboard", href: "/interviewer/dashboard" },
] as const;

export function InterviewerNavbar({ onSignOut }: InterviewerNavbarProps) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [initials, setInitials] = useState("IS");
  const menuRef = useRef<HTMLDivElement | null>(null);

  const activeItem = useMemo(() => {
    const matchedItem = navItems.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
    return matchedItem?.label ?? null;
  }, [pathname]);

  useEffect(() => {
    let cancelled = false;

    async function loadSession() {
      const session = await getSession();
      if (cancelled) {
        return;
      }

      setInitials(getInitials(session?.user.name));
    }

    void loadSession();

    return () => {
      cancelled = true;
    };
  }, []);

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
      className={`${plexSans.variable} border-b border-[#727D97] bg-[radial-gradient(circle_at_top_left,rgba(25,143,240,0.22),transparent_28%),linear-gradient(180deg,#c7d6e9_0%,#d8dbe2_100%)]`}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="mx-auto max-w-[106rem] px-5 py-4 md:px-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="grid size-11 place-items-center overflow-hidden rounded-2xl border border-[#198FF0]/25 bg-[#EAF4FD] shadow-[0_0_40px_rgba(25,143,240,0.2)]">
                <Image
                  alt="Interview Standardiser logo"
                  className="h-10 w-10 scale-[1.28] object-cover"
                  height={40}
                  src="/Logo-removebg-preview.png"
                  width={40}
                />
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#111111]">
                  Interview Standardiser
                </p>
              </div>
            </div>

            <nav className="hidden items-center gap-2 xl:flex">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
                    item.label === activeItem
                      ? "bg-[#F7F7F1] text-[#111111]"
                      : "text-[#5F6C86] hover:text-[#111111]"
                  }`}
                  href={item.href}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="relative flex items-center gap-2 self-end xl:self-auto" ref={menuRef}>
            <button
              className="rounded-full"
              onClick={() => setMenuOpen((current) => !current)}
              type="button"
            >
              <Avatar className="size-11 border border-[#727D97] bg-[#E6E9F0]">
                <AvatarFallback className="bg-[#AAB4C8] text-[#111111]">{initials}</AvatarFallback>
              </Avatar>
            </button>

            {menuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.6rem)] z-30 min-w-48 rounded-[1.2rem] border border-[#727D97] bg-[#F7F7F1] p-2 shadow-[0_18px_44px_rgba(114,125,151,0.2)]">
                <Link
                  className="flex w-full items-center justify-between rounded-[0.9rem] px-3 py-2 text-left text-sm font-medium text-[#49536B] transition-colors hover:bg-[#E6E9F0]"
                  href="/interviewer/settings"
                  onClick={() => setMenuOpen(false)}
                >
                  <span>View profile</span>
                  <UserRound className="size-4" />
                </Link>
                <button
                  className="flex w-full items-center justify-between rounded-[0.9rem] px-3 py-2 text-left text-sm font-medium text-[#AF3030] transition-colors hover:bg-[#F4DDDD]"
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
