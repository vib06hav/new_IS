 "use client";

import { useRouter } from "next/navigation";
import { signOut } from "@/lib/auth";
import { InterviewerNavbar } from "@/components/layout/InterviewerNavbar";

export function InterviewerShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  async function handleSignOut() {
    await signOut();
    router.replace("/interviewer/login");
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
