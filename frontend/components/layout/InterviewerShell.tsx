 "use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getSession, signOut } from "@/lib/auth";
import { Loader } from "@/components/ui/Loader";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";
import { InterviewerNavbar } from "@/components/layout/InterviewerNavbar";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap",
});

export function InterviewerShell({ 
  children, 
  navbarVariant = "light" 
}: { 
  children: React.ReactNode;
  navbarVariant?: "light" | "dark";
}) {
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
    <>
      <style>{`
        :root {
          --canvas: #f8fafc;
          --canvas-2: #e2e8f0;
          --surface: #ffffff;
          --surface-border: #e2e8f0;
          --accent-soft: #bfdbfe;
          --accent-soft-2: #eff6ff;
          --font-display: ${libreFranklin.style.fontFamily};
          --font-body: ${ibmPlexSans.style.fontFamily};
        }
      `}</style>
      <div
        className={`min-h-screen text-slate-900 ${libreFranklin.variable} ${ibmPlexSans.variable}`}
        style={bodyStyle}
      >
        <div className="min-h-screen bg-transparent text-slate-900">
          <InterviewerNavbar onSignOut={handleSignOut} variant={navbarVariant} />
          <main className="mx-auto max-w-[106rem] px-5 py-7 md:px-8 md:py-8">{children}</main>
        </div>
      </div>
    </>
  );
}

const bodyStyle: React.CSSProperties = {
  backgroundColor: "var(--canvas)",
  backgroundImage: "radial-gradient(var(--canvas-2) 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
};
