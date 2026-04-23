"use client";

import Link from "next/link";
import { useEffect, useRef, ReactNode } from "react";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";

const libreFranklin = Libre_Franklin({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-display",
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-body",
  display: "swap",
});

function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.opacity = "1";
          el.style.transform = "translateY(0px)";
          observer.unobserve(el);
        }
      },
      { threshold: 0.12 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return ref;
}

function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useScrollReveal();

  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: 0,
        transform: "translateY(24px)",
        transition: `opacity 0.6s ease ${delay}ms, transform 0.6s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

export default function PortalPage() {
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
        className={`min-h-screen flex flex-col text-slate-900 ${libreFranklin.variable} ${ibmPlexSans.variable}`}
        style={bodyStyle}
      >
        <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50 px-6 md:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div
              className="relative w-10 h-10 flex items-center justify-center bg-blue-100 rounded-lg shadow-sm"
              style={crestStyle}
            >
              <svg
                className="w-6 h-6 text-blue-900"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                />
              </svg>
              <span className="absolute -bottom-1 -right-1 bg-white text-blue-900 text-[10px] font-bold px-1 rounded border border-blue-200">
                IS
              </span>
            </div>
            <span className="text-xl font-semibold tracking-tight text-slate-800">
              Interview Standardiser
            </span>
          </div>

          <nav className="flex items-center gap-2" aria-label="Main navigation">
            <Link
              href="/"
              className="rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-600 transition-colors duration-200 hover:text-blue-700"
            >
              Home
            </Link>
            <Link
              href="/portal"
              className="rounded-full border border-blue-100 bg-blue-50 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-blue-700 transition-colors duration-200 hover:text-blue-800"
            >
              Portal
            </Link>
            <a
              href="/support"
              className="rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-600 transition-colors duration-200 hover:text-blue-700"
            >
              Support
            </a>
          </nav>
        </header>

        <main className="flex-1 w-full max-w-6xl mx-auto px-6 md:px-10 py-16 space-y-12">
          <Reveal delay={0}>
            <section className="max-w-3xl space-y-5">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-blue-200 bg-blue-50/70">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-700" aria-hidden="true" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-blue-900">
                  System Access
                </span>
              </div>

              <div>
                <h1
                  className="text-5xl md:text-[56px] font-black tracking-tight text-slate-800 leading-[1.05] mb-4"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Select your workspace
                </h1>
                <p
                  className="text-lg md:text-xl text-slate-600 leading-[1.6] max-w-2xl"
                  style={{ fontFamily: "var(--font-body)" }}
                >
                  Sign in to continue to your assigned workspace.
                </p>
              </div>
            </section>
          </Reveal>

          <Reveal delay={120}>
            <section
              className="grid md:grid-cols-2 gap-6"
              aria-label="Workspace access options"
            >
              <Link
                href="/admin/login"
                className="block group"
                aria-label="Sign in as Admin"
              >
                <div
                  className="p-7 rounded-2xl flex flex-col gap-5 transition-shadow duration-200 hover:shadow-lg"
                  style={gatewayCardStyle}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                      style={iconCircleStyle}
                    >
                      <svg
                        className="w-6 h-6 text-blue-700"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                        />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Admin</h2>
                    </div>
                  </div>

                  <p className="text-sm leading-7 text-slate-600">
                    Manage applications, team assignments, and monitor
                    interview workflows and operations.
                  </p>

                  <div className="mt-auto flex items-center gap-2 text-sm font-semibold text-blue-900">
                    Sign in as Admin
                    <svg
                      className="w-4 h-4 text-blue-900 transition-transform duration-200 group-hover:translate-x-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </Link>

              <Link
                href="/interviewer/login"
                className="block group"
                aria-label="Sign in as Interviewer"
              >
                <div
                  className="p-7 rounded-2xl flex flex-col gap-5 transition-shadow duration-200 hover:shadow-lg"
                  style={gatewayCardStyle}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                      style={iconCircleStyle}
                    >
                      <svg
                        className="w-6 h-6 text-blue-700"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                        />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-slate-800">Interviewer</h2>
                    </div>
                  </div>

                  <p className="text-sm leading-7 text-slate-600">
                    Access applicant materials, interview briefs and record
                    structured evaluations.
                  </p>

                  <div className="mt-auto flex items-center gap-2 text-sm font-semibold text-blue-900">
                    Sign in as Interviewer
                    <svg
                      className="w-4 h-4 text-blue-900 transition-transform duration-200 group-hover:translate-x-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </div>
              </Link>
            </section>
          </Reveal>
        </main>
      </div>
    </>
  );
}

const bodyStyle: React.CSSProperties = {
  backgroundColor: "var(--canvas)",
  backgroundImage: "radial-gradient(var(--canvas-2) 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
};

const crestStyle: React.CSSProperties = {
  border: "1px solid var(--accent-soft)",
};

const gatewayCardStyle: React.CSSProperties = {
  backgroundColor: "var(--surface)",
  border: "1px solid var(--surface-border)",
  boxShadow: "0 10px 30px rgba(2, 6, 23, 0.08)",
  minHeight: "100%",
};

const iconCircleStyle: React.CSSProperties = {
  backgroundColor: "var(--accent-soft-2)",
  border: "1px solid var(--accent-soft)",
};
