"use client";

import { Star } from "lucide-react";
import { useState } from "react";
import type {
  PrebuildFeedbackState,
  PrebuildQuestionThreadSummary,
  PrebuildQuestionVersionSummary,
} from "@/lib/types";
import { Card } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

type FocusAreaRecord = {
  focus_area_id?: string;
  title?: string;
  territory?: string;
  what_makes_it_worth_time?: string;
  source_theme_ids?: string[];
  source_signal_ids?: string[];
};

type QuestionRecord = {
  question_id?: string;
  question?: string;
  question_role?: string;
  framing_note?: string;
};

type QuestionGroupRecord = {
  focus_area_id?: string;
  group_label?: string;
  line_of_inquiry?: string;
  questions?: QuestionRecord[];
  source_theme_ids?: string[];
  source_signal_ids?: string[];
};

type ReportLike = Record<string, unknown> & {
  page_4_focus_areas?: {
    focus_areas?: FocusAreaRecord[];
  };
  page_5_question_groups?: {
    question_groups?: QuestionGroupRecord[];
  };
  signal_data?: {
    annotations?: Record<string, unknown>;
  };
};

type ReportTab = "page4" | "page5";

export function SynthesisReportSection({
  report,
  title = "Interview Brief",
  description,
  initialTab = "page4",
  hideInternalTabs = false,
  prebuildFeedback,
  onRateTheme,
  onRateQuestionVersion,
  onRegenerateQuestion,
  onActivateQuestionVersion,
}: {
  report: Record<string, unknown>;
  title?: string;
  description?: string;
  initialTab?: ReportTab;
  hideInternalTabs?: boolean;
  prebuildFeedback?: PrebuildFeedbackState | null;
  onRateTheme?: ((focusAreaId: string, rating: number) => Promise<void>) | null;
  onRateQuestionVersion?: ((threadId: string, versionId: string, rating: number) => Promise<void>) | null;
  onRegenerateQuestion?: ((threadId: string) => Promise<void>) | null;
  onActivateQuestionVersion?: ((threadId: string, versionId: string) => Promise<void>) | null;
}) {
  const parsed = report as ReportLike;
  const [activeTab, setActiveTab] = useState<ReportTab>(initialTab);
  const focusAreas = Array.isArray(parsed.page_4_focus_areas?.focus_areas) ? parsed.page_4_focus_areas?.focus_areas || [] : [];
  const groups = Array.isArray(parsed.page_5_question_groups?.question_groups) ? parsed.page_5_question_groups?.question_groups || [] : [];
  const [selectedFocusAreaKey, setSelectedFocusAreaKey] = useState<string>(() => getFocusAreaKey(focusAreas[0], 0));
  const [openQuestionNotes, setOpenQuestionNotes] = useState<Record<string, string | null>>({});
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const annotationCount = countAnnotations(parsed.signal_data?.annotations);
  const themeFeedbackById = new Map((prebuildFeedback?.theme_feedback || []).map((item) => [item.focus_area_id, item]));
  const threadByQuestionId = new Map((prebuildFeedback?.question_threads || []).map((item) => [item.base_question_id, item]));
  const showThemeControls = Boolean(prebuildFeedback && !prebuildFeedback.prebuild_generation_locked && prebuildFeedback.can_rate_themes && onRateTheme);
  const showQuestionControls = Boolean(
    prebuildFeedback &&
      !prebuildFeedback.prebuild_generation_locked &&
      prebuildFeedback.can_manage_questions &&
      onRateQuestionVersion &&
      onRegenerateQuestion &&
      onActivateQuestionVersion,
  );

  const activeFocusArea =
    focusAreas.find((focusArea, index) => getFocusAreaKey(focusArea, index) === selectedFocusAreaKey) ||
    focusAreas[0] ||
    null;

  const rootAnchorId = initialTab === "page5" ? "report-page5-question-groups" : "report-page4-focus-areas";

  return (
    <div id={rootAnchorId} className="space-y-5">
      {!hideInternalTabs ? (
        <Card title={title} description={description || "Structured presentation of the interview brief."}>
          <div className="metric-strip">
            <MetricPill label="Focus Areas" value={focusAreas.length} />
            <MetricPill label="Question Sets" value={groups.length} />
            <MetricPill label="Annotations" value={annotationCount} />
          </div>
        </Card>
      ) : null}

      <Card
        title={activeTab === "page4" ? "Focus Areas" : "Question Sets"}
        description={
          activeTab === "page4"
            ? "Rich interviewer-facing notes generated from the grounded backend structure."
            : "Grouped interview questions generated from the focus areas."
        }
        eyebrow={null}
      >
        <div className="space-y-5">
          {!hideInternalTabs ? (
            <SegmentedControl
              label="Synthesis pages"
              value={activeTab}
              onChange={setActiveTab}
              options={[
                { value: "page4", label: "Page 4", meta: "Focus areas" },
                { value: "page5", label: "Page 5", meta: "Question sets" },
              ]}
            />
          ) : null}

          {activeTab === "page4" ? (
            <div className="grid gap-5 xl:grid-cols-[19rem_minmax(0,1fr)]">
              <section className="space-y-4">
                <div className="space-y-2 xl:hidden">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Focus Areas</p>
                  <label className="sr-only" htmlFor="focus-area-select">
                    Select focus area
                  </label>
                  <select
                    id="focus-area-select"
                    className="w-full rounded-[1rem] border border-slate-200 bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)] shadow-[0_10px_22px_rgba(15,23,42,0.05)]"
                    value={selectedFocusAreaKey}
                    onChange={(event) => setSelectedFocusAreaKey(event.target.value)}
                  >
                    {focusAreas.map((focusArea, index) => (
                      <option key={getFocusAreaKey(focusArea, index)} value={getFocusAreaKey(focusArea, index)}>
                        {getFocusAreaLabel(focusArea, index)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="hidden space-y-3 xl:block">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Focus Areas</p>
                  {focusAreas.length ? (
                    focusAreas.map((focusArea, index) => {
                      const focusAreaKey = getFocusAreaKey(focusArea, index);
                      const active = activeFocusArea ? getFocusAreaKey(activeFocusArea, focusAreas.indexOf(activeFocusArea)) === focusAreaKey : false;
                      return (
                        <button
                          key={focusAreaKey}
                          type="button"
                          onClick={() => setSelectedFocusAreaKey(focusAreaKey)}
                          className={`block w-full rounded-[1.3rem] border p-4 text-left transition ${
                            active
                              ? "border-blue-200 bg-[linear-gradient(145deg,rgba(239,246,255,0.98),rgba(255,255,255,0.94))] shadow-[0_18px_34px_rgba(15,23,42,0.08)]"
                              : "border-slate-200 bg-white/80 shadow-[0_16px_30px_rgba(15,23,42,0.06)] hover:bg-white/92"
                          }`}
                        >
                          <p className="text-sm font-semibold leading-6 text-[color:var(--ink)]">{getFocusAreaLabel(focusArea, index)}</p>
                        </button>
                      );
                    })
                  ) : (
                    <EmptyDetail text="No synthesized focus areas yet." />
                  )}
                </div>
              </section>

              <section className="space-y-4">
                {activeFocusArea ? (
                  <article className="rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.96),rgba(239,246,255,0.88),rgba(255,255,255,0.9))] p-5 shadow-[0_18px_34px_rgba(15,23,42,0.08)]">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Interview Dossier</p>
                        <h3 className="text-2xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">
                          {activeFocusArea.title || "Untitled focus area"}
                        </h3>
                        {showThemeControls && activeFocusArea.focus_area_id ? (
                          <InlineStarRating
                            busy={busyKey === `theme:${activeFocusArea.focus_area_id}`}
                            currentRating={themeFeedbackById.get(String(activeFocusArea.focus_area_id))?.my_rating ?? null}
                            label="Rate this focus area"
                            onRate={async (rating) => {
                              if (!onRateTheme) return;
                              const localKey = `theme:${activeFocusArea.focus_area_id}`;
                              setBusyKey(localKey);
                              try {
                                await onRateTheme(String(activeFocusArea.focus_area_id), rating);
                              } finally {
                                setBusyKey((current) => (current === localKey ? null : current));
                              }
                            }}
                          />
                        ) : null}
                      </div>
                      <FocusBlock label="Territory" value={activeFocusArea.territory} />
                      <FocusBlock label="Why this is worth time" value={activeFocusArea.what_makes_it_worth_time} />
                    </div>
                  </article>
                ) : (
                  <EmptyDetail text="No synthesized focus areas yet." />
                )}
              </section>
            </div>
          ) : (
            <div className="space-y-4">
              {groups.length ? (
                groups.map((group, index) => {
                  const matchedFocusArea = focusAreas.find((item) => item.focus_area_id === group.focus_area_id);
                  const groupKey = group.focus_area_id || group.group_label || `group-${index}`;
                  return (
                    <article
                      key={groupKey}
                      className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                    >
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">
                            {matchedFocusArea?.title || `Focus Area ${index + 1}`}
                          </p>
                          <h3 className="text-xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">
                            {group.group_label || "Question set"}
                          </h3>
                          {group.line_of_inquiry ? (
                            <p className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-7 text-[color:var(--ink)]">
                              <span className="font-semibold">Line of inquiry:</span> {group.line_of_inquiry}
                            </p>
                          ) : null}
                        </div>
                        <div className="space-y-3">
                          {(group.questions || []).map((question, questionIndex) => {
                            const questionKey = question.question_id || `${groupKey}-${questionIndex}`;
                            const thread = question.question_id ? threadByQuestionId.get(question.question_id) : undefined;
                            const activeVersion = getActiveQuestionVersion(thread);
                            const renderedQuestion = activeVersion?.question_text || question.question || "Untitled question";
                            const framingNote = (activeVersion?.why_this || question.framing_note || "").trim();
                            const isOpen = openQuestionNotes[groupKey] === questionKey;
                            const visibleIndex = activeVersion ? getVisibleVersionIndex(thread, activeVersion.id) : -1;
                            const previousVersion = activeVersion ? getAdjacentVersion(thread, activeVersion.id, -1) : null;
                            const nextVersion = activeVersion ? getAdjacentVersion(thread, activeVersion.id, 1) : null;

                            return (
                              <div
                                key={questionKey}
                                className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-7 text-[color:var(--ink)]"
                              >
                                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
                                  Question {questionIndex + 1}
                                </p>
                                <div className="mt-1 flex items-start justify-between gap-3">
                                  <p className="min-w-0 flex-1 font-semibold text-[color:var(--ink)]">
                                    {renderedQuestion}
                                  </p>
                                  {framingNote ? (
                                    <button
                                      type="button"
                                      onClick={() =>
                                        setOpenQuestionNotes((current) => ({
                                          ...current,
                                          [groupKey]: current[groupKey] === questionKey ? null : questionKey,
                                        }))
                                      }
                                      aria-expanded={isOpen}
                                      className="shrink-0 rounded-full border border-slate-200 bg-white/90 px-2.5 py-1 text-[11px] font-semibold tracking-[0.06em] text-[color:var(--muted)] transition hover:bg-white"
                                    >
                                      Why this? {isOpen ? "v" : ">"}
                                    </button>
                                  ) : null}
                                </div>
                                {showQuestionControls && thread && activeVersion ? (
                                  <div className="mt-3 space-y-2 border-t border-slate-200/80 pt-3">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <InlineStarRating
                                        busy={busyKey === `question-rate:${thread.thread_id}:${activeVersion.id}`}
                                        currentRating={activeVersion.my_rating ?? null}
                                        label="Rate this generated question"
                                        onRate={async (rating) => {
                                          if (!onRateQuestionVersion) return;
                                          const localKey = `question-rate:${thread.thread_id}:${activeVersion.id}`;
                                          setBusyKey(localKey);
                                          try {
                                            await onRateQuestionVersion(thread.thread_id, activeVersion.id, rating);
                                          } finally {
                                            setBusyKey((current) => (current === localKey ? null : current));
                                          }
                                        }}
                                      />
                                      <span className="rounded-full border border-slate-200 bg-white/90 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-600">
                                        Version {visibleIndex + 1} / {thread.recent_versions.length}
                                      </span>
                                    </div>
                                    <div className="flex flex-wrap items-center gap-2">
                                      <button
                                        type="button"
                                        className="rounded-full border border-slate-200 bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                                        disabled={!previousVersion || busyKey !== null}
                                        onClick={() => void handleActivateVersion(previousVersion, thread, onActivateQuestionVersion, setBusyKey)}
                                      >
                                        Previous
                                      </button>
                                      <button
                                        type="button"
                                        className="rounded-full border border-slate-200 bg-white/90 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-50"
                                        disabled={!nextVersion || busyKey !== null}
                                        onClick={() => void handleActivateVersion(nextVersion, thread, onActivateQuestionVersion, setBusyKey)}
                                      >
                                        Next
                                      </button>
                                      <button
                                        type="button"
                                        className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 transition hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
                                        disabled={busyKey !== null}
                                        onClick={async () => {
                                          if (!onRegenerateQuestion) return;
                                          const localKey = `question-regen:${thread.thread_id}`;
                                          setBusyKey(localKey);
                                          try {
                                            await onRegenerateQuestion(thread.thread_id);
                                          } finally {
                                            setBusyKey((current) => (current === localKey ? null : current));
                                          }
                                        }}
                                      >
                                        Regenerate
                                      </button>
                                    </div>
                                  </div>
                                ) : null}
                                {framingNote && isOpen ? (
                                  <p className="mt-2 border-t border-slate-200/80 pt-2 text-[12px] leading-6 text-slate-500">
                                    {framingNote}
                                  </p>
                                ) : null}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </article>
                  );
                })
              ) : (
                <EmptyDetail text="No question sets have been generated yet." />
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-full border border-slate-200 bg-white/85 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--muted)]">
      <span className="mr-2 text-[color:var(--ink)]">{value}</span>
      {label}
    </div>
  );
}

function FocusBlock({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="rounded-[1rem] bg-[color:var(--accent-soft)] px-4 py-3 text-sm leading-7 text-[color:var(--ink)]">
      <span className="font-semibold">{label}:</span> {value}
    </div>
  );
}

function EmptyDetail({ text }: { text: string }) {
  return <p className="rounded-[1rem] border border-dashed border-slate-200 bg-slate-50/70 px-4 py-4 text-sm text-[color:var(--muted)]">{text}</p>;
}

function InlineStarRating({
  currentRating,
  onRate,
  label,
  busy,
}: {
  currentRating: number | null;
  onRate: (rating: number) => Promise<void>;
  label: string;
  busy: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5" aria-label={label}>
      {Array.from({ length: 5 }, (_, index) => {
        const value = index + 1;
        const active = (currentRating || 0) >= value;
        return (
          <button
            key={value}
            type="button"
            className={`rounded-full border px-2 py-1 text-xs font-semibold transition ${
              active
                ? "border-amber-200 bg-amber-50 text-amber-700"
                : "border-slate-200 bg-white/80 text-slate-500 hover:bg-white"
            }`}
            disabled={busy}
            onClick={() => void onRate(value)}
          >
            <Star className={`size-3.5 ${active ? "fill-current" : ""}`} strokeWidth={1.8} />
          </button>
        );
      })}
    </div>
  );
}

async function handleActivateVersion(
  version: PrebuildQuestionVersionSummary | null,
  thread: PrebuildQuestionThreadSummary,
  onActivateQuestionVersion: ((threadId: string, versionId: string) => Promise<void>) | null | undefined,
  setBusyKey: (value: string | null | ((current: string | null) => string | null)) => void,
) {
  if (!version || !onActivateQuestionVersion) return;
  const localKey = `question-activate:${thread.thread_id}:${version.id}`;
  setBusyKey(localKey);
  try {
    await onActivateQuestionVersion(thread.thread_id, version.id);
  } finally {
    setBusyKey((current) => (current === localKey ? null : current));
  }
}

function countAnnotations(annotations: Record<string, unknown> | undefined) {
  if (!annotations || typeof annotations !== "object") return 0;
  return Object.values(annotations).reduce<number>((sum, value) => {
    if (Array.isArray(value)) return sum + value.length;
    if (value && typeof value === "object") return sum + Object.keys(value).length;
    return sum;
  }, 0);
}

function getFocusAreaKey(focusArea: FocusAreaRecord | undefined, index: number) {
  return focusArea?.focus_area_id || `focus-area-${index}`;
}

function getFocusAreaLabel(focusArea: FocusAreaRecord | undefined, index: number) {
  return focusArea?.title || `Focus Area ${index + 1}`;
}

function getActiveQuestionVersion(thread: PrebuildQuestionThreadSummary | undefined) {
  if (!thread) return null;
  return thread.recent_versions.find((item) => item.id === thread.active_version_id) || thread.recent_versions[thread.recent_versions.length - 1] || null;
}

function getVisibleVersionIndex(thread: PrebuildQuestionThreadSummary | undefined, versionId: string) {
  if (!thread) return -1;
  return thread.recent_versions.findIndex((item) => item.id === versionId);
}

function getAdjacentVersion(
  thread: PrebuildQuestionThreadSummary | undefined,
  versionId: string,
  direction: -1 | 1,
) {
  if (!thread) return null;
  const currentIndex = thread.recent_versions.findIndex((item) => item.id === versionId);
  if (currentIndex < 0) return null;
  return thread.recent_versions[currentIndex + direction] || null;
}
