import Link from "next/link";
import type { CSSProperties, ReactNode } from "react";
import { Libre_Franklin, IBM_Plex_Sans } from "next/font/google";
import { LandingPreparationModule } from "@/components/landing/LandingPreparationModule";
import { LandingFinalReportSlice } from "@/components/landing/LandingFinalReportSlice";
import { LandingPostgameRefineSlice } from "@/components/landing/LandingPostgameRefineSlice";
import { LandingAdminControlLayer } from "@/components/landing/LandingAdminControlLayer";
import { LandingReportChatSlice } from "@/components/landing/LandingReportChatSlice";
import { LandingInterviewOverlaySlice } from "@/components/landing/LandingInterviewOverlaySlice";

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

export default function LandingPage() {
  return (
    <div
      className={`min-h-screen text-slate-900 ${libreFranklin.variable} ${ibmPlexSans.variable}`}
      style={{ fontFamily: "var(--font-body)" }}
    >
      <style>{`
        :root {
          --font-display: ${libreFranklin.style.fontFamily};
          --font-body: ${ibmPlexSans.style.fontFamily};
        }
      `}</style>

      <div style={bodyStyle}>
        <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/78 px-5 py-4 backdrop-blur-md md:px-8 xl:px-10">
          <div className="mx-auto flex w-full max-w-[88rem] items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 shadow-sm">
                <svg
                  className="h-6 w-6 text-blue-900"
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
                <span className="absolute -bottom-1 -right-1 rounded border border-blue-200 bg-white px-1 text-[10px] font-bold text-blue-900">
                  IS
                </span>
              </div>
              <span className="text-xl font-semibold tracking-tight text-slate-800">Interview Standardiser</span>
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
                Sign in
              </Link>
              <Link
                href="/support"
                className="rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-600 transition-colors duration-200 hover:text-blue-700"
              >
                Request a demo
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1">
          <section className="relative overflow-hidden px-5 pb-16 pt-16 text-center md:px-8 md:pt-24 xl:px-10">
            <div className="pointer-events-none absolute inset-0">
              <div className="absolute left-[10%] top-[10%] h-64 w-64 rounded-full bg-blue-100/70 blur-3xl" />
              <div className="absolute right-[8%] top-[14%] h-72 w-72 rounded-full bg-sky-100/60 blur-3xl" />
            </div>

            <div className="relative mx-auto max-w-5xl space-y-8">
              <div className="space-y-5">
                <h1
                  className="mx-auto max-w-4xl text-5xl font-black leading-[0.98] tracking-[-0.05em] text-slate-950 md:text-[4.65rem]"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Know what to ask in every interview
                </h1>
                <p className="mx-auto max-w-3xl text-lg leading-[1.75] text-slate-600 md:text-xl">
                  Standardise how interviews are prepared, run, and written up with a guided flow built from applicant material, so interviewers stay in control and every candidate is evaluated consistently.
                </p>
              </div>

              <div className="space-y-4">
                <p className="text-sm font-medium text-slate-600">See how your interviews could run with structure</p>
                <div className="flex justify-center">
                  <Link
                    href="/support"
                    className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-6 py-3 text-sm font-semibold text-white shadow-[0_20px_40px_rgba(37,99,235,0.28)] transition hover:bg-blue-800"
                  >
                    Request a demo
                    <ArrowIcon />
                  </Link>
                </div>
              </div>
            </div>
          </section>

          <TransitionLine>
            This isn't just guidance for one interview-it ensures every interview follows the same structure.
          </TransitionLine>

          <section className="px-5 py-10 md:px-8 xl:px-10">
            <div className="mx-auto grid w-full max-w-[88rem] gap-10 xl:grid-cols-[minmax(21rem,0.76fr)_minmax(0,1.24fr)] xl:items-center">
              <div className="max-w-2xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Interviewers start with a structured interview plan
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Applicant material is turned into focus areas and question groups, so for every application, interviewers begin with direction instead of starting from a blank page.
                </p>
              </div>

              <LandingPreparationModule />
            </div>
          </section>

          <TransitionLine>
            And you can explore and navigate it with a built-in copilot. Surface details, clarify focus areas, and get guidance as you move through the interview workflow.
          </TransitionLine>

          <section className="px-5 py-12 md:px-8 xl:px-10">
            <div className="mx-auto grid w-full max-w-[88rem] gap-10 xl:grid-cols-[minmax(0,1.04fr)_minmax(22rem,0.96fr)] xl:items-center">
              <LandingReportChatSlice />

              <div className="max-w-2xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Use a copilot to explore and navigate the workflow
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Use the copilot to surface key details, clarify focus areas, and get guidance as you move through the report, the live interview, and the final write-up without losing control of the process.
                </p>
              </div>
            </div>
          </section>

          <TransitionLine>Then it carries directly into the live interview.</TransitionLine>

          <section className="px-5 py-12 md:px-8 xl:px-10">
            <div className="mx-auto grid w-full max-w-[88rem] gap-10 xl:grid-cols-[minmax(0,1.04fr)_minmax(22rem,0.96fr)] xl:items-center">
              <div className="max-w-2xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Every interview follows a guided, structured flow
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Interviewers move through questions, capture outcomes in the moment, and stay in control of the
                  conversation without losing structure.
                </p>
              </div>

              <LandingInterviewOverlaySlice />
            </div>
          </section>

          <TransitionLine>After the interview, it continues into review and final write-up.</TransitionLine>

          <section className="px-5 py-12 md:px-8 xl:px-10">
            <div className="mx-auto grid w-full max-w-[88rem] gap-10 xl:grid-cols-[minmax(0,1.04fr)_minmax(22rem,0.96fr)] xl:items-center">
              <div className="max-w-2xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Refine interview notes with AI before finalising
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Interviewers can edit their notes, refine summaries with AI, and shape the final write-up before it becomes part of the report.
                </p>
              </div>

              <LandingPostgameRefineSlice />
            </div>
          </section>

          <section className="px-5 py-12 md:px-8 xl:px-10">
            <div className="mx-auto grid w-full max-w-[88rem] gap-10 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] xl:items-center">
              <LandingFinalReportSlice />

              <div className="max-w-2xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Every interview produces a consistent, reviewable record
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  The final report carries forward the summary and question outcomes in a format that is easier to review, compare, and revisit later.
                </p>
              </div>
            </div>
          </section>

          <section className="px-5 py-12 md:px-8 xl:px-10">
            <div className="mx-auto max-w-[88rem] space-y-6">
              <div className="max-w-3xl space-y-4">
                <h2
                  className="text-3xl font-black tracking-[-0.04em] text-slate-950 md:text-4xl"
                  style={{ fontFamily: "var(--font-display)" }}
                >
                  Control the interview workflow across your team
                </h2>
                <p className="text-base leading-7 text-slate-600">
                  Generate interview-ready reports, assign interviewers when candidates are ready, and review completed outputs from one shared workflow.
                </p>
              </div>

              <LandingAdminControlLayer />
            </div>
          </section>

          <section className="px-5 pb-20 pt-6 md:px-8 xl:px-10">
            <div className="mx-auto w-full max-w-5xl rounded-[2.2rem] border border-slate-200/85 bg-[linear-gradient(135deg,rgba(219,234,254,0.46),rgba(255,255,255,0.92),rgba(239,246,255,0.82))] px-6 py-10 text-center shadow-[0_24px_54px_rgba(15,23,42,0.08)] backdrop-blur md:px-10 md:py-12">
              <p className="text-sm font-medium text-slate-600">See how your interviews could run with structure</p>
              <div className="mt-5">
                <Link
                  href="/support"
                  className="inline-flex items-center gap-2 rounded-full bg-blue-700 px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_36px_rgba(37,99,235,0.24)] transition hover:bg-blue-800"
                >
                  Request a demo
                  <ArrowIcon />
                </Link>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

const bodyStyle: CSSProperties = {
  background:
    "radial-gradient(circle at 12% 12%, rgba(219,234,254,0.52), transparent 18%), radial-gradient(circle at 88% 12%, rgba(224,231,255,0.46), transparent 16%), radial-gradient(circle at 22% 82%, rgba(191,219,254,0.32), transparent 18%), linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)",
  backgroundAttachment: "fixed",
};

function TransitionLine({ children }: { children: ReactNode }) {
  return (
    <section className="px-6 py-6 text-center md:px-10">
      <p className="mx-auto max-w-4xl text-base font-medium leading-8 text-slate-700 md:text-lg">{children}</p>
    </section>
  );
}

function ArrowIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}
