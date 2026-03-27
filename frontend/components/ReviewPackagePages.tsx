"use client";

import { Fragment, type ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { JsonSection } from "@/components/JsonSection";

type EntityAnnotation = {
  signal_ids?: string[];
  theme_ids?: string[];
};

type FragmentAnnotation = {
  fragment_id: string;
  start_char: number;
  end_char: number;
  signal_ids?: string[];
  theme_ids?: string[];
};

type ReviewAnnotations = {
  page_2_entities?: Record<string, EntityAnnotation>;
  page_3_fragments?: Record<string, FragmentAnnotation[]>;
};

type Page2Record = Record<string, unknown> & { entity_id?: string };
type Page3Essay = {
  entity_id?: string;
  prompt?: string;
  full_text?: string;
  word_count?: number;
};

const PAGE_2_SECTIONS: Array<{ key: string; label: string }> = [
  { key: "academic_records", label: "Academic Records" },
  { key: "standardized_tests", label: "Standardized Tests" },
  { key: "extracurricular_activities", label: "Extracurricular Activities" },
  { key: "co_curricular_activities", label: "Co-Curricular Activities" },
  { key: "leadership_roles", label: "Leadership Roles" },
];

export function ReviewPageTwoSection({
  data,
  annotations,
}: {
  data: unknown;
  annotations?: ReviewAnnotations | null;
}) {
  const pageData = parsePageTwoData(data);
  if (!pageData) {
    return (
      <JsonSection
        title="ROS Page 2"
        description="Academic and engagement"
        data={data}
      />
    );
  }

  const entityAnnotations = annotations?.page_2_entities || {};

  return (
    <Card title="ROS Page 2" description="Academic and engagement">
      <div className="space-y-5">
        {PAGE_2_SECTIONS.map(({ key, label }) => {
          const items = pageData[key];
          if (!items || items.length === 0) {
            return null;
          }

          return (
            <div key={key} className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted">{label}</h3>
              <div className="space-y-3">
                {items.map((item, index) => {
                  const entityId = typeof item.entity_id === "string" ? item.entity_id : undefined;
                  const annotation = entityId ? entityAnnotations[entityId] : undefined;
                  const highlighted = Boolean(annotation);

                  return (
                    <article
                      key={`${key}-${entityId || index}`}
                      className={`rounded-lg border p-4 transition-colors ${
                        highlighted
                          ? "border-blue-300 bg-blue-50 shadow-sm"
                          : "border-line bg-surface"
                      }`}
                      title={buildAnnotationTitle(annotation)}
                    >
                      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                        <p className="font-semibold text-ink">{derivePageTwoTitle(item, label)}</p>
                        {entityId ? (
                          <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-muted shadow-sm">
                            {entityId}
                          </span>
                        ) : null}
                      </div>
                      {highlighted ? (
                        <p className="mb-2 text-xs font-medium text-blue-700">
                          Referenced in {annotation?.signal_ids?.length || 0} signal(s)
                          {annotation?.theme_ids?.length ? ` · ${annotation.theme_ids.join(", ")}` : ""}
                        </p>
                      ) : null}
                      <dl className="grid gap-2 text-sm text-ink md:grid-cols-2">
                        {Object.entries(item)
                          .filter(([entryKey]) => entryKey !== "entity_id")
                          .map(([entryKey, value]) => (
                            <Fragment key={entryKey}>
                              <dt className="font-medium capitalize text-muted">{formatKey(entryKey)}</dt>
                              <dd>{renderValue(value)}</dd>
                            </Fragment>
                          ))}
                      </dl>
                    </article>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export function ReviewPageThreeSection({
  data,
  annotations,
}: {
  data: unknown;
  annotations?: ReviewAnnotations | null;
}) {
  const pageData = parsePageThreeData(data);
  if (!pageData) {
    return (
      <JsonSection
        title="ROS Page 3"
        description="Essays"
        data={data}
      />
    );
  }

  const fragmentAnnotations = annotations?.page_3_fragments || {};

  return (
    <Card title="ROS Page 3" description="Essays">
      <div className="space-y-5">
        {pageData.essays.map((essay, index) => {
          const entityId = essay.entity_id || `essay-${index}`;
          const essayAnnotations = normalizeEssayAnnotations(fragmentAnnotations[entityId] || []);

          return (
            <article key={entityId} className="rounded-lg border border-line bg-surface p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-ink">{essay.prompt || "Essay"}</p>
                  <p className="text-xs text-muted">
                    {essay.entity_id || "Unknown essay"} · {essay.word_count || 0} words
                  </p>
                </div>
                {essayAnnotations.length ? (
                  <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                    {essayAnnotations.length} highlighted passage{essayAnnotations.length > 1 ? "s" : ""}
                  </span>
                ) : null}
              </div>
              <div className="text-sm leading-7 text-ink">
                {renderEssayText(essay.full_text || "", essayAnnotations)}
              </div>
            </article>
          );
        })}
      </div>
    </Card>
  );
}

function parsePageTwoData(data: unknown): Record<string, Page2Record[]> | null {
  if (!data || typeof data !== "object") {
    return null;
  }

  const parsed: Record<string, Page2Record[]> = {};
  for (const { key } of PAGE_2_SECTIONS) {
    const value = (data as Record<string, unknown>)[key];
    parsed[key] = Array.isArray(value) ? value.filter(isRecord) : [];
  }
  return parsed;
}

function parsePageThreeData(data: unknown): { essays: Page3Essay[] } | null {
  if (!data || typeof data !== "object") {
    return null;
  }
  const essays = (data as Record<string, unknown>).essays;
  if (!Array.isArray(essays)) {
    return null;
  }
  return {
    essays: essays.filter(isRecord).map((essay) => ({
      entity_id: typeof essay.entity_id === "string" ? essay.entity_id : undefined,
      prompt: typeof essay.prompt === "string" ? essay.prompt : undefined,
      full_text: typeof essay.full_text === "string" ? essay.full_text : undefined,
      word_count: typeof essay.word_count === "number" ? essay.word_count : undefined,
    })),
  };
}

function normalizeEssayAnnotations(annotations: FragmentAnnotation[]) {
  return annotations
    .filter(
      (annotation) =>
        Number.isInteger(annotation.start_char) &&
        Number.isInteger(annotation.end_char) &&
        annotation.start_char >= 0 &&
        annotation.end_char > annotation.start_char,
    )
    .sort((left, right) => left.start_char - right.start_char);
}

function renderEssayText(text: string, annotations: FragmentAnnotation[]) {
  if (!annotations.length) {
    return <p className="whitespace-pre-wrap">{text}</p>;
  }

  const elements: ReactNode[] = [];
  let cursor = 0;

  annotations.forEach((annotation) => {
    const start = Math.max(cursor, annotation.start_char);
    const end = Math.min(text.length, annotation.end_char);
    if (start > cursor) {
      elements.push(<Fragment key={`plain-${cursor}`}>{text.slice(cursor, start)}</Fragment>);
    }
    if (end > start) {
      elements.push(
        <span
          key={annotation.fragment_id}
          className="rounded-sm bg-amber-100/80 px-0.5 underline decoration-amber-600 decoration-2 underline-offset-4"
          title={buildAnnotationTitle(annotation)}
        >
          {text.slice(start, end)}
        </span>,
      );
      cursor = end;
    }
  });

  if (cursor < text.length) {
    elements.push(<Fragment key={`plain-${cursor}`}>{text.slice(cursor)}</Fragment>);
  }

  return <p className="whitespace-pre-wrap">{elements}</p>;
}

function buildAnnotationTitle(annotation?: EntityAnnotation | FragmentAnnotation) {
  if (!annotation) {
    return undefined;
  }

  const signalPart = annotation.signal_ids?.length ? `Signals: ${annotation.signal_ids.join(", ")}` : "";
  const themePart = annotation.theme_ids?.length ? `Themes: ${annotation.theme_ids.join(", ")}` : "";
  return [signalPart, themePart].filter(Boolean).join(" | ") || undefined;
}

function derivePageTwoTitle(item: Page2Record, label: string) {
  const candidates = [
    item.academic_level,
    item.test_name,
    item.activity_name,
    item.position_title,
  ];
  const title = candidates.find((candidate) => typeof candidate === "string" && candidate.trim().length > 0);
  return typeof title === "string" ? title : label.slice(0, -1);
}

function renderValue(value: unknown): React.ReactNode {
  if (value == null) {
    return <span className="text-muted">—</span>;
  }
  if (Array.isArray(value)) {
    if (!value.length) {
      return <span className="text-muted">—</span>;
    }
    return (
      <div className="space-y-1">
        {value.map((item, index) => (
          <div key={index} className="rounded bg-white px-2 py-1">
            {isRecord(item) ? JSON.stringify(item) : String(item)}
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === "object") {
    return <pre className="rounded bg-white px-2 py-1 text-xs">{JSON.stringify(value, null, 2)}</pre>;
  }
  return String(value);
}

function formatKey(value: string) {
  return value.replace(/_/g, " ");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
