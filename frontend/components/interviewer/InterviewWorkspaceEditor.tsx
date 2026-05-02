"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronDown, MinusCircle, Plus, Rocket, Save, Sparkles, Trash2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { usePortalSession } from "@/components/auth/PortalSessionProvider";
import {
  completeInterviewWorkspace,
  refineInterviewWorkspaceText,
  isApiErrorStatus,
  launchInterviewWorkspace,
  saveInterviewWorkspace,
} from "@/lib/api";
import { clearInterviewDraft, readInterviewDraft, writeInterviewDraft } from "@/lib/interviewDrafts";
import { openInterviewPopupPlaceholder } from "@/lib/interviewPopup";
import type {
  InterviewQuestionStatus,
  InterviewRefinementMode,
  InterviewWorkspaceQuestion,
  InterviewWorkspaceQuestionFollowUp,
  InterviewWorkspaceSummary,
  InterviewWorkspaceTheme,
} from "@/lib/types";

type Mode = "configure" | "postgame";

const QUESTION_STATUSES: InterviewQuestionStatus[] = ["unasked", "satisfactory", "mixed", "unsatisfactory"];
const CUSTOM_THEME_ID = "__custom_group__";
const CUSTOM_THEME_TITLE = "Custom";

export function InterviewWorkspaceEditor({
  applicationId,
  initialWorkspace,
  mode,
}: {
  applicationId: string;
  initialWorkspace: InterviewWorkspaceSummary;
  mode: Mode;
}) {
  const router = useRouter();
  const { authState, clearWorkflowActive, markWorkflowActive, revalidate } = usePortalSession();
  const [workspace, setWorkspace] = useState<InterviewWorkspaceSummary>(() => {
    const draft = readInterviewDraft(applicationId, mode);
    if (!draft) {
      return {
        ...initialWorkspace,
        content: withQuestionFollowUps(initialWorkspace.content),
      };
    }

    return {
      ...initialWorkspace,
      content: withQuestionFollowUps(draft),
    };
  });
  const [saving, setSaving] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [draftRestored, setDraftRestored] = useState(() => Boolean(readInterviewDraft(applicationId, mode)));
  const [activePostgameQuestionId, setActivePostgameQuestionId] = useState<string | null>(() =>
    mode === "postgame" ? getFirstQuestionId(initialWorkspace.content.themes) : null,
  );

  const pageTitle = mode === "configure" ? "Configure Interview" : "Interview Feedback";
  const subtitle =
    mode === "configure"
      ? "Refine generated themes, rewrite questions, and add custom prompts before launching the interview popup."
      : "Review every asked question, adjust ratings, add notes, and publish the final interview report.";
  const canLaunch = workspace.content.themes.some((theme) => theme.questions.length > 0) && workspace.status !== "completed";
  const completionCounts = useMemo(() => {
    const allQuestions = flattenWorkspaceQuestions(workspace);
    return {
      total: allQuestions.length,
      satisfactory: allQuestions.filter((question) => question.status === "satisfactory").length,
      mixed: allQuestions.filter((question) => question.status === "mixed").length,
      unsatisfactory: allQuestions.filter((question) => question.status === "unsatisfactory").length,
    };
  }, [workspace.content.themes]);

  useEffect(() => {
    markWorkflowActive();
    return () => {
      clearWorkflowActive();
    };
  }, [clearWorkflowActive, markWorkflowActive]);

  useEffect(() => {
    writeInterviewDraft(applicationId, mode, workspace.content);
  }, [applicationId, mode, workspace.content]);

  useEffect(() => {
    if (mode !== "postgame") {
      return;
    }

    const allQuestionIds = workspace.content.themes.flatMap((theme) => theme.questions.map((question) => question.id));
    if (allQuestionIds.length === 0) {
      if (activePostgameQuestionId !== null) {
        setActivePostgameQuestionId(null);
      }
      return;
    }

    if (activePostgameQuestionId === null) {
      return;
    }

    if (!allQuestionIds.includes(activePostgameQuestionId)) {
      setActivePostgameQuestionId(allQuestionIds[0]);
    }
  }, [activePostgameQuestionId, mode, workspace.content.themes]);

  function updateTheme(themeId: string, updater: (theme: InterviewWorkspaceTheme) => InterviewWorkspaceTheme) {
    setWorkspace((current) => ({
      ...current,
      content: {
        ...current.content,
        themes: current.content.themes.map((theme) => (theme.id === themeId ? updater(theme) : theme)),
      },
    }));
  }

  function removeTheme(themeId: string) {
    setWorkspace((current) => ({
      ...current,
      content: {
        ...current.content,
        themes: current.content.themes.filter((theme) => theme.id !== themeId),
      },
    }));
  }

  function addTheme() {
    const nextThemeId = `custom-${Date.now()}`;
    setWorkspace((current) => ({
      ...current,
      content: {
        ...current.content,
        themes: [
          ...current.content.themes,
          {
            id: nextThemeId,
            source: "custom",
            title: "",
            unifying_axis: "",
            interview_direction: "",
            question_group_title: "Custom prompts",
            questions: [createQuestion(nextThemeId, 0, "custom")],
          },
        ],
      },
    }));
  }

  function addQuestion(themeId: string, source: "generated" | "custom" = "custom") {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: [...theme.questions, createQuestion(themeId, theme.questions.length, source)],
    }));
  }

  function updateQuestion(themeId: string, questionId: string, updater: (question: InterviewWorkspaceQuestion) => InterviewWorkspaceQuestion) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: theme.questions.map((question) => (question.id === questionId ? updater(question) : question)),
    }));
  }

  function updateFollowUp(
    themeId: string,
    questionId: string,
    followUpId: string,
    updater: (followUp: InterviewWorkspaceQuestionFollowUp) => InterviewWorkspaceQuestionFollowUp,
  ) {
    updateQuestion(themeId, questionId, (question) => ({
      ...question,
      follow_ups: question.follow_ups.map((followUp) => (followUp.id === followUpId ? updater(followUp) : followUp)),
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

  function removeFollowUp(themeId: string, questionId: string, followUpId: string) {
    updateQuestion(themeId, questionId, (question) => ({
      ...question,
      follow_ups: question.follow_ups
        .filter((followUp) => followUp.id !== followUpId)
        .map((followUp, index) => ({ ...followUp, order: index })),
    }));
  }

  function createFollowUp(parentQuestionId: string, order: number): InterviewWorkspaceQuestionFollowUp {
    return {
      id: `${parentQuestionId}-f-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      text: "",
      source: "custom",
      status: "unasked",
      note: "",
      order,
    };
  }

  function addFollowUp(themeId: string, questionId: string) {
    updateQuestion(themeId, questionId, (question) => ({
      ...question,
      follow_ups: [...question.follow_ups, createFollowUp(question.id, question.follow_ups.length)],
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

  function handleAddPostgameCustomQuestion() {
    setWorkspace((current) => {
      const existingCustomTheme = current.content.themes.find((theme) => theme.id === CUSTOM_THEME_ID);
      const customTheme = existingCustomTheme ?? ensureCustomTheme(current);
      const nextQuestion = createQuestion(CUSTOM_THEME_ID, customTheme.questions.length, "custom");
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

  function handleAddPostgameQuestion(themeId: string) {
    if (themeId === CUSTOM_THEME_ID) {
      handleAddPostgameCustomQuestion();
      return;
    }

    addQuestion(themeId, "custom");
  }

  const orderedThemes = useMemo(() => {
    const nonCustomThemes = workspace.content.themes.filter((theme) => theme.id !== CUSTOM_THEME_ID);
    const customTheme =
      workspace.content.themes.find((theme) => theme.id === CUSTOM_THEME_ID) ??
      (mode === "postgame"
        ? {
            id: CUSTOM_THEME_ID,
            source: "custom" as const,
            title: CUSTOM_THEME_TITLE,
            unifying_axis: "",
            interview_direction: "",
            question_group_title: CUSTOM_THEME_TITLE,
            questions: [],
          }
        : undefined);
    return customTheme ? [...nonCustomThemes, customTheme] : nonCustomThemes;
  }, [mode, workspace.content.themes]);

  async function ensureWorkflowSession() {
    if (authState === "authenticated") {
      return true;
    }

    const snapshot = await revalidate({ force: true, reason: `workflow-${mode}-retry` });
    return snapshot.authState === "authenticated";
  }

  function handleAuthFailure(action: string, caughtError: unknown) {
    writeInterviewDraft(applicationId, mode, workspace.content);
    console.warn(`[workflow] auth-related ${action} failure`, {
      applicationId,
      mode,
      state: authState,
      error: caughtError instanceof Error ? caughtError.message : "Unknown auth error",
    });
    setError("Your session expired while this draft was open. The current draft has been preserved locally. Sign back in and retry this action.");
    setMessage(null);
  }

  async function handleSave(successMessage: string) {
    if (!(await ensureWorkflowSession())) {
      setError("We could not re-establish your session yet. Your draft is preserved locally, so you can retry once sign-in is restored.");
      setMessage(null);
      return;
    }

    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const nextWorkspace = await saveInterviewWorkspace(applicationId, workspace.content);
      setWorkspace({
        ...nextWorkspace,
        content: withQuestionFollowUps(nextWorkspace.content),
      });
      clearInterviewDraft(applicationId, mode);
      setDraftRestored(false);
      setMessage(successMessage);
    } catch (saveError) {
      if (isApiErrorStatus(saveError, [401, 403])) {
        handleAuthFailure("workspace save", saveError);
      } else {
        setError(saveError instanceof Error ? saveError.message : "Unable to save interview workspace.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleLaunch() {
    if (!(await ensureWorkflowSession())) {
      setError("We could not re-establish your session yet. Your draft is preserved locally, so you can retry launch after signing in again.");
      setMessage(null);
      return;
    }

    const popup = openInterviewPopupPlaceholder(applicationId);
    setLaunching(true);
    setError(null);
    setMessage(null);
    try {
      const nextWorkspace = await launchInterviewWorkspace(applicationId, workspace.content);
      setWorkspace({
        ...nextWorkspace,
        content: withQuestionFollowUps(nextWorkspace.content),
      });
      clearInterviewDraft(applicationId, mode);
      setDraftRestored(false);
      if (popup) {
        popup.location.href = `/interviewer/applications/${applicationId}/overlay`;
      } else {
        window.location.href = `/interviewer/applications/${applicationId}/overlay`;
        return;
      }
      setMessage("Interview popup opened.");
      router.push(`/interviewer/applications/${applicationId}`);
    } catch (launchError) {
      popup?.close();
      if (isApiErrorStatus(launchError, [401, 403])) {
        handleAuthFailure("workspace launch", launchError);
      } else {
        setError(launchError instanceof Error ? launchError.message : "Unable to launch interview popup.");
      }
    } finally {
      setLaunching(false);
    }
  }

  async function handlePublish() {
    if (!(await ensureWorkflowSession())) {
      setError("We could not re-establish your session yet. Your draft is preserved locally, so you can retry publishing after signing in again.");
      setMessage(null);
      return;
    }

    setPublishing(true);
    setError(null);
    setMessage(null);
    try {
      const normalizedContent = normalizeAuthoredContent(workspace.content);
      const nextWorkspace = await completeInterviewWorkspace(applicationId, normalizedContent);
      setWorkspace({
        ...nextWorkspace,
        content: withQuestionFollowUps(nextWorkspace.content),
      });
      clearInterviewDraft(applicationId, mode);
      setDraftRestored(false);
      setMessage("Final interview report published.");
      router.push(`/interviewer/applications/${applicationId}`);
    } catch (publishError) {
      if (isApiErrorStatus(publishError, [401, 403])) {
        handleAuthFailure("workspace publish", publishError);
      } else {
        setError(publishError instanceof Error ? publishError.message : "Unable to publish final interview report.");
      }
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <Card title={pageTitle} description={subtitle} eyebrow={null}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-wrap gap-3">
              <StatusPill label="Themes" value={String(workspace.content.themes.length)} />
              <StatusPill label="Questions" value={String(completionCounts.total)} />
            </div>

            <div className="flex flex-wrap gap-3">
              <Button disabled={saving} onClick={() => void handleSave(mode === "configure" ? "Interview prep saved." : "Feedback draft saved.")} size="sm" variant="secondary">
                <Save className="size-4" />
                {saving ? "Saving..." : mode === "configure" ? "Save draft" : "Save review"}
              </Button>

              {mode === "configure" ? (
                <Button disabled={!canLaunch || launching} onClick={() => void handleLaunch()} size="sm">
                  <Rocket className="size-4" />
                  {launching ? "Launching..." : "Launch overlay"}
                </Button>
              ) : (
                <Button disabled={publishing} onClick={() => void handlePublish()} size="sm">
                  <CheckCircle2 className="size-4" />
                  {publishing ? "Publishing..." : "Publish final interview report"}
                </Button>
              )}
            </div>
          </div>
        </Card>
      </section>

      {draftRestored ? (
        <p className="rounded-[1.2rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          A locally preserved feedback draft was restored for this application.
        </p>
      ) : null}
      {message ? <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p> : null}
      {error ? <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <section className="space-y-4">
        {orderedThemes.map((theme, themeIndex) => {
          const isCustomTheme = theme.id === CUSTOM_THEME_ID;
          return (
          <article
            key={theme.id}
            className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex flex-wrap gap-2">
                  <span className="inline-flex rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-700">
                    {theme.source}
                  </span>
                  <span className="inline-flex rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.16em] text-blue-700">
                    Theme {themeIndex + 1}
                  </span>
                </div>
                {mode === "configure" ? (
                  <input
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-lg font-semibold text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                    onChange={(event) =>
                      updateTheme(theme.id, (current) => ({ ...current, question_group_title: event.target.value }))
                    }
                    placeholder="Question group title"
                    value={theme.question_group_title}
                  />
                ) : (
                  <h2 className="text-xl font-semibold tracking-tight text-slate-900">
                    {isCustomTheme ? theme.question_group_title || CUSTOM_THEME_TITLE : theme.title || "Untitled theme"}
                  </h2>
                )}
              </div>

              {mode === "configure" || (mode === "postgame" && isCustomTheme) ? (
                <button
                  className="inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-bold uppercase tracking-[0.16em] text-rose-700 transition hover:bg-rose-100"
                  onClick={() => removeTheme(theme.id)}
                  type="button"
                >
                  <Trash2 className="size-3.5" />
                  Remove
                </button>
              ) : null}
            </div>

            {mode !== "configure" ? (
              <>
                {!isCustomTheme ? (
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <ReadOnlyField label="Unifying axis" value={theme.unifying_axis || "No unifying axis recorded."} />
                    <ReadOnlyField label="Interview direction" value={theme.interview_direction || "No interview direction recorded."} />
                  </div>
                ) : null}

                <div className="mt-4">
                  <ReadOnlyField label="Question group" value={theme.question_group_title || "Question group"} />
                </div>
              </>
            ) : null}

            <div className="mt-5 space-y-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Questions</p>

              <div className="space-y-3">
                {theme.questions.length === 0 ? (
                  <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-4 py-3 text-sm text-slate-500">
                    No questions yet. Add one here to capture miscellaneous or follow-up prompts.
                  </p>
                ) : null}
                {theme.questions
                  .slice()
                  .sort((left, right) => left.order - right.order)
                  .map((question, questionIndex) => {
                    const isEditablePostgameQuestion = mode === "postgame" && question.source === "custom";
                    const isExpandedPostgameQuestion = mode === "postgame" && activePostgameQuestionId === question.id;
                    const questionPreview = question.text.trim() || "Untitled question";
                    return (
                      <div key={question.id} className="rounded-[1.2rem] border border-slate-200 bg-slate-50/70 p-4">
                        {mode === "postgame" ? (
                          <>
                            <button
                              className="flex w-full items-start justify-between gap-3 text-left"
                              onClick={() =>
                                setActivePostgameQuestionId((current) => (current === question.id ? null : question.id))
                              }
                              type="button"
                            >
                              <div className="min-w-0 flex-1 space-y-2">
                                <div className="flex flex-wrap items-center gap-2">
                                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                                    Question {questionIndex + 1}
                                  </p>
                                  <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                    {question.source}
                                  </span>
                                </div>
                                <p className="truncate text-sm leading-6 text-slate-900">{questionPreview}</p>
                              </div>

                              <div className="flex shrink-0 items-center gap-2">
                                <span
                                  className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${getQuestionStatusClasses(question.status)}`}
                                >
                                  {getQuestionStatusLabel(question.status)}
                                </span>
                                {question.follow_ups.length ? (
                                  <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                    {question.follow_ups.length} follow-up{question.follow_ups.length === 1 ? "" : "s"}
                                  </span>
                                ) : null}
                                <ChevronDown
                                  className={`size-4 text-slate-500 transition-transform ${
                                    isExpandedPostgameQuestion ? "rotate-180" : ""
                                  }`}
                                />
                              </div>
                            </button>

                            {isExpandedPostgameQuestion ? (
                              <div className="mt-3 space-y-4">
                                <div className="flex flex-wrap items-center gap-3">
                                  <button
                                    className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800"
                                    onClick={() => addFollowUp(theme.id, question.id)}
                                    type="button"
                                  >
                                    <Plus className="size-3.5" />
                                    Follow-up
                                  </button>
                                  {isEditablePostgameQuestion ? (
                                    <button
                                      className="text-xs font-semibold text-rose-700"
                                      onClick={() => removeQuestion(theme.id, question.id)}
                                      type="button"
                                    >
                                      Remove
                                    </button>
                                  ) : null}
                                </div>

                                {isEditablePostgameQuestion ? (
                                  <textarea
                                    className="min-h-24 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                                    onChange={(event) =>
                                      updateQuestion(theme.id, question.id, (current) => ({ ...current, text: event.target.value }))
                                    }
                                    placeholder="Type question"
                                    value={question.text}
                                  />
                                ) : (
                                  <p className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900">
                                    {questionPreview}
                                  </p>
                                )}
                                <QuestionStatusSelector
                                  status={question.status}
                                  onChange={(status) =>
                                    updateQuestion(theme.id, question.id, (current) => ({ ...current, status }))
                                  }
                                />
                                <TextAreaField
                                  label="Question note"
                                  onChange={(value) =>
                                    updateQuestion(theme.id, question.id, (current) => ({ ...current, note: value }))
                                  }
                                  rows={4}
                                  value={question.note}
                                />
                                <RefinementControls
                                  applicationId={applicationId}
                                  content={workspace.content}
                                  currentValue={question.note}
                                  mode="question_note"
                                  onAccept={(value) =>
                                    updateQuestion(theme.id, question.id, (current) => ({ ...current, note: value }))
                                  }
                                  questionId={question.id}
                                  themeId={theme.id}
                                />

                                {question.follow_ups.length ? (
                                  <div className="space-y-3 rounded-[1rem] border border-slate-200 bg-white/70 p-3">
                                    <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Follow-ups</p>
                                    {question.follow_ups
                                      .slice()
                                      .sort((left, right) => left.order - right.order)
                                      .map((followUp, followUpIndex) => (
                                        <div key={followUp.id} className="rounded-[0.95rem] border border-slate-200 bg-white p-3">
                                          <div className="flex items-start justify-between gap-3">
                                            <div className="space-y-1">
                                              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                                                Follow-up {followUpIndex + 1}
                                              </p>
                                              <span className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                                {followUp.source}
                                              </span>
                                            </div>
                                            <button
                                              className="text-xs font-semibold text-rose-700"
                                              onClick={() => removeFollowUp(theme.id, question.id, followUp.id)}
                                              type="button"
                                            >
                                              Remove
                                            </button>
                                          </div>
                                          <div className="mt-3 space-y-4">
                                            <textarea
                                              className="min-h-24 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                                              onChange={(event) =>
                                                updateFollowUp(theme.id, question.id, followUp.id, (current) => ({
                                                  ...current,
                                                  text: event.target.value,
                                                }))
                                              }
                                              placeholder="Type follow-up"
                                              value={followUp.text}
                                            />
                                            <QuestionStatusSelector
                                              status={followUp.status}
                                              onChange={(status) =>
                                                updateFollowUp(theme.id, question.id, followUp.id, (current) => ({
                                                  ...current,
                                                  status,
                                                }))
                                              }
                                            />
                                            <TextAreaField
                                              label="Follow-up note"
                                              onChange={(value) =>
                                                updateFollowUp(theme.id, question.id, followUp.id, (current) => ({
                                                  ...current,
                                                  note: value,
                                                }))
                                              }
                                              rows={4}
                                              value={followUp.note}
                                            />
                                            <RefinementControls
                                              applicationId={applicationId}
                                              content={workspace.content}
                                              currentValue={followUp.note}
                                              followUpId={followUp.id}
                                              mode="follow_up_note"
                                              onAccept={(value) =>
                                                updateFollowUp(theme.id, question.id, followUp.id, (current) => ({
                                                  ...current,
                                                  note: value,
                                                }))
                                              }
                                              questionId={question.id}
                                              themeId={theme.id}
                                            />
                                          </div>
                                        </div>
                                      ))}
                                  </div>
                                ) : null}
                              </div>
                            ) : null}
                          </>
                        ) : mode === "configure" ? (
                          <>
                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-1">
                                <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">
                                  Question {questionIndex + 1}
                                </p>
                                <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                                  {question.source}
                                </span>
                              </div>
                              {theme.questions.length > 1 ? (
                                <button
                                  className="text-xs font-semibold text-rose-700"
                                  onClick={() => removeQuestion(theme.id, question.id)}
                                  type="button"
                                >
                                  Remove
                                </button>
                              ) : null}
                            </div>
                            <textarea
                              className="mt-3 min-h-24 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                              onChange={(event) =>
                                updateQuestion(theme.id, question.id, (current) => ({ ...current, text: event.target.value }))
                              }
                              value={question.text}
                            />
                          </>
                        ) : null}
                      </div>
                    );
                  })}

                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white px-3 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                  onClick={() => (mode === "configure" ? addQuestion(theme.id) : handleAddPostgameQuestion(theme.id))}
                  type="button"
                >
                  <Plus className="size-4" />
                  Add question
                </button>
              </div>
            </div>
          </article>
        )})}

        {mode === "configure" ? (
          <button
            className="flex w-full items-center justify-center gap-2 rounded-[1.4rem] border border-dashed border-slate-300 bg-white/70 px-4 py-4 text-sm font-semibold text-slate-700 transition hover:bg-white"
            onClick={addTheme}
            type="button"
          >
            <Plus className="size-4" />
            Add custom theme
          </button>
        ) : null}
      </section>

      {mode === "postgame" ? (
        <Card title="Final summary" description="Optional top-line wrap-up for the final interview report." eyebrow={null}>
          <div className="space-y-4">
            <TextAreaField
              label="Final summary"
              onChange={(value) =>
                setWorkspace((current) => ({
                  ...current,
                  content: { ...current.content, final_summary: value },
                }))
              }
              rows={6}
              value={workspace.content.final_summary}
            />
            <RefinementControls
              applicationId={applicationId}
              content={workspace.content}
              currentValue={workspace.content.final_summary}
              mode="final_summary"
              onAccept={(value) =>
                setWorkspace((current) => ({
                  ...current,
                  content: { ...current.content, final_summary: value },
                }))
              }
            />
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function createQuestion(themeId: string, order: number, source: "generated" | "custom"): InterviewWorkspaceQuestion {
  return {
    id: `${themeId}-q-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    text: "",
    source,
    status: "unasked",
    note: "",
    order,
    follow_ups: [],
  };
}

function StatusPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-full border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <span className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-500">{label}: </span>
      <span className="text-sm font-semibold text-slate-900">{value}</span>
    </div>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  rows,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows: number;
}) {
  return (
    <label className="block text-sm text-slate-600">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</span>
      <textarea
        className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
        value={value}
      />
    </label>
  );
}

function RefinementControls({
  applicationId,
  content,
  currentValue,
  mode,
  onAccept,
  themeId,
  questionId,
  followUpId,
}: {
  applicationId: string;
  content: InterviewWorkspaceSummary["content"];
  currentValue: string;
  mode: InterviewRefinementMode;
  onAccept: (value: string) => void;
  themeId?: string;
  questionId?: string;
  followUpId?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [instructionOpen, setInstructionOpen] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [preview, setPreview] = useState<string | null>(null);

  async function handleRefine() {
    if (!currentValue.trim()) {
      setError("Add some text before running refinement.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await refineInterviewWorkspaceText(applicationId, {
        mode,
        text: currentValue,
        instruction,
        content,
        theme_id: themeId,
        question_id: questionId,
        follow_up_id: followUpId,
      });
      setPreview(response.refined_text);
    } catch (refineError) {
      setError(refineError instanceof Error ? refineError.message : "Unable to refine this text right now.");
    } finally {
      setLoading(false);
    }
  }

  function resetPreview() {
    setPreview(null);
    setError(null);
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <button
          className="inline-flex items-center gap-1 text-xs font-semibold text-blue-700 transition hover:text-blue-800 disabled:text-slate-400"
          disabled={loading}
          onClick={() => void handleRefine()}
          type="button"
        >
          <Sparkles className="size-3.5" />
          {loading ? "Refining..." : "Refine"}
        </button>
        <button
          className="text-xs font-medium text-slate-500 transition hover:text-slate-700"
          onClick={() => setInstructionOpen((current) => !current)}
          type="button"
        >
          {instructionOpen ? "Hide instruction" : "Add instruction"}
        </button>
      </div>

      {instructionOpen ? (
        <label className="block text-sm text-slate-600">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Instruction</span>
          <textarea
            className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
            onChange={(event) => setInstruction(event.target.value)}
            placeholder="Optional: make this sharper, turn into bullets, emphasize constraints..."
            rows={2}
            value={instruction}
          />
        </label>
      ) : null}

      {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p> : null}

      {preview ? (
        <div className="space-y-3 rounded-[1rem] border border-blue-200 bg-blue-50/70 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-blue-800">Preview</p>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => {
                  onAccept(preview);
                  resetPreview();
                }}
                size="sm"
              >
                Accept
              </Button>
              <Button onClick={resetPreview} size="sm" variant="secondary">
                Cancel
              </Button>
            </div>
          </div>
          <div className="rounded-xl border border-blue-100 bg-white/80 px-4 py-3 text-sm leading-7 text-slate-900 whitespace-pre-wrap">
            {preview}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-3">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm leading-7 text-slate-800">{value}</p>
    </div>
  );
}

function QuestionStatusSelector({
  status,
  onChange,
}: {
  status: InterviewQuestionStatus;
  onChange: (status: InterviewQuestionStatus) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {QUESTION_STATUSES.map((candidate) => {
        const selected = status === candidate;
        return (
          <button
            key={candidate}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-bold uppercase tracking-[0.16em] transition ${
              selected ? getQuestionStatusClasses(candidate) : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
            onClick={() => onChange(candidate)}
            type="button"
          >
            {getQuestionStatusIcon(candidate)}
            {getQuestionStatusLabel(candidate)}
          </button>
        );
      })}
    </div>
  );
}

function getQuestionStatusClasses(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return "border-emerald-200 bg-emerald-100 text-emerald-900";
  if (status === "mixed") return "border-amber-200 bg-amber-100 text-amber-900";
  if (status === "unsatisfactory") return "border-rose-200 bg-rose-100 text-rose-900";
  return "border-slate-300 bg-slate-100 text-slate-700";
}

function getQuestionStatusLabel(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return "Satisfied";
  if (status === "mixed") return "Mixed";
  if (status === "unsatisfactory") return "Unsatisfied";
  return "Unasked";
}

function getQuestionStatusIcon(status: InterviewQuestionStatus) {
  if (status === "satisfactory") return <CheckCircle2 className="size-3.5" />;
  if (status === "mixed") return <MinusCircle className="size-3.5" />;
  if (status === "unsatisfactory") return <XCircle className="size-3.5" />;
  return <span className="inline-block size-3 rounded-full border border-current" />;
}

function normalizeAuthoredContent(content: InterviewWorkspaceSummary["content"]) {
  return {
    ...content,
    themes: content.themes
      .map((theme) => ({
        ...theme,
        questions: theme.questions
          .filter((question) => question.source !== "custom" || question.text.trim().length > 0)
          .map((question, index) => ({
            ...question,
            order: index,
            follow_ups: question.follow_ups
              .filter((followUp) => followUp.text.trim().length > 0)
              .map((followUp, followUpIndex) => ({ ...followUp, order: followUpIndex })),
          })),
      }))
      .filter((theme) => theme.id !== CUSTOM_THEME_ID || theme.questions.length > 0),
  };
}

function flattenWorkspaceQuestions(workspace: InterviewWorkspaceSummary) {
  return workspace.content.themes.flatMap((theme) =>
    theme.questions.flatMap((question) => [question, ...question.follow_ups]),
  );
}

function getFirstQuestionId(themes: InterviewWorkspaceTheme[]) {
  for (const theme of themes) {
    if (theme.questions.length > 0) {
      return theme.questions[0].id;
    }
  }

  return null;
}

function withQuestionFollowUps(content: InterviewWorkspaceSummary["content"]) {
  return {
    ...content,
    themes: content.themes.map((theme) => ({
      ...theme,
      questions: theme.questions.map((question) => ({
        ...question,
        follow_ups: question.follow_ups ?? [],
      })),
    })),
  };
}
