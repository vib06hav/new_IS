"use client";

import { useState } from "react";

const THEMES = [
  "Technical Depth vs Practice",
  "Interdisciplinary Motivation",
];

const QUESTIONS = [
  "Tell me about a project where you built something using this technology from scratch.",
  "Walk me through a time you had to debug or fix something that wasn't working-what steps did you take?",
  "What's one technical concept you've learned recently, and how have you applied it in practice?",
];

export function LandingPreparationModule() {
  const [tab, setTab] = useState<"focus" | "questions">("focus");

  return (
    <div className="overflow-hidden rounded-[1.8rem] border border-slate-200 bg-white/92 shadow-[0_20px_44px_rgba(15,23,42,0.08)]">
      <div className="border-b border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.92),rgba(255,255,255,0.98))] px-4 py-4 md:px-5">
        <div className="inline-flex flex-wrap rounded-full border border-slate-200 bg-white p-1 shadow-[0_10px_20px_rgba(15,23,42,0.05)]">
          <button
            type="button"
            onClick={() => setTab("focus")}
            className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
              tab === "focus"
                ? "bg-blue-700 text-white shadow-[0_10px_22px_rgba(37,99,235,0.24)]"
                : "text-slate-600 hover:text-blue-700"
            }`}
          >
            Focus Areas
          </button>
          <button
            type="button"
            onClick={() => setTab("questions")}
            className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
              tab === "questions"
                ? "bg-blue-700 text-white shadow-[0_10px_22px_rgba(37,99,235,0.24)]"
                : "text-slate-600 hover:text-blue-700"
            }`}
          >
            Interview Questions
          </button>
        </div>
      </div>

      <div className="min-h-[31.5rem] p-4 md:min-h-[27.5rem] md:p-5">
        {tab === "focus" ? <FocusAreasSlice /> : <InterviewQuestionsSlice />}
      </div>
    </div>
  );
}

function FocusAreasSlice() {
  return (
    <div className="grid h-full gap-5 lg:grid-cols-[14rem_minmax(0,1fr)] xl:grid-cols-[15rem_minmax(0,1fr)]">
      <section className="space-y-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Themes</p>
        {THEMES.map((theme, index) => {
          const active = index === 0;
          return (
            <div
              key={theme}
              className={`rounded-[1.25rem] border p-4 ${
                active
                  ? "border-blue-200 bg-[linear-gradient(145deg,rgba(239,246,255,0.98),rgba(255,255,255,0.94))] shadow-[0_18px_34px_rgba(15,23,42,0.08)]"
                  : "border-slate-200 bg-white/80 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
              }`}
            >
              <p className="text-sm font-semibold leading-6 text-slate-900">{theme}</p>
            </div>
          );
        })}
      </section>

      <section className="flex h-full flex-col gap-4">
        <article className="rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.96),rgba(239,246,255,0.88),rgba(255,255,255,0.9))] p-5 shadow-[0_18px_34px_rgba(15,23,42,0.08)]">
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Interview Focus</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-slate-900">
                Technical Depth vs Practice
              </h3>
            </div>
            <p className="text-sm leading-7 text-slate-600">
              Strong interest in technology, but limited evidence of hands-on building.
            </p>
            <div className="rounded-[1rem] bg-blue-50 px-4 py-3 text-sm leading-7 text-slate-900">
              <span className="font-semibold">Interview direction:</span>{" "}
              Probe whether interest has translated into real projects or practical work.
            </div>
          </div>
        </article>

        <article className="flex-1 rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]">
          <div className="space-y-2">
            <p className="text-base font-semibold text-slate-900">Concept without execution</p>
            <p className="text-sm leading-7 text-slate-700">
              Talks about technology concepts confidently but lacks concrete examples of building or coding.
            </p>
          </div>
        </article>
      </section>
    </div>
  );
}

function InterviewQuestionsSlice() {
  return (
    <div className="flex h-full flex-col">
      <article className="flex h-full flex-col rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-blue-700">
            Technical Depth vs Practice
          </span>
          <p className="text-base font-semibold text-slate-900">Testing practical depth</p>
        </div>
        <ol className="mt-4 grid flex-1 gap-3 lg:grid-cols-2">
          {QUESTIONS.map((question, questionIndex) => (
            <li
              key={question}
              className="grid content-start gap-3 rounded-[1rem] border border-slate-200 bg-slate-50/72 px-4 py-3 md:grid-cols-[2rem_1fr]"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                {questionIndex + 1}
              </span>
              <span className="text-sm leading-7 text-slate-900">{question}</span>
            </li>
          ))}
        </ol>
      </article>
    </div>
  );
}
