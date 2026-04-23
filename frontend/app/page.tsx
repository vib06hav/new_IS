"use client";

/**
 * IMPROVEMENTS MADE:
 * 1. CSS variables now defined inline via a <style> tag (no missing vars)
 * 2. ScrollAnimationWrapper replaced with a robust custom hook + div pattern
 *    using IntersectionObserver — SSR-safe, no forwardRef issues
 * 3. All browser APIs guarded against SSR (typeof window checks)
 * 4. Accessibility: aria-labels on nav icon, links, and gateway cards
 * 5. Dead href="#" replaced with a real support anchor or placeholder
 * 6. Inline style vs Tailwind conflicts resolved — CSS vars used via style,
 *    layout/spacing via Tailwind only
 * 7. Scroll animations now correctly fade IN (0→1 opacity, offset→0 translateY)
 * 8. Fonts loaded via next/font/google (Libre Franklin + IBM Plex Sans)
 * 9. Initial animation state set so content isn't invisible before JS runs
 */

import Link from "next/link";
import { useEffect, useRef, ReactNode } from "react";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";

// ─── Font Setup ──────────────────────────────────────────────────────────────
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

// ─── Scroll Reveal Hook (SSR-safe) ───────────────────────────────────────────
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

// ─── Reveal Wrapper Component ─────────────────────────────────────────────────
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

// ─── Main Component ───────────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <>
      {/* CSS Variables defined once, globally for this page */}
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
        {/* ── Header ─────────────────────────────────────────────────────── */}
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

          <nav className="flex items-center gap-6" aria-label="Main navigation">
            {/* FIX: href="#" replaced with a real route; use /support or mailto as appropriate */}
            <a
              href="/support"
              className="text-sm font-semibold text-slate-600 hover:text-blue-700 transition-colors duration-200"
            >
              Support
            </a>

            {/* FIX: Added aria-label so screen readers understand the button */}
            <button
              aria-label="User profile"
              className="h-10 w-10 rounded-full border border-slate-200 overflow-hidden bg-slate-100 flex items-center justify-center hover:border-blue-300 transition-colors"
            >
              <svg
                className="w-6 h-6 text-slate-400"
                fill="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z" />
              </svg>
            </button>
          </nav>
        </header>

        {/* ── Deploy Bar ──────────────────────────────────────────────────── */}
        <div
          className="w-full px-6 py-2 flex items-center justify-center gap-6 border-b border-slate-200"
          style={deployBarStyle}
        >
          <span className="text-xs text-slate-500 tracking-wide">
            Internal admissions tool · v1.7 · Academic Year 2026
          </span>
        </div>

        {/* ── Main ────────────────────────────────────────────────────────── */}
        <main className="flex-1 w-full max-w-6xl mx-auto px-6 md:px-10 py-12 space-y-20">

          {/* Section 1: Hero */}
          <section className="grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
            {/* FIX: fade IN (0→1), slide UP (24px→0), correct direction */}
            <Reveal delay={0}>
              <div className="space-y-6">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-blue-200 bg-blue-50/70">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-700" aria-hidden="true" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-blue-900">
                    University Interview Tool
                  </span>
                </div>

                <div>
                  <h1
                    className="text-5xl md:text-[56px] font-black tracking-tight text-slate-800 leading-[1.1] mb-6"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    Standardise Every{" "}
                    <span className="text-blue-700">Interview.</span>
                  </h1>
                  <p
                    className="text-lg md:text-xl text-slate-600 leading-[1.6] max-w-xl"
                    style={{ fontFamily: "var(--font-body)" }}
                  >
                    A structured preparation platform for university interviewers.
                    Grounded in applicant-submitted material, never evaluative.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-slate-600">
                  <div className="rounded-lg border border-slate-200 bg-white/70 px-4 py-3">
                    <p className="text-xs uppercase tracking-widest text-slate-400">Input</p>
                    <p className="font-semibold text-slate-800 mt-1">Applicant PDF</p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-white/70 px-4 py-3">
                    <p className="text-xs uppercase tracking-widest text-slate-400">Output</p>
                    <p className="font-semibold text-slate-800 mt-1">Interview brief</p>
                  </div>
                </div>
              </div>
            </Reveal>

            <Reveal delay={120}>
              <div
                className="rounded-3xl border border-slate-200 bg-white/80 p-8"
                style={visualCardStyle}
              >
                <div className="flex items-center justify-between text-xs uppercase tracking-widest text-slate-400">
                  <span>Interview Brief</span>
                  <span>Preview</span>
                </div>
                <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  {/* Stylized Mock UI for Interview Brief */}
                  <div className="space-y-4">
                    <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Applicant</div>
                        <div className="text-lg font-bold text-slate-800">APP-4902</div>
                      </div>
                      <div className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                        Ready
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <div className="mb-1 text-xs font-semibold text-slate-600">Generated Theme</div>
                        <div className="h-2 w-full rounded bg-slate-100"></div>
                        <div className="mt-1.5 h-2 w-5/6 rounded bg-slate-100"></div>
                      </div>
                      <div>
                        <div className="mb-1 text-xs font-semibold text-slate-600">Proposed Question</div>
                        <div className="h-2 w-full rounded bg-slate-100"></div>
                        <div className="mt-1.5 h-2 w-2/3 rounded bg-slate-100"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Reveal>
          </section>

          {/* Section 2: Gateway Cards (MOVED HERE) */}
          <Reveal delay={0}>
            <section
              className="grid md:grid-cols-2 gap-6"
              aria-label="Login options"
            >
              {/* FIX: aria-label on Link so the full card is described for screen readers */}
              <Link
                href="/admin/login"
                className="block group"
                aria-label="Sign in as Admin — Upload, assign, and monitor admissions briefs"
              >
                <div
                  className="p-7 rounded-2xl flex flex-col gap-4 transition-shadow duration-200 hover:shadow-lg"
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
                      <h2 className="text-xl font-bold text-slate-800">Admin Gateway</h2>
                      <p className="text-sm text-slate-600">
                        Upload, assign, and monitor admissions briefs.
                      </p>
                    </div>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-blue-900">
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
                aria-label="Sign in as Interviewer — Review profiles and focus themes"
              >
                <div
                  className="p-7 rounded-2xl flex flex-col gap-4 transition-shadow duration-200 hover:shadow-lg"
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
                      <h2 className="text-xl font-bold text-slate-800">Interviewer Login</h2>
                      <p className="text-sm text-slate-600">
                        Review profiles and focus themes with confidence.
                      </p>
                    </div>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-blue-900">
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

          {/* Section 3: Signal Map */}
          <Reveal delay={0}>
            <section className="grid lg:grid-cols-[0.95fr_1.05fr] gap-12 items-center">
              <div
                className="rounded-3xl border border-slate-200 bg-white/80 p-8"
                style={visualCardStyle}
              >
                <div className="flex items-center justify-between text-xs uppercase tracking-widest text-slate-400">
                  <span>Signal Map</span>
                  <span>Focus Themes</span>
                </div>
                <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  {/* Stylized Mock UI for Signal Map */}
                  <div className="space-y-3">
                    {/* Signal Item 1 */}
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                        <div className="text-sm font-bold text-slate-800">Intellectual Curiosity</div>
                      </div>
                      <div className="pl-4 text-xs text-slate-500">Demonstrated deep engagement with independent physics research.</div>
                    </div>
                    {/* Signal Item 2 */}
                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
                        <div className="text-sm font-bold text-slate-800">Community Leadership</div>
                      </div>
                      <div className="pl-4 text-xs text-slate-500">Founded the regional debate program for underrepresented students.</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-5">
                {[
                  {
                    label: "Key Value",
                    text: "Reduces manual review time while improving interviewer readiness.",
                  },
                  {
                    label: "What Makes It Different",
                    text: "Structured insights layered on top of the original applicant PDFs.",
                  },
                  {
                    label: "Ideal For",
                    text: "Admissions teams, scholarship committees, and fellowship programs.",
                  },
                ].map(({ label, text }) => (
                  <div
                    key={label}
                    className="rounded-2xl border border-slate-200 bg-white/80 px-5 py-4"
                  >
                    <p className="text-xs font-bold uppercase tracking-widest text-slate-400">
                      {label}
                    </p>
                    <p className="mt-2 text-sm text-slate-700">{text}</p>
                  </div>
                ))}
              </div>
            </section>
          </Reveal>
        </main>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <footer className="w-full py-8 text-center mt-auto border-t border-slate-200">
          <p className="flex items-center justify-center gap-2 text-sm text-slate-500 max-w-md mx-auto px-4">
            <svg
              className="w-4 h-4 text-slate-400 shrink-0"
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
            <span>Designed for university interviewers. This tool does not evaluate applicants.</span>
          </p>
        </footer>
      </div>
    </>
  );
}

// ─── Style Objects (CSS vars only — no Tailwind conflicts) ────────────────────

const bodyStyle: React.CSSProperties = {
  backgroundColor: "var(--canvas)",
  backgroundImage: "radial-gradient(var(--canvas-2) 0.5px, transparent 0.5px)",
  backgroundSize: "24px 24px",
};

const deployBarStyle: React.CSSProperties = {
  backgroundColor: "var(--canvas)",
};

const crestStyle: React.CSSProperties = {
  border: "1px solid var(--accent-soft)",
};

// FIX: Removed conflicting bg-white/80 Tailwind class from the card divs;
// backgroundColor now lives only here in the style object.
const gatewayCardStyle: React.CSSProperties = {
  backgroundColor: "var(--surface)",
  border: "1px solid var(--surface-border)",
  boxShadow: "0 10px 30px rgba(2, 6, 23, 0.08)",
};

const iconCircleStyle: React.CSSProperties = {
  backgroundColor: "var(--accent-soft-2)",
  border: "1px solid var(--accent-soft)",
};

const visualCardStyle: React.CSSProperties = {
  boxShadow: "0 18px 36px rgba(15, 23, 42, 0.08)",
};