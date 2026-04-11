"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

type ThemeRecord = {
  theme_id?: string;
  title?: string;
  unifying_axis?: string;
  interview_direction?: string;
  supporting_signal_ids?: string[];
  referenced_entity_ids?: string[];
};

type SignalRecord = {
  signal_id?: string;
  theme_id?: string;
  title?: string;
  evidence_anchor?: string;
  direct_read?: string;
  depth_opening?: string;
  why_it_matters?: string;
  referenced_entity_ids?: string[];
};

type QuestionGroupRecord = {
  theme_id?: string;
  group_title?: string;
  questions?: string[];
};

type ReportLike = Record<string, unknown> & {
  page_4_focus_areas?: {
    themes?: ThemeRecord[];
    signals?: SignalRecord[];
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
  const themes = Array.isArray(parsed.page_4_focus_areas?.themes) ? parsed.page_4_focus_areas?.themes || [] : [];
  const signals = Array.isArray(parsed.page_4_focus_areas?.signals) ? parsed.page_4_focus_areas?.signals || [] : [];
  const [selectedThemeKey, setSelectedThemeKey] = useState<string>(() => getThemeKey(themes[0], 0));
  const groups = Array.isArray(parsed.page_5_question_groups?.question_groups)
    ? parsed.page_5_question_groups?.question_groups || []
    : [];
  const annotationCount = countAnnotations(parsed.signal_data?.annotations);
  const activeTheme =
    themes.find((theme, index) => getThemeKey(theme, index) === selectedThemeKey) ||
    themes[0] ||
    null;
  const activeThemeSignals = activeTheme
    ? signals.filter(
        (signal) =>
          signal.theme_id === activeTheme.theme_id ||
          activeTheme.supporting_signal_ids?.includes(signal.signal_id || ""),
      )
    : [];

  return (
    <div className="space-y-5">
      {!hideInternalTabs ? (
        <Card title={title} description={description || "Structured presentation of synthesized Pages 4-5."}>
          <div className="metric-strip">
            <MetricPill label="Themes" value={themes.length} />
            <MetricPill label="Signals" value={signals.length} />
            <MetricPill label="Annotations" value={annotationCount} />
          </div>
        </Card>
      ) : null}

      <Card
        title={activeTab === "page4" ? "Focus Areas" : "Interview Questions"}
        description={
          activeTab === "page4"
            ? "Themes, signals, and deeper interview openings for the reviewer."
            : "Question groups generated from synthesized themes."
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
                { value: "page4", label: "Page 4", meta: "Themes and signals" },
                { value: "page5", label: "Page 5", meta: "Question groups" },
              ]}
            />
          ) : null}

          {activeTab === "page4" ? (
            <div className="grid gap-5 xl:grid-cols-[19rem_minmax(0,1fr)]">
              <section className="space-y-4">
                <div className="space-y-2 xl:hidden">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Themes</p>
                  <label className="sr-only" htmlFor="focus-theme-select">
                    Select theme
                  </label>
                  <select
                    id="focus-theme-select"
                    className="w-full rounded-[1rem] border border-[color:var(--line)] bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)] shadow-sm"
                    value={selectedThemeKey}
                    onChange={(event) => setSelectedThemeKey(event.target.value)}
                  >
                    {themes.map((theme, index) => (
                      <option key={getThemeKey(theme, index)} value={getThemeKey(theme, index)}>
                        {getThemeTabLabel(theme, index)}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="hidden space-y-3 xl:block">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Themes</p>
                  {themes.length ? (
                    themes.map((theme, index) => {
                      const themeKey = getThemeKey(theme, index);
                      const active = activeTheme ? getThemeKey(activeTheme, themes.indexOf(activeTheme)) === themeKey : false;
                      return (
                        <button
                          key={themeKey}
                          type="button"
                          onClick={() => setSelectedThemeKey(themeKey)}
                          className={`block w-full rounded-[1.3rem] border p-4 text-left transition ${
                            active
                              ? "border-blue-200 bg-[linear-gradient(145deg,rgba(239,246,255,0.98),rgba(255,255,255,0.94))] shadow-[0_18px_34px_rgba(15,23,42,0.08)]"
                              : "border-slate-200 bg-white/80 shadow-[0_16px_30px_rgba(15,23,42,0.06)] hover:bg-white/92"
                          }`}
                        >
                          <p className="text-sm font-semibold leading-6 text-[color:var(--ink)]">
                            {getThemeTabLabel(theme, index)}
                          </p>
                        </button>
                      );
                    })
                  ) : (
                    <EmptyDetail text="No synthesized themes yet." />
                  )}
                </div>
              </section>

              <section className="space-y-4">
                {activeTheme ? (
                  <>
                    <article className="rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.96),rgba(239,246,255,0.88),rgba(255,255,255,0.9))] p-5 shadow-[0_18px_34px_rgba(15,23,42,0.08)]">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">
                            Interview Focus
                          </p>
                          <h3 className="text-2xl font-semibold tracking-[-0.03em] text-[color:var(--ink)]">
                            {activeTheme.title || "Untitled theme"}
                          </h3>
                        </div>
                        {activeTheme.unifying_axis ? (
                          <p className="text-sm leading-7 text-[color:var(--muted)]">{activeTheme.unifying_axis}</p>
                        ) : null}
                        {activeTheme.interview_direction ? (
                          <div className="rounded-[1rem] bg-[color:var(--accent-soft)] px-4 py-3 text-sm leading-7 text-[color:var(--ink)]">
                            <span className="font-semibold">Interview direction:</span>{" "}
                            {activeTheme.interview_direction}
                          </div>
                        ) : null}
                      </div>
                    </article>

                    <div className="space-y-4">
                      {activeThemeSignals.length ? (
                        activeThemeSignals.map((signal, index) => (
                          <article
                            key={signal.signal_id || signal.title || index}
                            className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                          >
                            <div className="space-y-4">
                              <div className="space-y-2">
                                <p className="text-base font-semibold text-[color:var(--ink)]">
                                  {signal.title || `Signal ${index + 1}`}
                                </p>
                              </div>
                              <SignalBlock label="Direct read" value={signal.direct_read} />
                              <SignalBlock label="Why it matters" value={signal.why_it_matters} />
                              <SignalBlock label="Depth opening" value={signal.depth_opening} />
                              <EvidenceSources values={signal.referenced_entity_ids} />
                            </div>
                          </article>
                        ))
                      ) : (
                        <EmptyDetail text="No signals are attached to this theme yet." />
                      )}
                    </div>
                  </>
                ) : (
                  <EmptyDetail text="No synthesized themes yet." />
                )}
              </section>
            </div>
          ) : (
            <div className="space-y-4">
              {groups.length ? (
                groups.map((group, index) => (
                  <article
                    key={`${group.theme_id || "group"}-${index}`}
                    className="rounded-[1.3rem] border border-slate-200 bg-white/82 p-5 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      {group.theme_id ? <Tag>{group.theme_id}</Tag> : null}
                      <p className="text-base font-semibold text-[color:var(--ink)]">{group.group_title || "Question group"}</p>
                    </div>
                    <ol className="mt-4 grid gap-3">
                      {(group.questions || []).map((question, questionIndex) => (
                        <li
                          key={`${group.theme_id || "question"}-${questionIndex}`}
                          className="grid gap-3 rounded-[1rem] border border-[color:var(--line)] bg-slate-50/70 px-4 py-3 md:grid-cols-[2rem_1fr]"
                        >
                          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[color:var(--accent-soft)] text-xs font-bold text-[color:var(--accent-strong)]">
                            {questionIndex + 1}
                          </span>
                          <span className="text-sm leading-7 text-[color:var(--ink)]">{question}</span>
                        </li>
                      ))}
                    </ol>
                  </article>
                ))
              ) : (
                <EmptyDetail text="No synthesized question groups yet." />
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
    <div className="metric-card px-4 py-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]">{value}</p>
    </div>
  );
}

function SignalBlock({ label, value }: { label: string; value?: string }) {
  if (!value) {
    return null;
  }

  return (
    <div className="mt-4">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-2 text-sm leading-7 text-[color:var(--ink)]">{value}</p>
    </div>
  );
}

function EvidenceSources({ values }: { values?: string[] }) {
  if (!values?.length) {
    return null;
  }

  const grouped = groupEvidenceSources(values);
  const bucketLabels = Object.keys(grouped);

  return (
    <details className="mt-4 rounded-[1rem] border border-[color:var(--line)] bg-slate-50/78 px-4 py-3">
      <summary className="cursor-pointer list-none">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">
            Evidence sources
          </span>
          {bucketLabels.map((label) => (
            <BucketChip key={label} label={label} />
          ))}
        </div>
      </summary>
      <div className="mt-3 grid gap-3">
        {Object.entries(grouped).map(([label, entries]) => (
          <div key={label} className="space-y-2">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">{label}</p>
            <div className="flex flex-wrap gap-2">
              {entries.map((entry) => (
                <span
                  key={`${label}-${entry}`}
                  className="inline-flex rounded-full border border-[color:var(--line)] bg-white px-3 py-1.5 text-xs font-medium text-[color:var(--ink)] shadow-sm"
                >
                  {entry}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

function BucketChip({ label }: { label: string }) {
  return (
    <span className="inline-flex rounded-full bg-[color:var(--accent-soft)] px-2.5 py-1 text-[11px] font-bold text-[color:var(--accent-strong)]">
      {label}
    </span>
  );
}

function MetaRow({ label, values }: { label: string; values?: string[] }) {
  if (!values?.length) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-wrap items-start gap-2">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">{label}</span>
      <div className="flex flex-wrap gap-2">
        {values.map((value) => (
          <Tag key={value} tone="soft">
            {value}
          </Tag>
        ))}
      </div>
    </div>
  );
}

function Tag({ children, tone = "default" }: { children: React.ReactNode; tone?: "default" | "soft" }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${
        tone === "default"
          ? "bg-[color:var(--signal-soft)] text-[color:var(--signal)]"
          : "bg-slate-100/90 text-slate-700"
      }`}
    >
      {children}
    </span>
  );
}

function EmptyDetail({ text }: { text: string }) {
  return (
    <div className="rounded-[1.3rem] border border-dashed border-slate-300 bg-white/72 px-5 py-6 text-sm text-[color:var(--muted)]">
      {text}
    </div>
  );
}

function countAnnotations(annotations?: Record<string, unknown>) {
  if (!annotations) {
    return 0;
  }

  const page2 = annotations.page_2_entities;
  const page3 = annotations.page_3_fragments;
  const page2Count = page2 && typeof page2 === "object" && !Array.isArray(page2) ? Object.keys(page2).length : 0;
  const page3Count =
    page3 && typeof page3 === "object" && !Array.isArray(page3)
      ? Object.values(page3).reduce((sum, value) => sum + (Array.isArray(value) ? value.length : 0), 0)
      : 0;

  return page2Count + page3Count;
}

function getThemeKey(theme: ThemeRecord | undefined, index: number) {
  return theme?.theme_id || theme?.title || `theme-${index}`;
}

function getThemeTabLabel(theme: ThemeRecord, index: number) {
  const title = theme.title?.trim();
  if (!title) {
    return `Theme ${index + 1}`;
  }

  const separators = [":", " or ", " and ", ","];
  for (const separator of separators) {
    if (title.includes(separator)) {
      const leading = title.split(separator)[0]?.trim();
      if (leading) {
        return leading;
      }
    }
  }

  return title.length > 34 ? `${title.slice(0, 31).trimEnd()}...` : title;
}

function groupEvidenceSources(values: string[]) {
  const grouped: Record<string, string[]> = {};

  for (const value of values) {
    const bucket = getEvidenceBucket(value);
    const detail = getEvidenceDetail(value);
    if (!grouped[bucket]) {
      grouped[bucket] = [];
    }
    if (!grouped[bucket].includes(detail)) {
      grouped[bucket].push(detail);
    }
  }

  return grouped;
}

function getEvidenceBucket(value: string) {
  if (value.startsWith("ACA-")) {
    return "Academics";
  }
  if (value.startsWith("ACT-") || value.startsWith("LEAD-")) {
    return "Activities";
  }
  if (value.startsWith("TEST-")) {
    return "Tests";
  }
  if (value.startsWith("ESS-")) {
    return "Writing";
  }
  return "Application";
}

function getEvidenceDetail(value: string) {
  if (value.startsWith("ACA-")) {
    const number = parseInt(value.replace("ACA-", ""), 10);
    return Number.isFinite(number) ? `Academic record ${number}` : "Academic record";
  }
  if (value.startsWith("ACT-")) {
    const number = parseInt(value.replace("ACT-", ""), 10);
    return Number.isFinite(number) ? `Activity ${number}` : "Activity";
  }
  if (value.startsWith("LEAD-")) {
    const number = parseInt(value.replace("LEAD-", ""), 10);
    return Number.isFinite(number) ? `Leadership ${number}` : "Leadership";
  }
  if (value.startsWith("TEST-")) {
    const number = parseInt(value.replace("TEST-", ""), 10);
    return Number.isFinite(number) ? `Test ${number}` : "Test";
  }
  if (value.startsWith("ESS-")) {
    const number = parseInt(value.replace("ESS-", ""), 10);
    return Number.isFinite(number) ? `Essay ${number}` : "Essay";
  }
  return "Source detail";
}
