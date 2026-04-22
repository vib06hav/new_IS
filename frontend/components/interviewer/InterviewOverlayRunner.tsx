"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Minus, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { usePortalSession } from "@/components/auth/PortalSessionProvider";
import { finishInterviewWorkspace, isApiErrorStatus, saveInterviewWorkspace } from "@/lib/api";
import { clearInterviewDraft, readInterviewDraft, writeInterviewDraft } from "@/lib/interviewDrafts";
import type {
  InterviewQuestionStatus,
  InterviewWorkspaceQuestion,
  InterviewWorkspaceSummary,
  InterviewWorkspaceTheme,
} from "@/lib/types";

const STATUS_CYCLE: InterviewQuestionStatus[] = ["unasked", "satisfactory", "mixed", "unsatisfactory"];
const CUSTOM_THEME_ID = "__custom_group__";
const CUSTOM_THEME_TITLE = "Custom";

export function InterviewOverlayRunner({
  applicationId,
  initialWorkspace,
}: {
  applicationId: string;
  initialWorkspace: InterviewWorkspaceSummary;
}) {
  const router = useRouter();
  const { authState, clearWorkflowActive, markWorkflowActive, revalidate } = usePortalSession();
  const [workspace, setWorkspace] = useState(() => {
    const draft = readInterviewDraft(applicationId, "overlay");
    if (!draft) {
      return {
        ...initialWorkspace,
        content: ensureCustomThemePresence(initialWorkspace.content),
      };
    }

    return {
      ...initialWorkspace,
      content: ensureCustomThemePresence(draft),
    };
  });
  const [savingState, setSavingState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [finishBusy, setFinishBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autosaveFrozen, setAutosaveFrozen] = useState(false);
  const [draftRestored, setDraftRestored] = useState(() => Boolean(readInterviewDraft(applicationId, "overlay")));
  const saveTimerRef = useRef<number | null>(null);
  const firstRenderRef = useRef(true);
  const serializedContent = JSON.stringify(workspace.content);
  const initialQuestionIdsRef = useRef(
    new Set(initialWorkspace.content.themes.flatMap((theme) => theme.questions.map((question) => question.id))),
  );

  const totalQuestions = useMemo(
    () => workspace.content.themes.reduce((sum, theme) => sum + theme.questions.length, 0),
    [workspace.content.themes],
  );
  const askedQuestions = useMemo(
    () =>
      workspace.content.themes.reduce(
        (sum, theme) => sum + theme.questions.filter((question) => question.status !== "unasked").length,
        0,
      ),
    [workspace.content.themes],
  );

  useEffect(() => {
    markWorkflowActive();
    return () => {
      clearWorkflowActive();
    };
  }, [clearWorkflowActive, markWorkflowActive]);

  useEffect(() => {
    writeInterviewDraft(applicationId, "overlay", workspace.content);
  }, [applicationId, workspace.content]);

  useEffect(() => {
    if (firstRenderRef.current) {
      firstRenderRef.current = false;
      return;
    }

    if (autosaveFrozen) {
      return;
    }

    if (saveTimerRef.current) {
      window.clearTimeout(saveTimerRef.current);
    }

    setSavingState("saving");
    saveTimerRef.current = window.setTimeout(async () => {
      try {
        const nextWorkspace = await saveInterviewWorkspace(applicationId, workspace.content);
        const mergedContent = ensureCustomThemePresence(
          mergeOverlayDraftContent(workspace.content, nextWorkspace.content),
        );
        setWorkspace({
          ...nextWorkspace,
          content: mergedContent,
        });
        clearInterviewDraft(applicationId, "overlay");
        setDraftRestored(false);
        setSavingState("saved");
      } catch (saveError) {
        setSavingState("error");
        if (isApiErrorStatus(saveError, [401, 403])) {
          setAutosaveFrozen(true);
          console.warn("[overlay] auth-related autosave failure", {
            applicationId,
            state: authState,
            error: saveError instanceof Error ? saveError.message : "Unknown auth error",
          });
          setError("Session expired while the overlay was autosaving. Your draft was preserved locally. Sign in again, then reopen or resume autosave.");
        } else {
          setError(saveError instanceof Error ? saveError.message : "Unable to autosave interview overlay.");
        }
      }
    }, 500);

    return () => {
      if (saveTimerRef.current) {
        window.clearTimeout(saveTimerRef.current);
      }
    };
  }, [applicationId, authState, autosaveFrozen, serializedContent, workspace.content]);

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

  function createOverlayQuestion(themeId: string, order: number): InterviewWorkspaceQuestion {
    return {
      id: `${themeId}-q-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      text: "",
      source: "custom",
      status: "unasked",
      note: "",
      order,
    };
  }

  function addQuestion(themeId: string) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: [...theme.questions, createOverlayQuestion(themeId, theme.questions.length)],
    }));
  }

  function removeQuestion(themeId: string, questionId: string) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: theme.questions
        .filter((question) => question.id !== questionId)
        .map((question, index) => ({ ...question, order: index })),
    }));
  }

  function ensureCustomTheme(currentWorkspace: InterviewWorkspaceSummary) {
    const existingCustomTheme = currentWorkspace.content.themes.find((theme) => theme.id === CUSTOM_THEME_ID);
    if (existingCustomTheme) {
      return existingCustomTheme;
    }

    return {
      id: CUSTOM_THEME_ID,
      source: "custom" as const,
      title: CUSTOM_THEME_TITLE,
      unifying_axis: "",
      interview_direction: "",
      question_group_title: CUSTOM_THEME_TITLE,
      questions: [],
    };
  }

  function handleAddCustomQuestion() {
    setWorkspace((current) => {
      const existingCustomTheme = current.content.themes.find((theme) => theme.id === CUSTOM_THEME_ID);
      const customTheme = existingCustomTheme ?? ensureCustomTheme(current);
      const nextQuestion = createOverlayQuestion(CUSTOM_THEME_ID, customTheme.questions.length);

      const nextThemes = existingCustomTheme
        ? current.content.themes.map((theme) =>
            theme.id === CUSTOM_THEME_ID ? { ...theme, questions: [...theme.questions, nextQuestion] } : theme,
          )
        : [...current.content.themes, { ...customTheme, questions: [nextQuestion] }];

      return {
        ...current,
        content: {
          ...current.content,
          themes: nextThemes,
        },
      };
    });
  }

  const orderedThemes = useMemo(() => {
    const nonCustomThemes = workspace.content.themes.filter((theme) => theme.id !== CUSTOM_THEME_ID);
    const customTheme =
      workspace.content.themes.find((theme) => theme.id === CUSTOM_THEME_ID) ??
      ensureCustomTheme({ ...workspace, content: workspace.content });
    return customTheme ? [...nonCustomThemes, customTheme] : nonCustomThemes;
  }, [workspace, workspace.content.themes]);

  function isOverlayCreatedQuestion(questionId: string) {
    return !initialQuestionIdsRef.current.has(questionId);
  }

  async function ensureWorkflowSession() {
    if (authState === "authenticated") {
      return true;
    }

    const snapshot = await revalidate({ force: true, reason: "overlay-finish-retry" });
    return snapshot.authState === "authenticated";
  }

  async function handleResumeAutosave() {
    const sessionReady = authState === "authenticated" ? true : await ensureWorkflowSession();
    if (!sessionReady) {
      setError("Your session is still unavailable. The overlay draft is preserved locally and can be retried after sign-in is restored.");
      return;
    }

    setAutosaveFrozen(false);
    setError(null);
    setSavingState("saving");
    try {
      const nextWorkspace = await saveInterviewWorkspace(applicationId, workspace.content);
      const mergedContent = ensureCustomThemePresence(
        mergeOverlayDraftContent(workspace.content, nextWorkspace.content),
      );
      setWorkspace({
        ...nextWorkspace,
        content: mergedContent,
      });
      clearInterviewDraft(applicationId, "overlay");
      setDraftRestored(false);
      setSavingState("saved");
    } catch (saveError) {
      setSavingState("error");
      if (isApiErrorStatus(saveError, [401, 403])) {
        setAutosaveFrozen(true);
        setError("Session expired again before the overlay could save. The local draft is still preserved.");
      } else {
        setError(saveError instanceof Error ? saveError.message : "Unable to resume autosave.");
      }
    }
  }

  async function handleFinish() {
    if (!(await ensureWorkflowSession())) {
      setError("We could not re-establish your session yet. The overlay draft is preserved locally, so you can retry after signing in again.");
      return;
    }

    setFinishBusy(true);
    setError(null);
    try {
      const normalizedContent = normalizeAuthoredContent(workspace.content);
      const nextWorkspace = await finishInterviewWorkspace(applicationId, normalizedContent);
      setWorkspace(nextWorkspace);
      clearInterviewDraft(applicationId, "overlay");
      setDraftRestored(false);
      if (window.opener && !window.opener.closed) {
        window.opener.location.href = `/interviewer/applications/${applicationId}/postgame`;
        window.close();
        return;
      }
      router.push(`/interviewer/applications/${applicationId}/postgame`);
    } catch (finishError) {
      if (isApiErrorStatus(finishError, [401, 403])) {
        setAutosaveFrozen(true);
        setError("Your session expired before finishing the interview. The overlay draft has been preserved locally.");
      } else {
        setError(finishError instanceof Error ? finishError.message : "Unable to finish interview.");
      }
    } finally {
      setFinishBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#eff6ff_0%,#f8fafc_45%,#ffffff_100%)] p-4 text-slate-900">
      <div className="mx-auto flex max-w-[28rem] flex-col gap-4">
        <section className="rounded-[1.6rem] border border-slate-200 bg-white/90 p-4 shadow-[0_18px_36px_rgba(15,23,42,0.12)] backdrop-blur">
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold tracking-tight text-slate-900">Interview overlay</h1>
                <p className="mt-1 text-sm text-slate-600">
                  Mark questions as you go and add custom prompts without leaving the conversation.
                </p>
              </div>
              <Button disabled={finishBusy} onClick={() => void handleFinish()} size="sm">
                {finishBusy ? "Finishing..." : "Finish interview"}
              </Button>
            </div>

            <div className="grid gap-2 sm:grid-cols-2">
              <MiniStat label="Questions" value={`${askedQuestions}/${totalQuestions}`} />
              <MiniStat label="Themes" value={String(workspace.content.themes.length)} />
            </div>
          </div>
        </section>

        {draftRestored ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            A locally preserved overlay draft was restored for this application.
          </p>
        ) : null}
        {error ? (
          <div className="space-y-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <p>{error}</p>
            {autosaveFrozen ? (
              <Button onClick={() => void handleResumeAutosave()} size="sm" variant="secondary">
                Resume autosave
              </Button>
            ) : null}
          </div>
        ) : null}

        <section className="space-y-3">
          {orderedThemes.map((theme, index) => (
            <details
              key={theme.id}
              className="group rounded-[1.4rem] border border-slate-200 bg-white/90 shadow-[0_18px_36px_rgba(15,23,42,0.1)] backdrop-blur"
              open={index === 0}
            >
              <summary className="cursor-pointer list-none px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{theme.question_group_title}</p>
                    <h2 className="mt-1 text-base font-semibold text-slate-900">{theme.title || CUSTOM_THEME_TITLE}</h2>
                  </div>
                  <span className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-700">
                    {theme.questions.filter((question) => question.status !== "unasked").length}/{theme.questions.length}
                  </span>
                </div>
              </summary>

              <div className="space-y-3 px-4 pb-4">
                {theme.questions.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-3 text-sm text-slate-500">
                    No questions yet. Add one to capture a prompt for this group.
                  </p>
                ) : null}
                {theme.questions
                  .slice()
                  .sort((left, right) => left.order - right.order)
                  .map((question, questionIndex) => {
                    const isOverlayCreated = isOverlayCreatedQuestion(question.id);
                    return (
                      <div key={question.id} className="rounded-[1.1rem] border border-slate-200 bg-slate-50/80 p-3">
                        <div className="flex items-start gap-3">
                          <button
                            className={`mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-full border text-sm font-bold transition ${getCycleClasses(question.status)}`}
                            onClick={() => cycleQuestionStatus(theme.id, question.id)}
                            type="button"
                          >
                            {getCycleIcon(question.status)}
                          </button>
                          <div className="min-w-0 flex-1 space-y-2">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Q{questionIndex + 1}</span>
                                <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                  {question.source}
                                </span>
                              </div>
                              {isOverlayCreated ? (
                                <button
                                  className="text-xs font-semibold text-rose-700 transition hover:text-rose-800"
                                  onClick={() => removeQuestion(theme.id, question.id)}
                                  type="button"
                                >
                                  Remove
                                </button>
                              ) : null}
                            </div>
                            {isOverlayCreated ? (
                              <textarea
                                className="min-h-24 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                                onChange={(event) =>
                                  updateQuestion(theme.id, question.id, (current) => ({ ...current, text: event.target.value }))
                                }
                                placeholder="Type question"
                                value={question.text}
                              />
                            ) : (
                              <p className="text-sm leading-6 text-slate-900">{question.text}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}

                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  onClick={() => (theme.id === CUSTOM_THEME_ID ? handleAddCustomQuestion() : addQuestion(theme.id))}
                  type="button"
                >
                  <Plus className="size-4" />
                  Add question
                </button>
              </div>
            </details>
          ))}

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

function mergeOverlayDraftContent(
  localContent: InterviewWorkspaceSummary["content"],
  remoteContent: InterviewWorkspaceSummary["content"],
) {
  const remoteThemes = new Map(remoteContent.themes.map((theme) => [theme.id, theme]));

  const mergedThemes = localContent.themes.map((localTheme) => {
    const remoteTheme = remoteThemes.get(localTheme.id);
    if (!remoteTheme) {
      return localTheme;
    }

    const remoteQuestionIds = new Set(remoteTheme.questions.map((question) => question.id));
    const draftOnlyQuestions = localTheme.questions.filter(
      (question) => question.source === "custom" && !remoteQuestionIds.has(question.id),
    );

    return {
      ...remoteTheme,
      questions: [...remoteTheme.questions, ...draftOnlyQuestions].map((question, index) => ({
        ...question,
        order: index,
      })),
    };
  });

  remoteContent.themes.forEach((remoteTheme) => {
    if (!mergedThemes.some((theme) => theme.id === remoteTheme.id)) {
      mergedThemes.push(remoteTheme);
    }
  });

  return {
    ...remoteContent,
    themes: mergedThemes,
  };
}

function normalizeAuthoredContent(content: InterviewWorkspaceSummary["content"]) {
  return {
    ...content,
    themes: content.themes
      .map((theme) => ({
        ...theme,
        questions: theme.questions
          .filter((question) => question.source !== "custom" || question.text.trim().length > 0)
          .map((question, index) => ({ ...question, order: index })),
      }))
      .filter((theme) => theme.id !== CUSTOM_THEME_ID || theme.questions.length > 0),
  };
}

function ensureCustomThemePresence(content: InterviewWorkspaceSummary["content"]) {
  if (content.themes.some((theme) => theme.id === CUSTOM_THEME_ID)) {
    return content;
  }

  return {
    ...content,
    themes: [
      ...content.themes,
      {
        id: CUSTOM_THEME_ID,
        source: "custom" as const,
        title: CUSTOM_THEME_TITLE,
        unifying_axis: "",
        interview_direction: "",
        question_group_title: CUSTOM_THEME_TITLE,
        questions: [],
      },
    ],
  };
}
