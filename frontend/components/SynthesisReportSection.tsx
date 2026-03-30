"use client";

import { useState } from "react";
import { Card } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";

type ThemeRecord = {
  theme_id?: string;
  title?: string;
  framing?: string;
  what_this_theme_must_resolve?: string;
  supporting_signal_ids?: string[];
  referenced_entity_ids?: string[];
};

type SignalRecord = {
  signal_id?: string;
  theme_id?: string;
  title?: string;
  evidence_anchor?: string;
  direct_read?: string;
  what_remains_open?: string;
  why_it_matters?: string;
  referenced_entity_ids?: string[];
};

type QuestionGroupRecord = {
  theme_id?: string;
  group_title?: string;
  questions?: string[];
};

type DraftLike = Record<string, unknown> & {
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

type DraftTab = "page4" | "page5";

export function SynthesisReportSection({
  draft,
  title = "Draft Report",
  description,
}: {
  draft: Record<string, unknown>;
  title?: string;
  description?: string;
}) {
  const parsed = draft as DraftLike;
  const [activeTab, setActiveTab] = useState<DraftTab>("page4");
  const themes = Array.isArray(parsed.page_4_focus_areas?.themes) ? parsed.page_4_focus_areas?.themes || [] : [];
  const signals = Array.isArray(parsed.page_4_focus_areas?.signals) ? parsed.page_4_focus_areas?.signals || [] : [];
  const groups = Array.isArray(parsed.page_5_question_groups?.question_groups)
    ? parsed.page_5_question_groups?.question_groups || []
    : [];
  const annotationCount = countAnnotations(parsed.signal_data?.annotations);

  return (
    <div className="space-y-5">
      <Card title={title} description={description || "Structured presentation of synthesized Pages 4-5."}>
        <div className="metric-strip">
          <MetricPill label="Themes" value={themes.length} />
          <MetricPill label="Signals" value={signals.length} />
          <MetricPill label="Annotations" value={annotationCount} />
        </div>
      </Card>

      <Card
        title={activeTab === "page4" ? "ROS Page 4" : "ROS Page 5"}
        description={
          activeTab === "page4"
            ? "Focus areas, themes, and signal framing."
            : "Question groups generated from synthesized themes."
        }
      >
        <div className="space-y-5">
          <SegmentedControl
            label="Synthesis pages"
            value={activeTab}
            onChange={setActiveTab}
            options={[
              { value: "page4", label: "Page 4", meta: "Themes and signals" },
              { value: "page5", label: "Page 5", meta: "Question groups" },
            ]}
          />

          {activeTab === "page4" ? (
            <div className="grid gap-5 xl:grid-cols-[0.88fr_1.12fr]">
              <section className="space-y-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Themes</p>
                {themes.length ? (
                  themes.map((theme) => (
                    <article
                      key={theme.theme_id || theme.title}
                      className="rounded-[1.3rem] border border-[color:var(--line)] bg-white/82 p-4 shadow-[var(--card-shadow-soft)]"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        {theme.theme_id ? <Tag>{theme.theme_id}</Tag> : null}
                        <p className="text-base font-semibold text-[color:var(--ink)]">{theme.title || "Untitled theme"}</p>
                      </div>
                      {theme.framing ? <p className="mt-3 text-sm leading-7 text-[color:var(--muted)]">{theme.framing}</p> : null}
                      {theme.what_this_theme_must_resolve ? (
                        <div className="mt-4 rounded-[1rem] bg-[color:var(--accent-soft)] px-4 py-3 text-sm leading-6 text-[color:var(--ink)]">
                          <span className="font-semibold">Must resolve:</span> {theme.what_this_theme_must_resolve}
                        </div>
                      ) : null}
                      <MetaRow label="Signals" values={theme.supporting_signal_ids} />
                      <MetaRow label="References" values={theme.referenced_entity_ids} />
                    </article>
                  ))
                ) : (
                  <EmptyDetail text="No synthesized themes yet." />
                )}
              </section>

              <section className="space-y-4">
                <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[color:var(--muted)]">Signals</p>
                {signals.length ? (
                  signals.map((signal) => (
                    <article
                      key={signal.signal_id || signal.title}
                      className="rounded-[1.3rem] border border-[color:var(--line)] bg-white/82 p-4 shadow-[var(--card-shadow-soft)]"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        {signal.signal_id ? <Tag>{signal.signal_id}</Tag> : null}
                        {signal.theme_id ? <Tag tone="soft">{signal.theme_id}</Tag> : null}
                        <p className="text-base font-semibold text-[color:var(--ink)]">{signal.title || "Untitled signal"}</p>
                      </div>
                      <SignalBlock label="Evidence anchor" value={signal.evidence_anchor} />
                      <SignalBlock label="Direct read" value={signal.direct_read} />
                      <SignalBlock label="What remains open" value={signal.what_remains_open} />
                      <SignalBlock label="Why it matters" value={signal.why_it_matters} />
                      <MetaRow label="Entity IDs" values={signal.referenced_entity_ids} />
                    </article>
                  ))
                ) : (
                  <EmptyDetail text="No synthesized signals yet." />
                )}
              </section>
            </div>
          ) : (
            <div className="space-y-4">
              {groups.length ? (
                groups.map((group, index) => (
                  <article
                    key={`${group.theme_id || "group"}-${index}`}
                    className="rounded-[1.3rem] border border-[color:var(--line)] bg-white/82 p-5 shadow-[var(--card-shadow-soft)]"
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
    <div className="rounded-[1.3rem] border border-dashed border-[color:var(--line-strong)] bg-white/72 px-5 py-6 text-sm text-[color:var(--muted)]">
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
