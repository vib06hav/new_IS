"use client";

import { Fragment, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
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
  themes?: ThemeRecord[];
  signals?: SignalRecord[];
};

type ThemeRecord = {
  theme_id?: string;
  title?: string;
  unifying_axis?: string;
  interview_direction?: string;
  supporting_signal_ids?: string[];
};

type SignalRecord = {
  signal_id?: string;
  theme_id?: string;
  title?: string;
  direct_read?: string;
  why_it_matters?: string;
  depth_opening?: string;
};

type Page2Record = Record<string, unknown> & { entity_id?: string };
type PageTwoData = {
  academicRecords: Page2Record[];
  activities: Page2Record[];
  leadership: Page2Record[];
  tests: Page2Record[];
};
type Page3Essay = {
  entity_id?: string;
  prompt?: string;
  full_text?: string;
  word_count?: number;
};

type PageOneData = {
  applicantName?: string;
  dateOfBirth?: string;
  intendedCourse?: string;
  location?: string;
  familyMembers: Array<{
    label: string;
    name?: string;
    education?: string;
    occupation?: string;
    organization?: string;
    role?: string;
  }>;
  schoolHistory: Array<{
    level?: string;
    schoolName?: string;
    boardName?: string;
    entityId?: string;
  }>;
};

const PAGE_2_SECTIONS: Array<{ key: string; label: string }> = [
  { key: "academic_records", label: "Academic Records" },
  { key: "standardized_tests", label: "Standardized Tests" },
  { key: "extracurricular_activities", label: "Extracurricular Activities" },
  { key: "co_curricular_activities", label: "Co-Curricular Activities" },
  { key: "leadership_roles", label: "Leadership Roles" },
];

export function ReviewPageOneSection({ data }: { data: unknown }) {
  const pageData = parsePageOneData(data);
  if (!pageData) {
    return (
      <div id="report-page1-overview">
        <JsonSection title="Application Overview" description="Applicant summary" data={data} />
      </div>
    );
  }

  return (
    <div id="report-page1-overview" className="space-y-4">
      <section className="rounded-[1.8rem] border border-slate-200 bg-[linear-gradient(145deg,rgba(255,255,255,0.96),rgba(239,246,255,0.88),rgba(255,255,255,0.9))] p-5 shadow-[0_20px_42px_rgba(15,23,42,0.08)]">
        <div className="max-w-4xl space-y-3">
          <div className="space-y-2">
            <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-[color:var(--muted)]">Application Overview</p>
            <h2 className="text-3xl font-semibold tracking-[-0.04em] text-[color:var(--ink)] md:text-[2.35rem]">
              {pageData.applicantName || "Applicant name unavailable"}
            </h2>
            <div className="flex flex-wrap gap-x-5 gap-y-1 text-base leading-7 text-[color:var(--muted)]">
              {pageData.intendedCourse ? (
                <span className="font-medium text-[color:var(--ink)]">Preferred Major: {pageData.intendedCourse}</span>
              ) : null}
              {pageData.location ? <span>{pageData.location}</span> : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm leading-6 text-[color:var(--muted)]">
            {pageData.dateOfBirth ? <span>Date of Birth: {formatDate(pageData.dateOfBirth)}</span> : null}
          </div>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Card title="Family Context" description="Key household background for reviewer orientation" eyebrow={null}>
          <div className={`grid gap-4 ${pageData.familyMembers.length > 1 ? "md:grid-cols-2" : ""}`}>
            {pageData.familyMembers.length ? (
              pageData.familyMembers.map((member) => (
                <article
                  key={member.label}
                  className="rounded-[1.35rem] border border-slate-200 bg-white/82 p-4 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                >
                  <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--muted)]">
                    {member.label}
                  </p>
                  <p className="mt-3 text-lg font-semibold text-[color:var(--ink)]">
                    {member.name || "Information unavailable"}
                  </p>
                  <dl className="mt-4 grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
                    <InfoRow label="Education" value={member.education} />
                    <InfoRow label="Occupation" value={member.occupation} />
                    <InfoRow label="Organisation" value={member.organization} />
                    <InfoRow label="Role" value={member.role} />
                  </dl>
                </article>
              ))
            ) : (
              <EmptyStateCopy text="Family background information is not available for this application." />
            )}
          </div>
        </Card>

        <Card title="Schooling Background" description="Educational progression at a glance" eyebrow={null}>
          <div className="space-y-2.5">
            {pageData.schoolHistory.length ? (
              pageData.schoolHistory.map((school, index) => (
                <article
                  key={school.entityId || `${school.level || "level"}-${index}`}
                  className="grid gap-3 rounded-[1.3rem] border border-slate-200 bg-white/82 p-4 shadow-[0_16px_30px_rgba(15,23,42,0.06)] sm:grid-cols-[4.5rem_minmax(0,1fr)]"
                >
                  <div className="inline-flex h-fit w-fit min-w-[4.5rem] items-center justify-center rounded-full bg-[color:var(--accent-soft)] px-3 py-2 text-sm font-semibold text-[color:var(--accent-strong)]">
                    {school.level || `Stage ${index + 1}`}
                  </div>
                  <div className="space-y-1">
                    <p className="text-base font-semibold text-[color:var(--ink)]">
                      {school.schoolName || "School unavailable"}
                    </p>
                    <p className="text-sm leading-6 text-[color:var(--muted)]">
                      {school.boardName || "Board information unavailable"}
                    </p>
                  </div>
                </article>
              ))
            ) : (
              <EmptyStateCopy text="Schooling history is not available for this application." />
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function ReviewPageTwoSectionLegacy({
  data,
  annotations,
}: {
  data: unknown;
  annotations?: ReviewAnnotations | null;
}) {
  const pageData = parsePageTwoData(data);
  if (!pageData) {
    return <JsonSection title="Academics & Activities" description="Academic and engagement" data={data} />;
  }

  const entityAnnotations = annotations?.page_2_entities || {};

  return (
    <Card title="Academics & Activities" description="Academic and engagement" eyebrow={null}>
      <div className="space-y-5">
        {PAGE_2_SECTIONS.map(({ key, label }) => {
          const items = pageData[key];
          if (!items || items.length === 0) {
            return null;
          }

          return (
            <div key={key} className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-[color:var(--muted)]">{label}</h3>
              <div className="space-y-3">
                {items.map((item, index) => {
                  const entityId = typeof item.entity_id === "string" ? item.entity_id : undefined;
                  const annotation = entityId ? entityAnnotations[entityId] : undefined;
                  const highlighted = Boolean(annotation);

                  return (
                    <article
                      key={`${key}-${entityId || index}`}
                      className={`group/annotation relative rounded-[1.2rem] border p-4 transition-colors ${highlighted
                          ? "border-blue-200 bg-[linear-gradient(180deg,rgba(239,246,255,0.98),rgba(255,255,255,0.96))] shadow-[0_16px_30px_rgba(59,130,246,0.10)]"
                          : "border-slate-200 bg-white/80 shadow-[0_16px_30px_rgba(15,23,42,0.06)]"
                        }`}
                    >
                      <StyledTooltip content={buildAnnotationTitle(annotation, annotations)} />
                      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                        <p className="font-semibold text-[color:var(--ink)]">{derivePageTwoTitle(item, label)}</p>
                        {entityId ? (
                          <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-[color:var(--muted)] shadow-sm">
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
                      <dl className="grid gap-2 text-sm text-[color:var(--ink)] md:grid-cols-2">
                        {Object.entries(item)
                          .filter(([entryKey]) => entryKey !== "entity_id")
                          .map(([entryKey, value]) => (
                            <Fragment key={entryKey}>
                              <dt className="font-medium capitalize text-[color:var(--muted)]">{formatKey(entryKey)}</dt>
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

export function ReviewPageTwoSection({
  data,
  annotations,
}: {
  data: unknown;
  annotations?: ReviewAnnotations | null;
}) {
  const pageData = parsePageTwoDisplayData(data);
  if (!pageData) {
    return (
      <div id="report-page2-academics">
        <JsonSection title="Academics & Activities" description="Academic and engagement" data={data} />
      </div>
    );
  }

  const entityAnnotations = annotations?.page_2_entities || {};
  const [selectedAcademic, setSelectedAcademic] = useState(0);
  const [selectedActivity, setSelectedActivity] = useState(0);
  const [selectedLeadership, setSelectedLeadership] = useState(0);
  const [selectedTest, setSelectedTest] = useState(0);

  const activeAcademic = getTabbedItem(pageData.academicRecords, selectedAcademic);
  const activeActivity = getTabbedItem(pageData.activities, selectedActivity);
  const activeLeadership = getTabbedItem(pageData.leadership, selectedLeadership);
  const activeTest = getTabbedItem(pageData.tests, selectedTest);

  return (
    <Card title="Academics & Activities" description="Study and engagement" eyebrow={null}>
      <div className="grid gap-4 xl:grid-cols-2">
        <PageTwoPanel
          anchorId="report-page2-academics"
          title="Academic Records"
          description=""
          tabs={pageData.academicRecords.map((record, index) => ({
            key: `academic-${record.entity_id || index}`,
            label: normalizeAcademicLabel(record, index),
            anchorId: readString(record.entity_id) ? buildEntityAnchorId(readString(record.entity_id)!) : undefined,
            highlighted: Boolean(getItemAnnotation(record, entityAnnotations)),
            title: buildItemAnnotationTitle(record, annotations),
          }))}
          activeIndex={activeAcademic ? Math.min(selectedAcademic, pageData.academicRecords.length - 1) : -1}
          onSelect={setSelectedAcademic}
          highlighted={Boolean(activeAcademic && getItemAnnotation(activeAcademic, entityAnnotations))}
          annotationTitle={buildItemAnnotationTitle(activeAcademic, annotations)}
        >
          {activeAcademic ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-xl font-semibold tracking-tight text-[color:var(--ink)]">
                    {normalizeAcademicLabel(activeAcademic, 0)}
                  </p>
                  <p className="text-sm leading-6 text-[color:var(--muted)]">
                    {readString(activeAcademic.board_name) || "Board information unavailable"}
                  </p>
                  <RelationSummary item={activeAcademic} annotations={annotations} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <CompactMetric
                    label="Overall Score"
                    value={formatAcademicScore(activeAcademic.score_raw, activeAcademic.grading_mode)}
                  />
                  {formatAcademicScore(activeAcademic.predicted_score_raw, activeAcademic.grading_mode) ? (
                    <CompactMetric
                      label="Predicted"
                      value={formatAcademicScore(activeAcademic.predicted_score_raw, activeAcademic.grading_mode)}
                    />
                  ) : null}
                </div>
              </div>

              <div className="overflow-hidden rounded-[1.1rem] border border-slate-200 bg-white/80">
                <table className="min-w-full divide-y divide-[color:var(--line)] text-sm">
                  <thead className="bg-slate-50/85 text-left text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
                    <tr>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3 text-right">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[color:var(--line)] text-[color:var(--ink)]">
                    {getSubjectEntries(activeAcademic).length ? (
                      getSubjectEntries(activeAcademic).map((subject, index) => (
                        <tr key={`${readString(subject.subject_name) || "subject"}-${index}`}>
                          <td className="px-4 py-3 font-medium">
                            {readString(subject.subject_name) || `Subject ${index + 1}`}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold tabular-nums">
                            {formatScoreWithMax(subject.score_raw, subject.max_score_raw)}
                            {readString(subject.predicted_score_raw) ? (
                              <span className="ml-2 text-xs font-medium text-[color:var(--muted)]">
                                Pred. {readString(subject.predicted_score_raw)}
                              </span>
                            ) : null}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={2} className="px-4 py-4 text-sm text-[color:var(--muted)]">
                          Subject-wise marks are not available for this class record.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <EmptyStateCopy text="Academic records are not available for this application." />
          )}
        </PageTwoPanel>

        <PageTwoPanel
          anchorId="report-page2-activities"
          title="Activities"
          description=""
          tabs={pageData.activities.map((activity, index) => ({
            key: `activity-${activity.entity_id || index}`,
            label: `ACT${index + 1}`,
            anchorId: readString(activity.entity_id) ? buildEntityAnchorId(readString(activity.entity_id)!) : undefined,
            highlighted: Boolean(getItemAnnotation(activity, entityAnnotations)),
            title: buildItemAnnotationTitle(activity, annotations),
          }))}
          activeIndex={activeActivity ? Math.min(selectedActivity, pageData.activities.length - 1) : -1}
          onSelect={setSelectedActivity}
          highlighted={Boolean(activeActivity && getItemAnnotation(activeActivity, entityAnnotations))}
          annotationTitle={buildItemAnnotationTitle(activeActivity, annotations)}
        >
          {activeActivity ? (
            <div className="space-y-4">
              <div className="space-y-1">
                <UserProvidedText
                  value={readString(activeActivity.activity_name) || "Activity"}
                  className="text-xl font-semibold tracking-tight text-[color:var(--ink)]"
                />
                {normalizeActivityType(activeActivity.activity_type) ? (
                  <p className="text-sm leading-6 text-[color:var(--muted)]">
                    {normalizeActivityType(activeActivity.activity_type)}
                  </p>
                ) : null}
                <RelationSummary item={activeActivity} annotations={annotations} />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <InfoRow label="Highest Level" value={readString(activeActivity.level)} />
                <InfoRow label="Duration" value={formatDuration(activeActivity.duration_years ?? activeActivity.duration)} />
                <InfoRow label="Role" value={readString(activeActivity.position_title)} />
                <InfoRow label="Achievement" value={readString(activeActivity.achievement)} />
              </div>

              {readString(activeActivity.roles_and_responsibilities) ? (
                <section className="rounded-[1.1rem] border border-slate-200 bg-white/78 p-4">
                  <UserProvidedText
                    label="Responsibilities"
                    value={readString(activeActivity.roles_and_responsibilities)!}
                    className="mt-2 whitespace-pre-wrap text-sm leading-7 text-[color:var(--ink)]"
                  />
                </section>
              ) : null}

              {readString(activeActivity.description_raw) ? (
                <section className="rounded-[1.1rem] border border-slate-200 bg-white/78 p-4">
                  <UserProvidedText
                    label="Description"
                    value={readString(activeActivity.description_raw)!}
                    className="mt-2 whitespace-pre-wrap text-sm leading-7 text-[color:var(--ink)]"
                  />
                </section>
              ) : null}

              {!hasDisplayValue([
                readString(activeActivity.position_title),
                readString(activeActivity.achievement),
                readString(activeActivity.roles_and_responsibilities),
                readString(activeActivity.description_raw),
              ]) ? (
                <EmptyStateCopy text="No additional activity details were provided for this entry." />
              ) : null}
            </div>
          ) : (
            <EmptyStateCopy text="Activity information is not available for this application." />
          )}
        </PageTwoPanel>

        <PageTwoPanel
          anchorId="report-page2-leadership"
          title="Leadership"
          description=""
          tabs={pageData.leadership.map((entry, index) => ({
            key: `lead-${entry.entity_id || index}`,
            label: `LEAD${index + 1}`,
            anchorId: readString(entry.entity_id) ? buildEntityAnchorId(readString(entry.entity_id)!) : undefined,
            highlighted: Boolean(getItemAnnotation(entry, entityAnnotations)),
            title: buildItemAnnotationTitle(entry, annotations),
          }))}
          activeIndex={activeLeadership ? Math.min(selectedLeadership, pageData.leadership.length - 1) : -1}
          onSelect={setSelectedLeadership}
          highlighted={Boolean(activeLeadership && getItemAnnotation(activeLeadership, entityAnnotations))}
          annotationTitle={buildItemAnnotationTitle(activeLeadership, annotations)}
        >
          {activeLeadership ? (
            <div className="space-y-4">
              <div className="space-y-1">
                <UserProvidedText
                  value={readString(activeLeadership.position_title) || "Leadership Role"}
                  className="text-lg font-semibold tracking-tight text-[color:var(--ink)]"
                />
                {[readString(activeLeadership.activity_name), readString(activeLeadership.level)].filter(Boolean)
                  .length ? (
                  <p className="text-sm leading-6 text-[color:var(--muted)]">
                    {[readString(activeLeadership.activity_name), readString(activeLeadership.level)]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                ) : null}
                <RelationSummary item={activeLeadership} annotations={annotations} />
              </div>

              <div className="grid gap-3">
                <InfoRow label="Duration" value={formatDuration(activeLeadership.duration_years ?? activeLeadership.duration)} />
                <InfoRow label="Achievement" value={readString(activeLeadership.achievement)} />
                <InfoRow
                  label="Responsibilities"
                  value={readString(activeLeadership.roles_and_responsibilities)}
                />
              </div>

              {readString(activeLeadership.description_raw) ? (
                <section className="rounded-[1.1rem] border border-slate-200 bg-white/78 p-4">
                  <UserProvidedText
                    label="Description"
                    value={readString(activeLeadership.description_raw)!}
                    className="mt-2 whitespace-pre-wrap text-sm leading-7 text-[color:var(--ink)]"
                  />
                </section>
              ) : null}

              {!hasDisplayValue([
                readString(activeLeadership.achievement),
                readString(activeLeadership.roles_and_responsibilities),
                readString(activeLeadership.description_raw),
              ]) ? (
                <EmptyStateCopy text="No additional leadership notes were provided for this entry." />
              ) : null}
            </div>
          ) : (
            <EmptyStateCopy text="Leadership information is not available for this application." />
          )}
        </PageTwoPanel>

        <PageTwoPanel
          anchorId="report-page2-tests"
          title="Tests"
          description=""
          tabs={pageData.tests.map((entry, index) => ({
            key: `test-${entry.entity_id || index}`,
            label: normalizeTestLabel(entry, index),
            anchorId: readString(entry.entity_id) ? buildEntityAnchorId(readString(entry.entity_id)!) : undefined,
            highlighted: Boolean(getItemAnnotation(entry, entityAnnotations)),
            title: buildItemAnnotationTitle(entry, annotations),
          }))}
          activeIndex={activeTest ? Math.min(selectedTest, pageData.tests.length - 1) : -1}
          onSelect={setSelectedTest}
          highlighted={Boolean(activeTest && getItemAnnotation(activeTest, entityAnnotations))}
          annotationTitle={buildItemAnnotationTitle(activeTest, annotations)}
        >
          {activeTest ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-lg font-semibold tracking-tight text-[color:var(--ink)]">
                    {readString(activeTest.test_name) || "Test"}
                  </p>
                  <RelationSummary item={activeTest} annotations={annotations} />
                </div>
                <CompactMetric label="Overall Result" value={formatTestScore(activeTest)} />
              </div>

              <div className="overflow-hidden rounded-[1.1rem] border border-slate-200 bg-white/80">
                <table className="min-w-full divide-y divide-[color:var(--line)] text-sm">
                  <thead className="bg-slate-50/85 text-left text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
                    <tr>
                      <th className="px-4 py-3">Section</th>
                      <th className="px-4 py-3 text-right">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[color:var(--line)] text-[color:var(--ink)]">
                    {getSectionalScores(activeTest).length ? (
                      getSectionalScores(activeTest).map((score, index) => (
                        <tr key={`${readString(score.label) || "section"}-${index}`}>
                          <td className="px-4 py-3 font-medium">
                            {readString(score.label) || `Section ${index + 1}`}
                          </td>
                          <td className="px-4 py-3 text-right font-semibold tabular-nums">
                            {readString(score.raw_score) || "—"}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={2} className="px-4 py-4 text-sm text-[color:var(--muted)]">
                          Section-level scores are not available for this test entry.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <EmptyStateCopy text="Test information is not available for this application." />
          )}
        </PageTwoPanel>
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
      <div id="report-page3-essays">
        <JsonSection title="Writing" description="Essays and highlighted excerpts" data={data} />
      </div>
    );
  }

  const fragmentAnnotations = annotations?.page_3_fragments || {};

  return (
    <div id="report-page3-essays">
      <Card title="Writing" description="Essays and highlighted excerpts" eyebrow={null}>
      <div className="space-y-5">
        {pageData.essays.map((essay, index) => {
          const entityId = essay.entity_id || `essay-${index}`;
          const essayAnnotations = normalizeEssayAnnotations(fragmentAnnotations[entityId] || []);

          return (
            <article
              key={entityId}
              className="rounded-[1.8rem] border border-slate-200 bg-white/85 p-6 shadow-[0_18px_38px_rgba(15,23,42,0.06)] md:p-10"
            >
              <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-6">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-bold tracking-tight text-slate-800">{essay.prompt || "Personal Statement"}</p>
                  </div>
                  <p className="text-[11px] font-medium tracking-wide text-slate-400">{essay.word_count || 0} words</p>
                  <p className="hidden text-[11px] font-medium tracking-wide text-slate-400">
                    {essay.word_count || 0} words {essay.entity_id ? `· ID: ${essay.entity_id}` : ""}
                  </p>
                </div>
                {essayAnnotations.length ? (
                  <span className="rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-bold tracking-tight text-blue-700 ring-1 ring-inset ring-blue-700/10">
                    {essayAnnotations.length} Highlighted Excerpt{essayAnnotations.length > 1 ? "s" : ""}
                  </span>
                ) : null}
              </div>
              <div className="text-base leading-relaxed text-slate-700">
                <div>
                  {renderEssayText(essay.full_text || "", essayAnnotations, annotations)}
                </div>
              </div>
            </article>
          );
        })}
      </div>
      </Card>
    </div>
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

function parsePageTwoDisplayData(data: unknown): PageTwoData | null {
  if (!isRecord(data)) {
    return null;
  }

  const academicRecords = Array.isArray(data.academic_records) ? data.academic_records.filter(isRecord) : [];
  const extracurricular = Array.isArray(data.extracurricular_activities)
    ? data.extracurricular_activities.filter(isRecord)
    : [];
  const coCurricular = Array.isArray(data.co_curricular_activities)
    ? data.co_curricular_activities.filter(isRecord)
    : [];
  const leadership = Array.isArray(data.leadership_roles) ? data.leadership_roles.filter(isRecord) : [];
  const standardizedTests = Array.isArray(data.standardized_tests) ? data.standardized_tests.filter(isRecord) : [];
  const additionalTests = Array.isArray(data.additional_tests) ? data.additional_tests.filter(isRecord) : [];

  return {
    academicRecords,
    activities: [...extracurricular, ...coCurricular],
    leadership,
    tests: [...standardizedTests, ...additionalTests],
  };
}

function getTabbedItem(items: Page2Record[], index: number) {
  if (!items.length) {
    return undefined;
  }
  return items[Math.min(Math.max(index, 0), items.length - 1)];
}

function getItemAnnotation(item: Page2Record | undefined, annotations: Record<string, EntityAnnotation>) {
  const entityId = item && typeof item.entity_id === "string" ? item.entity_id : undefined;
  return entityId ? annotations[entityId] : undefined;
}

function buildItemAnnotationTitle(item: Page2Record | undefined, annotations?: ReviewAnnotations | null) {
  return buildAnnotationTitle(getItemAnnotation(item, annotations?.page_2_entities || {}), annotations);
}

function RelationSummary({ item, annotations }: { item: Page2Record | undefined; annotations?: ReviewAnnotations | null }) {
  const annotation = getItemAnnotation(item, annotations?.page_2_entities || {});
  if (!annotation) {
    return null;
  }

  const themeMap = buildThemeMap(annotations?.themes || []);
  const signalMap = buildSignalMap(annotations?.signals || []);
  const themeTitle = (annotation.theme_ids || []).map((themeId) => themeMap[themeId]?.title).find(Boolean);
  const signalTitle = (annotation.signal_ids || []).map((signalId) => signalMap[signalId]?.title).find(Boolean);

  if (!themeTitle && !signalTitle) {
    return null;
  }

  return (
    <div className="pt-1 text-[11px] leading-4 text-slate-500">
      {themeTitle ? (
        <p>
          <span className="font-semibold text-slate-600">Theme:</span> {themeTitle}
        </p>
      ) : null}
      {signalTitle ? (
        <p>
          <span className="font-semibold text-slate-600">Signal:</span> {signalTitle}
        </p>
      ) : null}
    </div>
  );
}

function normalizeAcademicLabel(record: Page2Record, index: number) {
  return readString(record.academic_level) || `CLASS ${index + 1}`;
}

function normalizeTestLabel(record: Page2Record, index: number) {
  const testName = readString(record.test_name);
  if (!testName) {
    return `TEST${index + 1}`;
  }
  return testName;
}

function formatAcademicScore(value: unknown, gradingMode: unknown) {
  const score = readString(value);
  if (!score) {
    return undefined;
  }
  return readString(gradingMode)?.toLowerCase() === "percentage" ? `${score}%` : score;
}

function formatScoreWithMax(score: unknown, max: unknown) {
  const scoreValue = readString(score);
  const maxValue = readString(max);
  if (!scoreValue) {
    return "—";
  }
  return maxValue ? `${scoreValue}/${maxValue}` : scoreValue;
}

function formatTestScore(record: Page2Record) {
  return readString(record.total_score) || readString(record.percentile) || readString(record.rank) || "—";
}

function formatDuration(value: unknown) {
  const duration = readString(value);
  if (!duration) {
    return undefined;
  }
  return `${duration} yr${duration === "1" ? "" : "s"}`;
}

function normalizeActivityType(value: unknown) {
  const raw = readString(value);
  if (!raw) {
    return undefined;
  }
  return raw === "co_curricular" ? "Co-curricular" : formatKey(raw);
}

function getSubjectEntries(record: Page2Record) {
  return Array.isArray(record.subject_entries) ? record.subject_entries.filter(isRecord) : [];
}

function getSectionalScores(record: Page2Record) {
  return Array.isArray(record.sectional_scores) ? record.sectional_scores.filter(isRecord) : [];
}

function parsePageOneData(data: unknown): PageOneData | null {
  if (!isRecord(data)) {
    return null;
  }

  const identity = isRecord(data.identity) ? data.identity : null;
  const familyBackground = isRecord(data.family_background) ? data.family_background : null;
  const schoolHistory = Array.isArray(data.schooling_history) ? data.schooling_history.filter(isRecord) : [];

  return {
    applicantName: readString(identity?.full_name),
    dateOfBirth: readString(identity?.date_of_birth),
    intendedCourse: readString(identity?.preferred_major),
    location: formatLocation(identity?.geographic_context),
    familyMembers: familyBackground
      ? [
        buildFamilyMember("Parent / Guardian 1", familyBackground.father),
        buildFamilyMember("Parent / Guardian 2", familyBackground.mother),
      ].filter((member) => hasDisplayValue([member.name, member.education, member.occupation, member.organization, member.role]))
      : [],
    schoolHistory: schoolHistory.map((entry) => ({
      level: readString(entry.level),
      schoolName: readString(entry.school_name),
      boardName: readString(entry.board_name),
      entityId: readString(entry.entity_id),
    })),
  };
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

function renderEssayText(text: string, annotations: FragmentAnnotation[], annotationContext?: ReviewAnnotations | null) {
  if (!text) return null;

  // Stable segmentation: We identify [start, end] ranges for each paragraph
  // to ensure 100% character coverage and stable highlight offsets.
  const createSegments = (rawText: string) => {
    const segs: Array<{ start: number; end: number }> = [];
    
    // Primary split: Existing double newlines
    if (rawText.includes("\n\n")) {
      let last = 0;
      const splitRegex = /\n\s*\n/g;
      let match;
      while ((match = splitRegex.exec(rawText)) !== null) {
        segs.push({ start: last, end: match.index });
        last = match.index + match[0].length;
      }
      if (last < rawText.length) {
        segs.push({ start: last, end: rawText.length });
      }
      return segs;
    }

    // Secondary split: Visual paragraphs every 4 sentences
    const sentenceRegex = /[^.!?]+[.!?]+(?:\s+|$)/g;
    let match;
    let last = 0;
    let count = 0;
    while ((match = sentenceRegex.exec(rawText)) !== null) {
      count++;
      if (count >= 4) {
        const end = match.index + match[0].length;
        segs.push({ start: last, end: end });
        last = end;
        count = 0;
      }
    }
    if (last < rawText.length) {
      segs.push({ start: last, end: rawText.length });
    }
    return segs.length > 0 ? segs : [{ start: 0, end: rawText.length }];
  };

  const segments = createSegments(text);

  return (
    <div className="space-y-6">
      {segments.map((seg, i) => {
        const segText = text.slice(seg.start, seg.end);
        const pAnnotations = annotations.filter(a => a.end_char > seg.start && a.start_char < seg.end);

        if (!pAnnotations.length) {
          return <p key={i} className="mb-6 whitespace-pre-wrap last:mb-0">{segText}</p>;
        }

        const elements: ReactNode[] = [];
        let cursor = 0;

        pAnnotations.forEach((annotation) => {
          const startInP = Math.max(0, annotation.start_char - seg.start);
          const endInP = Math.min(segText.length, annotation.end_char - seg.start);

          if (startInP > cursor) {
            elements.push(<Fragment key={`plain-${cursor}`}>{segText.slice(cursor, startInP)}</Fragment>);
          }
          if (endInP > startInP) {
            elements.push(
              <span
                key={annotation.fragment_id}
                id={buildFragmentAnchorId(annotation.fragment_id)}
                className="group/annotation relative rounded-sm bg-blue-100/60 px-0.5 font-medium underline decoration-blue-500/40 decoration-2 underline-offset-4 transition-colors hover:bg-blue-100"
              >
                <StyledTooltip content={buildAnnotationTitle(annotation, annotationContext)} compact />
                {segText.slice(startInP, endInP)}
              </span>
            );
            cursor = endInP;
          }
        });

        if (cursor < segText.length) {
          elements.push(<Fragment key={`plain-${cursor}`}>{segText.slice(cursor)}</Fragment>);
        }

        return <p key={i} className="mb-6 whitespace-pre-wrap last:mb-0">{elements}</p>;
      })}
    </div>
  );
}

function buildAnnotationTitle(annotation?: EntityAnnotation | FragmentAnnotation, annotationContext?: ReviewAnnotations | null) {
  if (!annotation) {
    return undefined;
  }

  const themeMap = buildThemeMap(annotationContext?.themes || []);
  const signalMap = buildSignalMap(annotationContext?.signals || []);
  const themeTitles = (annotation.theme_ids || [])
    .map((themeId) => themeMap[themeId]?.title)
    .filter(Boolean) as string[];
  const resolvedSignals = (annotation.signal_ids || [])
    .map((signalId) => signalMap[signalId])
    .filter(Boolean) as SignalRecord[];
  const signalTitles = resolvedSignals.map((signal) => signal.title).filter(Boolean) as string[];
  return [
    themeTitles.length ? `Relevant to: ${themeTitles.join(", ")}` : "",
    signalTitles.length ? `Signal: ${signalTitles.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n") || undefined;
}

function buildAnnotationBadge(annotation?: EntityAnnotation | FragmentAnnotation, annotationContext?: ReviewAnnotations | null) {
  if (!annotation) {
    return "Referenced in the synthesized report.";
  }

  const themeMap = buildThemeMap(annotationContext?.themes || []);
  const signalMap = buildSignalMap(annotationContext?.signals || []);
  const themeTitle = (annotation.theme_ids || []).map((themeId) => themeMap[themeId]?.title).find(Boolean);
  const signalTitle = (annotation.signal_ids || []).map((signalId) => signalMap[signalId]?.title).find(Boolean);

  if (themeTitle && signalTitle) {
    return `${themeTitle} · ${signalTitle}`;
  }
  if (themeTitle) {
    return themeTitle;
  }
  if (signalTitle) {
    return signalTitle;
  }
  return "Referenced in synthesis";
}

function buildThemeMap(themes: ThemeRecord[]) {
  return Object.fromEntries(
    themes
      .filter((theme) => theme.theme_id)
      .map((theme) => [theme.theme_id as string, theme]),
  ) as Record<string, ThemeRecord>;
}

function buildSignalMap(signals: SignalRecord[]) {
  return Object.fromEntries(
    signals
      .filter((signal) => signal.signal_id)
      .map((signal) => [signal.signal_id as string, signal]),
  ) as Record<string, SignalRecord>;
}

function StyledTooltip({ content, compact = false }: { content?: string; compact?: boolean }) {
  if (!content) {
    return null;
  }

  const lines = content
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  return (
    <span
      className={`pointer-events-none absolute left-1/2 top-0 z-30 w-max max-w-[16rem] -translate-x-1/2 -translate-y-[calc(100%+0.45rem)] rounded-[0.7rem] border border-slate-300/80 bg-[#fffdf8] px-2.5 py-2 text-left shadow-[0_4px_10px_rgba(15,23,42,0.06)] opacity-0 transition-opacity duration-100 group-hover/annotation:opacity-100 group-focus-within/annotation:opacity-100 ${
        compact ? "max-w-[12rem]" : ""
      }`}
      role="tooltip"
    >
      <span className="relative block space-y-0.5">
        {lines.map((line, index) => (
          <span
            key={`${line}-${index}`}
            className={`block ${index === 0 ? "text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500" : "text-[11px] font-medium leading-4 text-slate-900"}`}
          >
            {line}
          </span>
        ))}
      </span>
    </span>
  );
}

function derivePageTwoTitle(item: Page2Record, label: string) {
  const candidates = [item.academic_level, item.test_name, item.activity_name, item.position_title];
  const title = candidates.find((candidate) => typeof candidate === "string" && candidate.trim().length > 0);
  return typeof title === "string" ? title : label.slice(0, -1);
}

function renderValue(value: unknown): React.ReactNode {
  if (value == null) {
    return <span className="text-[color:var(--muted)]">—</span>;
  }
  if (Array.isArray(value)) {
    if (!value.length) {
      return <span className="text-[color:var(--muted)]">—</span>;
    }
    return (
      <div className="space-y-1">
        {value.map((item, index) => (
          <div key={index} className="rounded-xl bg-slate-50/90 px-3 py-2">
            {isRecord(item) ? JSON.stringify(item) : String(item)}
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === "object") {
    return (
      <pre className="overflow-x-auto rounded-xl bg-slate-50/90 px-3 py-3 text-xs">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }
  return String(value);
}

function formatKey(value: string) {
  return value.replace(/_/g, " ");
}

function buildFamilyMember(label: string, value: unknown) {
  const member = isRecord(value) ? value : {};
  return {
    label,
    name: readString(member.name),
    education: readString(member.education),
    occupation: readString(member.field_of_employment),
    organization: readString(member.organization),
    role: readString(member.designation),
  };
}

function formatLocation(value: unknown) {
  if (!isRecord(value)) {
    return undefined;
  }

  const parts = [readString(value.city), readString(value.state), readString(value.country)].filter(Boolean);
  return parts.length ? parts.join(", ") : undefined;
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function readString(value: unknown) {
  return typeof value === "string" && value.trim() ? value : undefined;
}

function hasDisplayValue(values: Array<string | undefined>) {
  return values.some(Boolean);
}

function InfoRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="space-y-1">
      <dt className="text-[11px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">{label}</dt>
      <dd className="text-sm leading-6 text-[color:var(--ink)]">{value || "Unavailable"}</dd>
    </div>
  );
}

function CompactMetric({ label, value }: { label: string; value?: string }) {
  if (!value) {
    return null;
  }

  return (
    <div className="min-w-[8.5rem] rounded-[1rem] border border-slate-200 bg-white/82 px-3 py-2 shadow-[0_14px_26px_rgba(15,23,42,0.06)]">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">{label}</p>
      <p className="mt-1 text-sm font-semibold text-[color:var(--ink)]">{value}</p>
    </div>
  );
}

function PageTwoPanel({
  anchorId,
  title,
  description,
  tabs,
  activeIndex,
  onSelect,
  highlighted,
  annotationTitle,
  children,
}: {
  anchorId?: string;
  title: string;
  description: string;
  tabs: Array<{ key: string; label: string; anchorId?: string; highlighted?: boolean; title?: string }>;
  activeIndex: number;
  onSelect: (index: number) => void;
  highlighted?: boolean;
  annotationTitle?: string;
  children: ReactNode;
}) {
  return (
    <section
      id={anchorId}
      className={`isolate relative overflow-hidden rounded-[1.5rem] border bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(248,250,252,0.9))] shadow-[0_18px_36px_rgba(15,23,42,0.08)] transition-colors ${
        highlighted
          ? "border-blue-200 shadow-[0_18px_32px_rgba(59,130,246,0.12)]"
          : "border-slate-200"
        }`}
    >
      {tabs.length ? (
        <div className="relative z-0 overflow-x-auto border-b border-slate-200 bg-[linear-gradient(180deg,rgba(248,250,252,0.96),rgba(255,255,255,0.82))] px-4 pt-3">
          <div className="flex min-w-max items-end gap-2">
            {tabs.map((tab, index) => {
              const active = index === activeIndex;

              return (
                <button
                  key={tab.key}
                  id={tab.anchorId}
                  type="button"
                  onPointerDown={(event) => {
                    event.preventDefault();
                    onSelect(index);
                  }}
                  onClick={() => onSelect(index)}
                  className={`relative touch-manipulation rounded-t-[1rem] border px-4 py-2.5 text-left transition-all focus:outline-none ${active
                      ? "z-10 border-slate-200 border-b-white bg-white text-[color:var(--ink)] shadow-[0_-4px_14px_rgba(15,23,42,0.08)]"
                      : "z-0 border-transparent bg-white/45 text-[color:var(--muted)] hover:bg-white/75"
                    }`}
                  aria-pressed={active}
                >
                  <span className="text-sm font-semibold tracking-tight">{tab.label}</span>
                  {tab.highlighted ? (
                    <span className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-blue-400 ring-2 ring-white/80" />
                  ) : null}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="space-y-4 p-5">
        <div className="space-y-1">
          <h3 className="text-lg font-semibold tracking-tight text-[color:var(--brand-deep)]">{title}</h3>
          <p className="text-sm leading-6 text-[color:var(--muted)]">{description}</p>
        </div>
        {children}
      </div>
    </section>
  );
}

function ApplicantProvidedLabel({ label }: { label: string }) {
  return (
    <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
      {label} · Applicant-provided
    </p>
  );
}

function buildEntityAnchorId(entityId: string) {
  return `report-entity-${entityId.toLowerCase()}`;
}

function buildFragmentAnchorId(fragmentId: string) {
  return `report-fragment-${fragmentId.toLowerCase()}`;
}

function UserProvidedText({
  value,
  label,
  className,
}: {
  value: string;
  label?: string;
  className?: string;
}) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[color:var(--muted)]">
        {label ? `${label} · Applicant-provided` : "Applicant-provided"}
      </p>
      <p className={className}>{`"${value}"`}</p>
    </div>
  );
}

function EmptyStateCopy({ text }: { text: string }) {
  return (
    <div className="rounded-[1.2rem] border border-dashed border-slate-300 bg-white/70 px-4 py-5 text-sm leading-6 text-[color:var(--muted)]">
      {text}
    </div>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
