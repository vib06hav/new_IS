"use client";

import { useState } from "react";
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
  title = "Final Report",
  description,
  initialTab = "page4",
  hideInternalTabs = false,
}: {
  report: Record<string, unknown>;
  title?: string;
  description?: string;
  initialTab?: ReportTab;
  hideInternalTabs?: boolean;
}) {
  const parsed = report as ReportLike;
  const [activeTab, setActiveTab] = useState<ReportTab>(initialTab);
  const focusAreas = Array.isArray(parsed.page_4_focus_areas?.focus_areas) ? parsed.page_4_focus_areas?.focus_areas || [] : [];
  const groups = Array.isArray(parsed.page_5_question_groups?.question_groups) ? parsed.page_5_question_groups?.question_groups || [] : [];
  const [selectedFocusAreaKey, setSelectedFocusAreaKey] = useState<string>(() => getFocusAreaKey(focusAreas[0], 0));
  const annotationCount = countAnnotations(parsed.signal_data?.annotations);

  const activeFocusArea =
    focusAreas.find((focusArea, index) => getFocusAreaKey(focusArea, index) === selectedFocusAreaKey) ||
    focusAreas[0] ||
    null;

  const rootAnchorId = initialTab === "page5" ? "report-page5-question-groups" : "report-page4-focus-areas";

  return (
    <div id={rootAnchorId} className="space-y-5">
      {!hideInternalTabs ? (
        <Card title={title} description={description || "Structured presentation of synthesized Pages 4-5."}>
          <div className="metric-strip">
            <MetricPill label="Focus Areas" value={focusAreas.length} />
            <MetricPill label="Question Groups" value={groups.length} />
            <MetricPill label="Annotations" value={annotationCount} />
          </div>
        </Card>
      ) : null}

      <Card
        title={activeTab === "page4" ? "Focus Areas" : "Question Groups"}
        description={
          activeTab === "page4"
            ? "Rich interviewer-facing dossier notes generated from the grounded backend structure."
            : "Lean live-interview question groups generated from the focus areas."
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
                { value: "page5", label: "Page 5", meta: "Question groups" },
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
                  return (
                    <article
                      key={group.focus_area_id || group.group_label || index}
                      className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                    >
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">
                            {matchedFocusArea?.title || `Focus Area ${index + 1}`}
                          </p>
                          <h3 className="text-xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">
                            {group.group_label || "Question group"}
                          </h3>
                          {group.line_of_inquiry ? (
                            <p className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-7 text-[color:var(--ink)]">
                              <span className="font-semibold">Line of inquiry:</span> {group.line_of_inquiry}
                            </p>
                          ) : null}
                        </div>
                        <div className="space-y-3">
                          {(group.questions || []).map((question, questionIndex) => (
                            <div
                              key={question.question_id || `${group.focus_area_id || index}-${questionIndex}`}
                              className="rounded-[1rem] border border-slate-200 bg-slate-50/80 px-4 py-3 text-sm leading-7 text-[color:var(--ink)]"
                            >
                              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
                                Question {questionIndex + 1}
                              </p>
                              <p className="mt-1 font-semibold text-[color:var(--ink)]">{question.question || "Untitled question"}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </article>
                  );
                })
              ) : (
                <EmptyDetail text="No question groups have been generated yet." />
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
