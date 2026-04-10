"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSession, signOut } from "@/lib/auth";
import { Loader } from "@/components/ui/Loader";
import { AdminNavbar } from "@/components/layout/AdminNavbar";
import {
  AdminSessionHistoryProvider,
  clearPersistedAdminSessionHistory,
} from "@/components/layout/AdminSessionHistory";

const adminNav = [
  { href: "/admin/reports", label: "Reports" },
  { href: "/admin/upload", label: "Upload" },
  { href: "/admin/interviewers", label: "Interviewers" },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      const session = await getSession();
      if (cancelled) {
        return;
      }

      if (!session || session.user.role !== "admin") {
        router.replace("/admin/login");
        return;
      }

      setReady(true);
    }

    void checkSession();

    return () => {
      cancelled = true;
    };
  }, [router]);

  async function handleSignOut() {
    clearPersistedAdminSessionHistory();
    await signOut();
    router.replace("/admin/login");
  }

  if (!ready) {
    return <Loader label="Checking session..." fullscreen />;
  }

  return (
    <AdminSessionHistoryProvider>
      <div className="min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]">
        <div className="min-h-screen bg-[#D8DBE2] text-[#111111]">
          <AdminNavbar onSignOut={handleSignOut} />
          <main className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">{children}</main>
        </div>
      </div>
    </AdminSessionHistoryProvider>
  );
}
