"use client";

import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Card } from "@/components/ui/Card";

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
  "Tell me about a project where you built something using this technology from scratch.",
  "Walk me through a time you had to debug or fix something that wasn’t working—what steps did you take?",
  "What’s one technical concept you’ve learned recently, and how have you applied it in practice?",
];

export function Page5InterviewQuestionsSandbox() {
  return (
    <div
      className={[
        spaceGrotesk.variable,
        plexSans.variable,
        "min-h-screen bg-[linear-gradient(180deg,#eef0f5_0%,#dfe3eb_22%,#d8dbe2_22%,#cfd5df_62%,#dfe3eb_62%,#eef0f5_100%)] text-[#111111]",
      ].join(" ")}
      style={{ fontFamily: "var(--font-reports-plex)" }}
    >
      <div className="min-h-screen bg-[#D8DBE2] text-[#111111]">
        <AdminDesignLabNavbar activeItem="Reports" />

        <main className="mx-auto max-w-[92rem] px-5 py-7 md:px-8 md:py-8">
          <div className="space-y-6">
            <section className="overflow-hidden rounded-[2rem] border border-[#727D97] bg-[linear-gradient(135deg,#c9d0dc_0%,#d8dbe2_40%,#ced4df_100%)] p-6">
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#5F6C86]">
                  <span className="inline-flex items-center gap-2 text-[#111111]">Design lab preview</span>
                </div>
                <div className="space-y-3">
                  <h1
                    className="max-w-4xl text-[3rem] leading-[0.92] tracking-[-0.07em] text-[#111111] md:text-[3.6rem]"
                    style={{ fontFamily: "var(--font-reports-space)" }}
                  >
                    Page 5 interview questions slice
                  </h1>
                  <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                    Detached mock of the real Page 5 question-group layout using simplified copy for landing-page visuals.
                  </p>
                </div>
              </div>
            </section>

            <Card
              title="Interview Questions"
              description="Question groups generated from synthesized themes."
              eyebrow={null}
            >
              <div className="space-y-4">
                <article className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex rounded-full bg-[color:var(--signal-soft)] px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-[color:var(--signal)]">
                      Technical Depth vs Practice
                    </span>
                    <p className="text-base font-semibold text-[color:var(--ink)]">Testing practical depth</p>
                  </div>
                  <ol className="mt-4 grid gap-3">
                    {QUESTIONS.map((question, questionIndex) => (
                      <li
                        key={question}
                        className="grid gap-3 rounded-[1rem] border border-slate-200 bg-slate-50/72 px-4 py-3 md:grid-cols-[2rem_1fr]"
                      >
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[color:var(--accent-soft)] text-xs font-bold text-[color:var(--accent-strong)]">
                          {questionIndex + 1}
                        </span>
                        <span className="text-sm leading-7 text-[color:var(--ink)]">{question}</span>
                      </li>
                    ))}
                  </ol>
                </article>
              </div>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
