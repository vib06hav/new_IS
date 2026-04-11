"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { LogOut, UserRound } from "lucide-react";
import { IBM_Plex_Sans } from "next/font/google";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
  display: "swap",
});

const navItems = [
  { label: "Reports", href: "/design-lab/reports-dashboard-playground" },
  { label: "Upload", href: "/design-lab/admin-upload" },
  { label: "Interviewers", href: "/design-lab/admin-interviewers" },
] as const;

export function AdminDesignLabNavbar({
  activeItem,
}: {
  activeItem: "Reports" | "Upload" | "Interviewers" | "Profile";
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

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

  return (
    <div
      className={`${ibmPlexSans.variable} sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur-md`}
      style={{ fontFamily: "var(--font-body)" }}
    >
      <div className="mx-auto max-w-[106rem] px-5 py-4 md:px-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex items-center gap-5">
            <div className="flex items-center gap-3">
              <div className="grid size-11 place-items-center overflow-hidden rounded-xl border border-blue-200 bg-blue-50 shadow-sm">
                <Image
                  alt="Interview Standardiser logo"
                  className="h-10 w-10 scale-[1.28] object-cover"
                  height={40}
                  src="/Logo-removebg-preview.png"
                  width={40}
                />
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-800">
                  Interview Standardiser
                </p>
              </div>
            </div>

            <nav className="hidden items-center gap-2 xl:flex">
              {navItems.map((item) => (
                <Link
                  key={item.label}
                  className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
                    item.label === activeItem
                      ? "border-blue-100 bg-[linear-gradient(135deg,rgba(219,234,254,0.98),rgba(239,246,255,0.98))] text-slate-800 shadow-[0_10px_22px_rgba(148,163,184,0.16)]"
                      : "border-transparent text-slate-500 hover:border-slate-200 hover:bg-white hover:text-blue-700"
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
              <Avatar className="size-11 border border-slate-200 bg-slate-100">
                <AvatarFallback className="bg-slate-200 text-slate-700">IS</AvatarFallback>
              </Avatar>
            </button>

            {menuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.6rem)] z-30 min-w-48 rounded-[1.2rem] border border-slate-200 bg-white p-2 shadow-[0_18px_44px_rgba(15,23,42,0.12)]">
                <Link
                  className={`flex items-center justify-between rounded-[0.9rem] px-3 py-2 text-sm font-medium transition-colors ${
                    activeItem === "Profile"
                      ? "bg-blue-50 text-slate-800"
                      : "text-slate-600 hover:bg-slate-50"
                  }`}
                  href="/design-lab/admin-profile"
                  onClick={() => setMenuOpen(false)}
                >
                  <span>View profile</span>
                  <UserRound className="size-4" />
                </Link>
                <button
                  className="flex w-full items-center justify-between rounded-[0.9rem] px-3 py-2 text-left text-sm font-medium text-rose-700 transition-colors hover:bg-rose-50"
                  onClick={() => setMenuOpen(false)}
                  type="button"
                >
                  <span>Sign out</span>
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
