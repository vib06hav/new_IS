"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { LogOut, UserRound } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";

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
    <div className="border-b border-[#727D97] bg-[radial-gradient(circle_at_top_left,rgba(25,143,240,0.22),transparent_28%),linear-gradient(180deg,#c7d6e9_0%,#d8dbe2_100%)]">
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
                <AvatarFallback className="bg-[#AAB4C8] text-[#111111]">IS</AvatarFallback>
              </Avatar>
            </button>

            {menuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.6rem)] z-30 min-w-48 rounded-[1.2rem] border border-[#727D97] bg-[#F7F7F1] p-2 shadow-[0_18px_44px_rgba(114,125,151,0.2)]">
                <Link
                  className={`flex items-center justify-between rounded-[0.9rem] px-3 py-2 text-sm font-medium transition-colors ${
                    activeItem === "Profile"
                      ? "bg-[#E6E9F0] text-[#111111]"
                      : "text-[#49536B] hover:bg-[#E6E9F0]"
                  }`}
                  href="/design-lab/admin-profile"
                  onClick={() => setMenuOpen(false)}
                >
                  <span>View profile</span>
                  <UserRound className="size-4" />
                </Link>
                <button
                  className="flex w-full items-center justify-between rounded-[0.9rem] px-3 py-2 text-left text-sm font-medium text-[#AF3030] transition-colors hover:bg-[#F4DDDD]"
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
