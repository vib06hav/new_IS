"use client";

import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { NotebookPen } from "lucide-react";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-reports-space",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-reports-plex",
});

const QUESTIONS = [
  {
    status: "Satisfied",
    text: "Tell me about a project where you built something using this technology from scratch.",
    note: "Described a full project build with clear ownership and practical execution.",
  },
  {
    status: "Mixed",
    text: "Walk me through a time you had to debug or fix something that wasn’t working—what steps did you take?",
    note: "Good debugging sequence, but the final explanation stayed a little high level.",
  },
  {
    status: "Unasked",
    text: "What’s one technical concept you’ve learned recently, and how have you applied it in practice?",
    note: "Not covered in the live interview.",
  },
];

export function FinalReportSummarySandbox() {
  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        "min-h-screen bg-white text-slate-950",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="min-h-screen bg-white text-slate-950">
        <AdminDesignLabNavbar activeItem="Reports" />

        <main className="mx-auto max-w-[88rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-4">
            <section className="rounded-[1.55rem] border border-slate-200 bg-white/80 px-5 py-4 shadow-[0_12px_24px_rgba(15,23,42,0.07)] backdrop-blur-sm">
              <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-slate-500">
                <span className="inline-flex items-center gap-2 text-slate-800">
                  <NotebookPen className="size-3.5" />
                  Post-Interview
                </span>
              </div>
              <div className="mt-2.5 space-y-2">
                <h1 className="max-w-4xl text-[1.9rem] font-black leading-[0.96] tracking-tight text-slate-800 md:text-[2.3rem]">
                  Final Interview Report
                </h1>
                <p className="max-w-3xl text-[0.9rem] leading-6 text-slate-600">
                  Final interviewer feedback and question outcomes captured after interview completion.
                </p>
              </div>
            </section>

            <section className="rounded-[1.3rem] border border-slate-200 bg-white/88 p-4 shadow-[0_14px_28px_rgba(15,23,42,0.08)]">
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Interview Summary</h2>
              <p className="mt-2.5 text-sm leading-7 text-slate-800">
                Strong conceptual interest and clear technical communication. The interview surfaced genuine motivation,
                though practical building experience still needs deeper validation across hands-on examples.
              </p>
            </section>

            <section className="rounded-[1.3rem] border border-slate-200 bg-white/88 p-4 shadow-[0_14px_28px_rgba(15,23,42,0.08)]">
              <div className="space-y-2">
                <h2 className="text-xl font-semibold tracking-[-0.03em] text-slate-900">Question Outcomes</h2>
                <p className="text-sm leading-6 text-slate-600">A compressed mock of the published question outcomes view.</p>
              </div>

              <div className="mt-3.5 space-y-3">
                {QUESTIONS.map((question, index) => (
                  <article
                    key={question.text}
                    className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-3.5 py-3 shadow-[0_8px_18px_rgba(15,23,42,0.04)]"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                        Q{index + 1}
                      </span>
                      <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getStatusClasses(question.status)}`}>
                        {question.status}
                      </span>
                    </div>
                    <p className="mt-3 truncate text-sm font-medium leading-6 text-slate-900" title={question.text}>
                      {question.text}
                    </p>
                    <p className="mt-1.5 line-clamp-2 text-sm leading-6 text-slate-700">{question.note}</p>
                  </article>
                ))}
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}

function getStatusClasses(status: string) {
  if (status === "Satisfied") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "Mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "Unsatisfied") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-200 bg-slate-100 text-slate-700";
}
