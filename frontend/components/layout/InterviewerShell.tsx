 "use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSession, signOut } from "@/lib/auth";
import { Loader } from "@/components/ui/Loader";
import { InterviewerNavbar } from "@/components/layout/InterviewerNavbar";

export function InterviewerShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      const session = await getSession();
      if (cancelled) {
        return;
      }

      if (!session || session.user.role !== "interviewer") {
        router.replace("/interviewer/login");
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
    await signOut();
    router.replace("/interviewer/login");
  }

  if (!ready) {
    return <Loader label="Checking session..." fullscreen />;
  }

  return (
    <div
      className="min-h-screen text-slate-900"
      style={{
        backgroundColor: "#f8fafc",
        backgroundImage: "radial-gradient(#e2e8f0 0.5px, transparent 0.5px)",
        backgroundSize: "24px 24px",
      }}
    >
      <div className="min-h-screen bg-transparent text-slate-900">
        <InterviewerNavbar onSignOut={handleSignOut} />
        <main className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}
