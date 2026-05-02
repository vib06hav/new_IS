"use client";

import { useState } from "react";
import { Check, Minus, X } from "lucide-react";
import { IBM_Plex_Sans, Space_Grotesk } from "next/font/google";
import { AdminDesignLabNavbar } from "@/components/design-lab/AdminDesignLabNavbar";
import { Button } from "@/components/ui/Button";
import type { InterviewQuestionStatus } from "@/lib/types";

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

const STATUS_CYCLE: InterviewQuestionStatus[] = ["unasked", "satisfactory", "mixed", "unsatisfactory"];

const INITIAL_QUESTIONS = [
  {
    id: "q1",
    text: "Tell me about a project where you built something using this technology from scratch.",
    status: "satisfactory" as InterviewQuestionStatus,
  },
  {
    id: "q2",
    text: "Walk me through a time you had to debug or fix something that wasn’t working—what steps did you take?",
    status: "unasked" as InterviewQuestionStatus,
  },
  {
    id: "q3",
    text: "What’s one technical concept you’ve learned recently, and how have you applied it in practice?",
    status: "unasked" as InterviewQuestionStatus,
  },
];

export function InterviewOverlaySandbox() {
  const [questions, setQuestions] = useState(INITIAL_QUESTIONS);

  function cycleQuestionStatus(questionId: string) {
    setQuestions((current) =>
      current.map((question) =>
        question.id === questionId
          ? { ...question, status: getNextStatus(question.status) }
          : question,
      ),
    );
  }

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

        <main className="mx-auto max-w-[46rem] px-5 py-7 md:px-8 md:py-8">
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
                    Interview overlay slice
                  </h1>
                  <p className="max-w-3xl text-sm leading-7 text-[#49536B]">
                    Detached mock of the live overlay with one theme and three questions for landing-page motion tests.
                  </p>
                </div>
              </div>
            </section>

            <div className="mx-auto flex max-w-[28rem] flex-col gap-4">
              <section className="rounded-[1.6rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.12)] backdrop-blur">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h1 className="text-xl font-semibold tracking-tight text-slate-900">Interview Overlay</h1>
                  </div>
                  <Button size="sm" type="button">
                    Finish interview
                  </Button>
                </div>
              </section>

              <section className="space-y-3">
                <details
                  className="group rounded-[1.4rem] border border-slate-200 bg-white/90 shadow-[0_18px_36px_rgba(15,23,42,0.1)] backdrop-blur"
                  open
                >
                  <summary className="list-none px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Interview Questions</p>
                        <h2 className="mt-1 text-base font-semibold text-slate-900">Technical Depth vs Practice</h2>
                      </div>
                    </div>
                  </summary>

                  <div className="space-y-3 px-4 pb-4">
                    {questions.map((question, questionIndex) => (
                      <div key={question.id} className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 p-3">
                        <div className="flex items-start gap-3">
                          <button
                            className={`mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-full border text-sm font-bold transition ${getCycleClasses(question.status)}`}
                            onClick={() => cycleQuestionStatus(question.id)}
                            type="button"
                          >
                            {getCycleIcon(question.status)}
                          </button>
                          <div className="min-w-0 flex-1 space-y-3">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Q{questionIndex + 1}</span>
                              <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                generated
                              </span>
                            </div>
                            <p className="text-sm leading-6 text-slate-900">{question.text}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              </section>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function getCycleClasses(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "unsatisfactory") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-200 bg-white text-slate-500";
}

function getCycleIcon(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return <Check className="size-4" />;
  if (status === "mixed") return <Minus className="size-4" />;
  if (status === "unsatisfactory") return <X className="size-4" />;
  return <span className="text-base leading-none">•</span>;
}

function getNextStatus(status: InterviewQuestionStatus) {
  const currentIndex = STATUS_CYCLE.indexOf(status);
  return STATUS_CYCLE[(currentIndex + 1) % STATUS_CYCLE.length];
}
