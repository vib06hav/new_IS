"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronDown, Minus, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { finishInterviewWorkspace, saveInterviewWorkspace } from "@/lib/api";
import type {
  InterviewQuestionStatus,
  InterviewWorkspaceQuestion,
  InterviewWorkspaceSummary,
  InterviewWorkspaceTheme,
} from "@/lib/types";

const STATUS_CYCLE: InterviewQuestionStatus[] = ["unasked", "satisfactory", "mixed", "unsatisfactory"];

export function InterviewOverlayRunner({
  applicationId,
  initialWorkspace,
}: {
  applicationId: string;
  initialWorkspace: InterviewWorkspaceSummary;
}) {
  const router = useRouter();
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [activeThemeIndex, setActiveThemeIndex] = useState(0);
  const [savingState, setSavingState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [finishBusy, setFinishBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const saveTimerRef = useRef<number | null>(null);
  const firstRenderRef = useRef(true);
  const serializedContent = JSON.stringify(workspace.content);

  const themes = workspace.content.themes;
  const currentTheme = themes[activeThemeIndex];

  const totalQuestions = useMemo(
    () => themes.reduce((sum, theme) => sum + theme.questions.length, 0),
    [themes],
  );
  const askedQuestions = useMemo(
    () =>
      themes.reduce(
        (sum, theme) => sum + theme.questions.filter((question) => question.status !== "unasked").length,
        0,
      ),
    [themes],
  );

  useEffect(() => {
    if (firstRenderRef.current) {
      firstRenderRef.current = false;
      return;
    }

    if (saveTimerRef.current) {
      window.clearTimeout(saveTimerRef.current);
    }

    setSavingState("saving");
    saveTimerRef.current = window.setTimeout(async () => {
      try {
        const nextWorkspace = await saveInterviewWorkspace(applicationId, workspace.content);
        setWorkspace(nextWorkspace);
        setSavingState("saved");
      } catch (saveError) {
        setSavingState("error");
        setError(saveError instanceof Error ? saveError.message : "Unable to autosave interview overlay.");
      }
    }, 500);

    return () => {
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
    };
  }, [applicationId, serializedContent]);

  function updateTheme(themeId: string, updater: (theme: InterviewWorkspaceTheme) => InterviewWorkspaceTheme) {
    setWorkspace((current) => ({
      ...current,
      content: {
        ...current.content,
        themes: current.content.themes.map((theme) => (theme.id === themeId ? updater(theme) : theme)),
      },
    }));
  }

  function updateQuestion(themeId: string, questionId: string, updater: (question: InterviewWorkspaceQuestion) => InterviewWorkspaceQuestion) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: theme.questions.map((question) => (question.id === questionId ? updater(question) : question)),
    }));
  }

  function cycleQuestionStatus(themeId: string, questionId: string) {
    updateQuestion(themeId, questionId, (question) => {
      const currentIndex = STATUS_CYCLE.indexOf(question.status);
      const nextStatus = STATUS_CYCLE[(currentIndex + 1) % STATUS_CYCLE.length];
      return { ...question, status: nextStatus };
    });
  }

  function addCustomQuestion(themeId: string) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: [
        ...theme.questions,
        {
          id: `${themeId}-q-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          text: "New custom question",
          source: "custom",
          status: "unasked",
          note: "",
          order: theme.questions.length,
        },
      ],
    }));
  }

  async function handleFinish() {
    setFinishBusy(true);
    setError(null);
    try {
      const nextWorkspace = await finishInterviewWorkspace(applicationId, workspace.content);
      setWorkspace(nextWorkspace);
      if (window.opener && !window.opener.closed) {
        window.opener.location.href = `/interviewer/applications/${applicationId}/postgame`;
        window.close();
        return;
      }
      router.push(`/interviewer/applications/${applicationId}/postgame`);
    } catch (finishError) {
      setError(finishError instanceof Error ? finishError.message : "Unable to finish interview.");
    } finally {
      setFinishBusy(false);
    }
  }

  const goToPrev = () => setActiveThemeIndex((i) => Math.max(0, i - 1));
  const goToNext = () => setActiveThemeIndex((i) => Math.min(themes.length - 1, i + 1));

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#eff6ff_0%,#f8fafc_45%,#ffffff_100%)] p-4 text-slate-900">
      <div className="mx-auto flex max-w-[28rem] flex-col gap-4">
        <section className="rounded-[1.6rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.12)] backdrop-blur">
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-blue-700">Interview overlay</p>
                <h1 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">Live runner</h1>
                <p className="mt-1 text-sm text-slate-600">
                  Mark questions as you go and add custom prompts.
                </p>
              </div>
              <Button disabled={finishBusy} onClick={() => void handleFinish()} size="sm">
                {finishBusy ? "Finishing..." : "Finish interview"}
              </Button>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <MiniStat label="Progress" value={`${askedQuestions} / ${totalQuestions} Qs`} />
              <MiniStat label="Autosave" value={getSaveLabel(savingState)} />
            </div>
          </div>
        </section>

        {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-3 rounded-[1.4rem] border border-slate-200 bg-white/95 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.1)] backdrop-blur">
            <div className="flex items-center gap-3">
              <button
                className="flex size-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-white"
                disabled={activeThemeIndex === 0}
                onClick={goToPrev}
                type="button"
              >
                <ArrowLeft className="size-4" />
              </button>
              <div className="min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">
                  Theme {activeThemeIndex + 1} of {themes.length}
                </p>
                <h2 className="line-clamp-1 text-base font-bold text-slate-900">{currentTheme?.title}</h2>
              </div>
            </div>
            <button
              className="flex size-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:opacity-30 disabled:hover:bg-white"
              disabled={activeThemeIndex === themes.length - 1}
              onClick={goToNext}
              type="button"
            >
              <ArrowRight className="size-4" />
            </button>
          </div>

          <div className="animate-in fade-in slide-in-from-right-2 duration-300">
            <article className="rounded-[1.4rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.1)] backdrop-blur">
              <div className="mb-4 flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700">{currentTheme?.question_group_title}</p>
                <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-700">
                  {currentTheme?.questions.filter((q) => q.status !== "unasked").length}/{currentTheme?.questions.length} asked
                </span>
              </div>

              <div className="space-y-3">
                {currentTheme?.questions
                  .slice()
                  .sort((left, right) => left.order - right.order)
                  .map((question, questionIndex) => (
                    <div key={question.id} className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 p-3">
                      <div className="flex items-start gap-3">
                        <button
                          className={`mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-full border text-sm font-bold transition ${getCycleClasses(question.status)}`}
                          onClick={() => cycleQuestionStatus(currentTheme.id, question.id)}
                          type="button"
                        >
                          {getCycleIcon(question.status)}
                        </button>
                        <div className="min-w-0 flex-1 space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Q{questionIndex + 1}</span>
                            <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                              {question.source}
                            </span>
                          </div>
                          {question.source === "custom" ? (
                            <textarea
                              className="min-h-20 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm leading-6 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                              onChange={(event) =>
                                updateQuestion(currentTheme.id, question.id, (current) => ({ ...current, text: event.target.value }))
                              }
                              placeholder="Type your custom question"
                              value={question.text}
                            />
                          ) : (
                            <p className="text-sm leading-6 text-slate-900">{question.text}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}

                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  onClick={() => addCustomQuestion(currentTheme.id)}
                  type="button"
                >
                  <Plus className="size-4" />
                  Add custom question
                </button>
              </div>
            </article>
          </div>
        </section>
      </div>
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

function getSaveLabel(state: "idle" | "saving" | "saved" | "error") {
  if (state === "saving") return "Saving";
  if (state === "saved") return "Saved";
  if (state === "error") return "Error";
  return "Ready";
}

function getCycleClasses(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "unsatisfactory") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-300 bg-white text-slate-500 hover:bg-slate-50";
}

function getCycleIcon(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return <Check className="size-4" />;
  if (status === "mixed") return <Minus className="size-4" />;
  if (status === "unsatisfactory") return <X className="size-4" />;
  return <span className="inline-block size-2 rounded-full border border-current" />;
}
