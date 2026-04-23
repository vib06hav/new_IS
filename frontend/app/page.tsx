"use client";

import Link from "next/link";
import { useEffect, useRef, useState, ReactNode } from "react";
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

type RoleKey = "interviewer" | "admin";

const roleContent: Record<
  RoleKey,
  {
    label: string;
    intro: string;
    features: Array<{ title: string; text: string }>;
    visual: {
      eyebrow: string;
      title: string;
      accent: string;
    };
  }
> = {
  interviewer: {
    label: "Interviewer",
    intro:
      "Give interviewers clearer context, better direction, and stronger support in the room.",
    features: [
      {
        title: "Application highlights",
        text: "Surface meaningful passages and signals directly from applicant materials.",
      },
      {
        title: "Themes and questions",
        text: "Generate interview themes and more focused questions from the application.",
      },
      {
        title: "Live interview overlay",
        text: "Support interviewers during the conversation with structured, real-time guidance.",
      },
    ],
    visual: {
      eyebrow: "Interviewer view",
      title: "Move from source material to live guidance",
      accent: "Highlights, themes, questions, and overlay support stay connected.",
    },
  },
  admin: {
    label: "Admin",
    intro: "Coordinate interview operations with more structure and visibility.",
    features: [
      {
        title: "Application oversight",
        text: "Keep applicant materials, interview readiness, and workflow status in one system.",
      },
      {
        title: "Evaluator assignment",
        text: "Assign applications across evaluators and keep ownership clear across the team.",
      },
      {
        title: "Interview workflow management",
        text: "Support the interview process with stronger coordination before, during, and after the interview.",
      },
    ],
    visual: {
      eyebrow: "Admin view",
      title: "Assignments, ownership, and workflow status",
      accent: "Admissions teams can keep interview work moving with clearer control.",
    },
  },
};

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

export default function LandingPage() {
  const [selectedRole, setSelectedRole] = useState<RoleKey>("interviewer");
  const currentRole = roleContent[selectedRole];

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
              className="rounded-full border border-blue-100 bg-blue-50 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-blue-700 transition-colors duration-200 hover:text-blue-800"
            >
              Home
            </Link>
            <Link
              href="/portal"
              className="rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-600 transition-colors duration-200 hover:text-blue-700"
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

        <main className="flex-1 w-full max-w-6xl mx-auto px-6 md:px-10 py-14 space-y-20">
          <section className="grid lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
            <Reveal delay={0}>
              <div className="space-y-6">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-blue-200 bg-blue-50/70">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-700" aria-hidden="true" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-blue-900">
                    Admissions interview intelligence
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
                    className="text-lg md:text-xl text-slate-600 leading-[1.6] max-w-2xl"
                    style={{ fontFamily: "var(--font-body)" }}
                  >
                    A structured preparation platform for university interviewers.
                    Grounded in applicant-submitted material, never evaluative.
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <SmallKeyStat label="Highlights" value="Source evidence" />
                  <SmallKeyStat label="Questions" value="Interview direction" />
                  <SmallKeyStat label="Overlay" value="Live support" />
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

          <Reveal delay={0}>
            <section className="space-y-8">
              <div className="max-w-3xl space-y-3">
                <p className="text-xs font-bold uppercase tracking-[0.28em] text-slate-400">
                  By Role
                </p>
                <h2
                  className="text-3xl md:text-4xl font-black tracking-tight text-slate-800"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Explore the system by role
                </h2>
                <p className="text-base md:text-lg text-slate-600 leading-7">
                  Interview Standardiser supports both admissions coordination and
                  interviewer preparation across the full interview process.
                </p>
              </div>

              <div className="inline-flex rounded-full border border-slate-200 bg-white/80 p-1 shadow-sm">
                <button
                  type="button"
                  onClick={() => setSelectedRole("interviewer")}
                  className={`rounded-full px-5 py-2 text-xs font-semibold uppercase tracking-widest transition-colors duration-200 ${selectedRole === "interviewer"
                      ? "bg-blue-50 text-blue-700 border border-blue-100"
                      : "text-slate-600 hover:text-blue-700"
                    }`}
                >
                  Interviewer
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRole("admin")}
                  className={`rounded-full px-5 py-2 text-xs font-semibold uppercase tracking-widest transition-colors duration-200 ${selectedRole === "admin"
                      ? "bg-blue-50 text-blue-700 border border-blue-100"
                      : "text-slate-600 hover:text-blue-700"
                    }`}
                >
                  Admin
                </button>
              </div>

              <div className="grid lg:grid-cols-[0.92fr_1.08fr] gap-6">
                <div
                  className="rounded-3xl border border-slate-200 bg-white/80 p-5"
                  style={gatewayCardStyle}
                >
                  <div className="space-y-3">
                    <p className="text-xs font-bold uppercase tracking-[0.28em] text-slate-400">
                      {currentRole.label}
                    </p>
                    <h3 className="text-2xl font-bold tracking-tight text-slate-800">
                      {currentRole.intro}
                    </h3>
                  </div>

                  <div className="mt-6 space-y-4">
                    {currentRole.features.map((feature) => (
                      <div
                        key={feature.title}
                        className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3"
                      >
                        <p className="text-sm font-semibold text-slate-800">
                          {feature.title}
                        </p>
                        <p className="text-sm font-semibold text-slate-800">
                          {feature.title}
                        </p>
                        <div className="mt-2 space-y-1.5">
                          <div className="h-1.5 w-full rounded bg-slate-200/60"></div>
                          <div className="h-1.5 w-4/5 rounded bg-slate-200/60"></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div
                  className="rounded-3xl border border-slate-200 bg-white/80 p-5"
                  style={visualCardStyle}
                >
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.28em] text-slate-400">
                      {currentRole.visual.eyebrow}
                    </p>
                    <h3 className="mt-3 text-2xl font-bold tracking-tight text-slate-800">
                      {currentRole.visual.title}
                    </h3>
                    <p className="mt-3 text-sm leading-7 text-slate-600">
                      {currentRole.visual.accent}
                    </p>
                  </div>

                  {selectedRole === "interviewer" ? (
                    <div className="mt-6 rounded-[1.6rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.08)]">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-700">
                            Interview overlay
                          </p>
                          <h4 className="mt-1 text-base font-semibold tracking-tight text-slate-900">
                            Live runner
                          </h4>
                        </div>
                        <span className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                          2/5
                        </span>
                      </div>

                      <div className="mt-4 space-y-2">
                        <div className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 p-3">
                          <div className="flex items-center gap-2">
                            <span className="rounded-full border border-slate-300 bg-white px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                              Q1
                            </span>
                            <span className="rounded-full border border-slate-200 bg-white px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                              generated
                            </span>
                          </div>
                          <div className="mt-4 space-y-2">
                            <div className="h-2 w-full rounded bg-slate-100"></div>
                            <div className="h-2 w-2/3 rounded bg-slate-100"></div>
                          </div>
                        </div>
                        <div className="rounded-[1.1rem] border border-blue-100 bg-blue-50/75 p-3">
                          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
                            Current theme
                          </p>
                          <div className="mt-3 h-2 w-3/4 rounded bg-blue-200"></div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-6 rounded-[1.8rem] border border-slate-200 bg-white/90 text-slate-900 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm">
                      <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <StatusMark status="ASSIGNED" />
                          </div>
                          <div className="h-6 w-32 rounded bg-slate-100"></div>
                        </div>
                        <button
                          className="grid size-10 place-items-center rounded-full border border-slate-200 bg-white text-slate-500"
                          type="button"
                        >
                          <span className="text-lg leading-none">...</span>
                        </button>
                      </div>

                      <div className="space-y-4 px-5 py-5">
                        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
                          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Status</p>
                          <div className="mt-2 h-2 w-1/2 rounded bg-slate-100"></div>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3">
                          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Assignment</p>
                          <div className="mt-2 h-2 w-3/4 rounded bg-indigo-200"></div>
                          <div className="mt-2 h-1.5 w-1/2 rounded bg-slate-100"></div>
                        </div>

                        <div className="flex justify-end">
                          <PrimaryLink label="Open" />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>
          </Reveal>

          <Reveal delay={80}>
            <section className="grid md:grid-cols-2 gap-6">
              <div
                className="rounded-3xl border border-slate-200 bg-white/80 p-5"
                style={visualCardStyle}
              >
                <h3 className="mt-2 text-xl font-bold tracking-tight text-slate-800">
                  Application Highlights
                </h3>
                <div className="mt-4 space-y-3">
                  <div className="rounded-2xl border border-slate-200 bg-white/90 p-3">
                    <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                      Essay excerpt
                    </p>
                    <div className="mt-3 space-y-2">
                      <div className="h-2 w-full rounded bg-slate-100"></div>
                      <div className="h-2 w-full rounded bg-slate-100"></div>
                      <div className="h-2 w-5/6 rounded bg-slate-100"></div>
                    </div>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div className="rounded-2xl border border-blue-100 bg-blue-50/75 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-blue-700">
                        Signal
                      </p>
                      <div className="mt-3 h-2 w-3/4 rounded bg-blue-200"></div>
                    </div>
                    <div className="rounded-2xl border border-slate-200 bg-slate-50/75 p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">
                        Follow-up
                      </p>
                      <div className="mt-3 h-2 w-4/5 rounded bg-slate-200"></div>
                    </div>
                  </div>
                </div>
              </div>

              <div
                className="rounded-3xl border border-slate-200 bg-white/80 p-5"
                style={visualCardStyle}
              >
                <h3 className="mt-2 text-xl font-bold tracking-tight text-slate-800">
                  Interview Overlay
                </h3>
                <div className="mt-4 rounded-[1.6rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.08)]">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-700">
                        Interview overlay
                      </p>
                      <h4 className="mt-1 text-base font-semibold tracking-tight text-slate-900">
                        Live runner
                      </h4>
                    </div>
                    <span className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                      3/6 asked
                    </span>
                  </div>
                  <div className="mt-4 grid gap-2">
                    <div className="rounded-2xl border border-slate-200 bg-slate-50/80 p-3">
                      <p className="text-xs uppercase tracking-widest text-slate-400">
                        Current theme
                      </p>
                      <div className="mt-2 h-2 w-3/4 rounded bg-slate-200"></div>
                    </div>
                    <div className="rounded-2xl border border-blue-100 bg-blue-50/75 p-3">
                      <p className="text-xs uppercase tracking-widest text-blue-700">
                        Next prompt
                      </p>
                      <div className="mt-2 space-y-1.5">
                        <div className="h-2 w-full rounded bg-blue-200"></div>
                        <div className="h-2 w-2/3 rounded bg-blue-200"></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </Reveal>

          <Reveal delay={120}>
            <section
              className="rounded-3xl border border-slate-200 bg-white/80 p-6 text-center"
              style={visualCardStyle}
            >
              <h2
                className="mt-2 text-2xl font-black tracking-tight text-slate-800"
                style={{ fontFamily: "var(--font-display)" }}
              >
                Access the System
              </h2>
              <p className="mt-3 max-w-2xl mx-auto text-sm text-slate-600 leading-relaxed">
                Use the portal to continue into the workspace that matches your role.
              </p>
              <div className="mt-5">
                <Link
                  href="/portal"
                  className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-5 py-3 text-sm font-semibold text-blue-700 transition-colors duration-200 hover:text-blue-800"
                >
                  Open Portal
                  <svg
                    className="w-4 h-4"
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
                </Link>
              </div>
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
};

const visualCardStyle: React.CSSProperties = {
  boxShadow: "0 18px 36px rgba(15, 23, 42, 0.08)",
};

function SmallKeyStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white/70 px-3 py-2">
      <p className="text-xs uppercase tracking-widest text-slate-400">{label}</p>
      <p className="mt-1 font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/80 px-3 py-2">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function StatusMark({ status }: { status: string }) {
  const styles = {
    ASSIGNED: "border-sky-200 bg-sky-100 text-sky-900",
  };

  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${styles[status as keyof typeof styles] ?? "border-slate-200 bg-slate-100 text-slate-700"
        }`}
    >
      {status}
    </span>
  );
}

function BlacklineMeta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-slate-200 bg-white px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-800">{value}</p>
    </div>
  );
}

function PrimaryLink({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-blue-700 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-white shadow-sm">
      {label}
      <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17L17 7M17 7H9M17 7v8" />
      </svg>
    </span>
  );
}