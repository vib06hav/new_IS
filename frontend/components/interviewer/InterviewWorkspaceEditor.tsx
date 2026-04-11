"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, MinusCircle, Plus, Rocket, Save, Trash2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  completeInterviewWorkspace,
  launchInterviewWorkspace,
  saveInterviewWorkspace,
} from "@/lib/api";
import { openInterviewPopupPlaceholder } from "@/lib/interviewPopup";
import type {
  InterviewQuestionStatus,
  InterviewWorkspaceQuestion,
  InterviewWorkspaceSummary,
  InterviewWorkspaceTheme,
} from "@/lib/types";

type Mode = "configure" | "postgame";

const QUESTION_STATUSES: InterviewQuestionStatus[] = ["unasked", "satisfactory", "mixed", "unsatisfactory"];

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
  const [workspace, setWorkspace] = useState<InterviewWorkspaceSummary>(initialWorkspace);
  const [saving, setSaving] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const pageTitle = mode === "configure" ? "Configure Interview" : "Postgame Review";
  const subtitle =
    mode === "configure"
      ? "Refine generated themes, rewrite questions, and add custom prompts before launching the interview popup."
      : "Review every asked question, adjust ratings, add notes, and publish the final interview report.";
  const canLaunch = workspace.content.themes.some((theme) => theme.questions.length > 0) && workspace.status !== "completed";
  const completionCounts = useMemo(() => {
    const allQuestions = workspace.content.themes.flatMap((theme) => theme.questions);
    return {
      total: allQuestions.length,
      satisfactory: allQuestions.filter((question) => question.status === "satisfactory").length,
      mixed: allQuestions.filter((question) => question.status === "mixed").length,
      unsatisfactory: allQuestions.filter((question) => question.status === "unsatisfactory").length,
    };
  }, [workspace.content.themes]);

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

  function removeQuestion(themeId: string, questionId: string) {
    updateTheme(themeId, (theme) => ({
      ...theme,
      questions: theme.questions
        .filter((question) => question.id !== questionId)
        .map((question, index) => ({ ...question, order: index })),
    }));
  }

  async function handleSave(successMessage: string) {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const nextWorkspace = await saveInterviewWorkspace(applicationId, workspace.content);
      setWorkspace(nextWorkspace);
      setMessage(successMessage);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to save interview workspace.");
    } finally {
      setSaving(false);
    }
  }

  async function handleLaunch() {
    const popup = openInterviewPopupPlaceholder(applicationId);
    setLaunching(true);
    setError(null);
    setMessage(null);
    try {
      const nextWorkspace = await launchInterviewWorkspace(applicationId, workspace.content);
      setWorkspace(nextWorkspace);
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
      setError(launchError instanceof Error ? launchError.message : "Unable to launch interview popup.");
    } finally {
      setLaunching(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setError(null);
    setMessage(null);
    try {
      const nextWorkspace = await completeInterviewWorkspace(applicationId, workspace.content);
      setWorkspace(nextWorkspace);
      setMessage("Final interview report published.");
      router.push(`/interviewer/applications/${applicationId}`);
    } catch (publishError) {
      setError(publishError instanceof Error ? publishError.message : "Unable to publish final interview report.");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <Card title={pageTitle} description={subtitle} eyebrow={null}>
          <div className="flex flex-wrap gap-3">
            <StatusPill label="Stage" value={workspace.status.toUpperCase()} />
            <StatusPill label="Themes" value={String(workspace.content.themes.length)} />
            <StatusPill label="Questions" value={String(completionCounts.total)} />
            {mode === "postgame" ? <StatusPill label="Satisfied" value={String(completionCounts.satisfactory)} /> : null}
          </div>
        </Card>

        <Card
          title={mode === "configure" ? "Launch" : "Publish"}
          description={
            mode === "configure"
              ? "Save your prep and open the compact interview runner in a popup window."
              : "Ratings and notes are draftable until you publish the final interview report."
          }
          eyebrow={null}
        >
          <div className="space-y-3">
            <Button disabled={saving} onClick={() => void handleSave(mode === "configure" ? "Interview prep saved." : "Postgame draft saved.")} size="sm" variant="secondary">
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
        </Card>
      </section>

      {message ? <p className="rounded-[1.2rem] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">{message}</p> : null}
      {error ? <p className="rounded-[1.2rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

      <section className="space-y-4">
        {workspace.content.themes.map((theme, themeIndex) => (
          <article
            key={theme.id}
            className="rounded-[1.6rem] border border-slate-200 bg-white/80 p-5 shadow-[0_18px_36px_rgba(15,23,42,0.08)] backdrop-blur-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
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
                    onChange={(event) => updateTheme(theme.id, (current) => ({ ...current, title: event.target.value }))}
                    placeholder="Theme title"
                    value={theme.title}
                  />
                ) : (
                  <h2 className="text-xl font-semibold tracking-tight text-slate-900">{theme.title || "Untitled theme"}</h2>
                )}
              </div>

              {mode === "configure" ? (
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

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {mode === "configure" ? (
                <>
                  <TextAreaField
                    label="Unifying axis"
                    onChange={(value) => updateTheme(theme.id, (current) => ({ ...current, unifying_axis: value }))}
                    rows={4}
                    value={theme.unifying_axis}
                  />
                  <TextAreaField
                    label="Interview direction"
                    onChange={(value) => updateTheme(theme.id, (current) => ({ ...current, interview_direction: value }))}
                    rows={4}
                    value={theme.interview_direction}
                  />
                </>
              ) : (
                <>
                  <ReadOnlyField label="Unifying axis" value={theme.unifying_axis || "No unifying axis recorded."} />
                  <ReadOnlyField label="Interview direction" value={theme.interview_direction || "No interview direction recorded."} />
                </>
              )}
            </div>

            <div className="mt-4">
              {mode === "configure" ? (
                <label className="block text-sm text-slate-600">
                  <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Question group title</span>
                  <input
                    className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                    onChange={(event) =>
                      updateTheme(theme.id, (current) => ({ ...current, question_group_title: event.target.value }))
                    }
                    value={theme.question_group_title}
                  />
                </label>
              ) : (
                <ReadOnlyField label="Question group" value={theme.question_group_title || "Question group"} />
              )}
            </div>

            <div className="mt-5 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-slate-500">Questions</p>
                {mode === "configure" ? (
                  <button
                    className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-bold uppercase tracking-[0.16em] text-slate-700 transition hover:bg-slate-50"
                    onClick={() => addQuestion(theme.id)}
                    type="button"
                  >
                    <Plus className="size-3.5" />
                    Add question
                  </button>
                ) : null}
              </div>

              <div className="space-y-3">
                {theme.questions
                  .slice()
                  .sort((left, right) => left.order - right.order)
                  .map((question, questionIndex) => (
                    <div key={question.id} className="rounded-[1.2rem] border border-slate-200 bg-slate-50/70 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-500">Question {questionIndex + 1}</p>
                          <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-600">
                            {question.source}
                          </span>
                        </div>
                        {mode === "configure" && theme.questions.length > 1 ? (
                          <button
                            className="text-xs font-semibold text-rose-700"
                            onClick={() => removeQuestion(theme.id, question.id)}
                            type="button"
                          >
                            Remove
                          </button>
                        ) : null}
                      </div>

                      {mode === "configure" ? (
                        <textarea
                          className="mt-3 min-h-24 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-200"
                          onChange={(event) =>
                            updateQuestion(theme.id, question.id, (current) => ({ ...current, text: event.target.value }))
                          }
                          value={question.text}
                        />
                      ) : (
                        <div className="mt-3 space-y-4">
                          <p className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-900">
                            {question.text || "Untitled question"}
                          </p>
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
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          </article>
        ))}

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
        </Card>
      ) : null}
    </div>
  );
}

function createQuestion(themeId: string, order: number, source: "generated" | "custom"): InterviewWorkspaceQuestion {
  return {
    id: `${themeId}-q-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    text: source === "custom" ? "New custom question" : "",
    source,
    status: "unasked",
    note: "",
    order,
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
