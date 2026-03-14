# `ROS_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. Purpose of This Document

This document defines the complete Report Output Specification (ROS v1) — the sole output artifact of the AG_InterviewStandardiser system.

It specifies:

- The top-level structure of the ROS v1 artifact
- The complete schema for all five pages
- The canonical source for every field in Pages 1–3
- The production rules for every page
- The provenance model for Pages 4–5
- Projection rules — what is permitted and prohibited during ROS construction

This document does not define:

- How the canonical representation is constructed (governed by `canonical_model_philosophy_v1.7.md`)
- How canonical projections are built for LLM reasoning (governed by `canonical_projection_spec_v1.7.md`)
- LLM call contracts (governed by `llm_synthesis_contract_v1.7.md`)
- Agent responsibilities (governed by `agent_pipeline_spec_v1.7.md`)
- Database storage of the artifact (governed by `database_schema_v1.7.md`)

### Naming Clarification

The document is named `ROS_v1.7.md` because it is the Stage 1.7 specification document. The artifact it describes remains **ROS v1**. The `report_version` field inside every generated report is `"ROS_v1"`. No consumer of the output artifact sees any version change. Document version tracks the stage; artifact version tracks the schema.

---

## 2. Key Definitions

**Canonical Representation** — The authoritative, structured output of Agents 1–11. The source of truth for all applicant data. Stored in `canonical_records`. Never modified by any downstream component.

**Entity ID** — A stable formatted identifier assigned to each canonical entry by the ROS projector. Format: `PREFIX-###`. The LLM references canonical entries using entity IDs.

**Deterministic Projection** — The process by which the ROS Projector maps canonical data to ROS Pages 1–3 without LLM involvement.

**Signal-Guided Synthesis** — The two-stage process by which LLM Call 1 (signal interpretation) and LLM Call 2 (interview generation) produce ROS Pages 4–5, guided by deterministic signals derived from canonical data.

**Null Preservation Rule** — If a canonical field is null or absent, the corresponding ROS field must be null. No heuristic reconstruction or default substitution is permitted.

---

## 3. Top-Level Structure

The ROS v1 artifact is a single JSON document with six top-level keys:

```json
{
  "report_metadata": { ... },
  "page_1_background_profile": { ... },
  "page_2_academic_and_engagement": { ... },
  "page_3_essays": { ... },
  "page_4_focus_themes": { ... },
  "page_5_question_groups": { ... }
}
```

All six keys are required. No key may be absent. No additional top-level keys may be introduced.

### Page Source Summary

| Page | Key | Source | Type |
|---|---|---|---|
| Metadata | `report_metadata` | System-generated | Deterministic |
| Page 1 | `page_1_background_profile` | Canonical projection | Deterministic |
| Page 2 | `page_2_academic_and_engagement` | Canonical projection | Deterministic |
| Page 3 | `page_3_essays` | Canonical projection | Deterministic |
| Page 4 | `page_4_focus_themes` | LLM Call 2 (validated) | Signal-guided synthesis |
| Page 5 | `page_5_question_groups` | LLM Call 2 (validated) | Signal-guided synthesis |

Pages 1–3 and Pages 4–5 are produced through entirely separate pipeline paths and merged only at the ROS Assembly step.

---

## 4. Entity ID Prefix Reference

The following prefixes are used throughout this document. All entity IDs are assigned by the ROS Projector before projection construction and before LLM stages begin.

| Canonical Collection | Prefix | Example |
|---|---|---|
| `academic_entries[]` | `ACA` | `ACA-001`, `ACA-002` |
| `test_entries[]` | `TST` | `TST-001`, `TST-002` |
| `essay_entries[]` | `ESS` | `ESS-001`, `ESS-002` |
| `activity_entries[]` | `ACT` | `ACT-001`, `ACT-006` |
| `schooling_history[]` | `SCH` | `SCH-001`, `SCH-002` |

All activity entries — extracurricular, co-curricular, and leadership — share the `ACT` prefix. Activity type determines which ROS section an entry appears in, not its entity ID prefix.

---

## 5. `report_metadata`

System-generated metadata. Not derived from LLM output.

```json
{
  "report_metadata": {
    "application_id": "string",
    "generated_at": "ISO-8601 timestamp",
    "canonical_version": "string",
    "report_version": "ROS_v1"
  }
}
```

**Field rules:**

| Field | Source | Rule |
|---|---|---|
| `application_id` | `canonical.identifiers.application_id` | Always present |
| `generated_at` | System clock at ROS assembly time | ISO-8601 format with timezone |
| `canonical_version` | `canonical.canonical_version` | Must match the canonical record version |
| `report_version` | Hardcoded | Always `"ROS_v1"` — this value does not change in Stage 1.7 |

---

## 6. Page 1 — Background Profile

### 6.1 Full Schema

```json
{
  "page_1_background_profile": {
    "identity": {
      "application_id": "string",
      "full_name": "string | null",
      "date_of_birth": "string | null",
      "preferred_major": "string | null"
    },
    "family_background": {
      "father": {
        "name": "string | null",
        "education": "string | null",
        "field_of_employment": "string | null",
        "organization": "string | null",
        "designation": "string | null"
      },
      "mother": {
        "name": "string | null",
        "education": "string | null",
        "field_of_employment": "string | null",
        "organization": "string | null",
        "designation": "string | null"
      }
    },
    "schooling_history": [
      {
        "entity_id": "SCH-###",
        "level": "string | null",
        "school_name": "string | null",
        "board_name": "string | null",
        "location": "string | null"
      }
    ]
  }
}
```

### 6.2 Canonical Source Mapping

| ROS Field | Canonical Source |
|---|---|
| `identity.application_id` | `identifiers.application_id` |
| `identity.full_name` | `identifiers.full_name` |
| `identity.date_of_birth` | `identifiers.date_of_birth` |
| `identity.preferred_major` | `identifiers.preferred_major` |
| `family_background.father.*` | `identifiers.family_background.father.*` |
| `family_background.mother.*` | `identifiers.family_background.mother.*` |
| `schooling_history[].entity_id` | Assigned by ROS Projector (`SCH-###`) |
| `schooling_history[].level` | `schooling_history[].level` |
| `schooling_history[].school_name` | `schooling_history[].school_name` |
| `schooling_history[].board_name` | `schooling_history[].board_name` |
| `schooling_history[].location` | `schooling_history[].location` |

### 6.3 Projection Rules

- Null canonical fields map to null ROS fields — no substitution
- If all father fields are null, the `father` object is included with all null values — it is not omitted
- Same for mother
- `schooling_history` entries are included in canonical array order
- No sorting, no deduplication, no merging of entries
- The following fields are explicitly not present in Page 1 because they do not exist in canonical: `gender`, `nationality`, `city`, `state`, `country`, `blood_group`, `domicile`, `category`, `financial_aid`

---

## 7. Page 2 — Academic and Engagement Profile

### 7.1 Full Schema

```json
{
  "page_2_academic_and_engagement": {
    "academic_records": [
      {
        "entity_id": "ACA-###",
        "level": "string",
        "school_name": "string | null",
        "board": "string | null",
        "year": "string | null",
        "grading_mode": "string",
        "overall_score": "string | null",
        "predicted_score": "string | null",
        "subjects": [
          {
            "subject": "string",
            "score": "string | null",
            "predicted_score": "string | null"
          }
        ]
      }
    ],
    "standardized_tests": [
      {
        "entity_id": "TST-###",
        "name": "string",
        "overall_score": "string | null",
        "percentile": "string | null",
        "rank": "string | null",
        "sections": [
          {
            "label": "string",
            "score": "string | null"
          }
        ]
      }
    ],
    "extracurricular_activities": [
      {
        "entity_id": "ACT-###",
        "name": "string | null",
        "position": "string | null",
        "level": "string | null",
        "duration_years": "string | null"
      }
    ],
    "co_curricular_activities": [
      {
        "entity_id": "ACT-###",
        "name": "string | null",
        "position": "string | null",
        "level": "string | null",
        "duration_years": "string | null"
      }
    ],
    "leadership_roles": [
      {
        "entity_id": "ACT-###",
        "position": "string | null",
        "level": "string | null",
        "duration_years": "string | null"
      }
    ]
  }
}
```

### 7.2 Academic Records — Canonical Source Mapping

| ROS Field | Canonical Source |
|---|---|
| `entity_id` | Assigned by ROS Projector (`ACA-###`) |
| `level` | `academic_entries[].academic_level` |
| `school_name` | `academic_entries[].school_name` |
| `board` | `academic_entries[].board_name` |
| `year` | `academic_entries[].academic_year` |
| `grading_mode` | `academic_entries[].grading_mode` |
| `overall_score` | `academic_entries[].score_raw` |
| `predicted_score` | `academic_entries[].predicted_score_raw` |
| `subjects[].subject` | `academic_entries[].subject_entries[].subject_name` |
| `subjects[].score` | `academic_entries[].subject_entries[].score_raw` |
| `subjects[].predicted_score` | `academic_entries[].subject_entries[].predicted_score_raw` |

`predicted_score` at both record and subject level is included only if non-null in canonical. If null, it is omitted from the ROS entry entirely.

### 7.3 Standardized Tests — Canonical Source Mapping

| ROS Field | Canonical Source |
|---|---|
| `entity_id` | Assigned by ROS Projector (`TST-###`) |
| `name` | `test_entries[].test_name` |
| `overall_score` | `test_entries[].total_score` |
| `percentile` | `test_entries[].percentile` |
| `rank` | `test_entries[].rank` |
| `sections[].label` | `test_entries[].sectional_scores[].label` |
| `sections[].score` | `test_entries[].sectional_scores[].raw_score` |

All test entries from canonical appear in a single `standardized_tests[]` array. There is no split between primary and additional tests — canonical has one `test_entries[]` collection and the ROS reflects that exactly. `TST-###` entity IDs are used for all entries.

Section breakdowns use the generic `label`/`score` structure — the same labels as stored in canonical (e.g. `"Maths Percentile"`, `"Chemistry Percentile"`) are preserved verbatim. No hardcoded subject-specific field names are introduced.

### 7.4 Activity Classification Rule

Activity entries from canonical are routed to ROS sections based strictly on their `activity_type` value assigned by Agent 7. The projection must not reclassify activities.

| Canonical `activity_type` | ROS Section |
|---|---|
| `"extracurricular"` | `extracurricular_activities[]` |
| `"co_curricular"` | `co_curricular_activities[]` |
| `"leadership"` | `leadership_roles[]` |
| `"other"` | `extracurricular_activities[]` |

All activity entries carry their `ACT-###` entity ID regardless of which section they appear in.

### 7.5 Activity Fields — Canonical Source Mapping

**Extracurricular and co-curricular entries:**

| ROS Field | Canonical Source |
|---|---|
| `entity_id` | Assigned by ROS Projector (`ACT-###`) |
| `name` | `activity_entries[].activity_name` |
| `position` | `activity_entries[].position_title` |
| `level` | `activity_entries[].level` |
| `duration_years` | `activity_entries[].duration` (numeric strings only) |

**Leadership entries:**

| ROS Field | Canonical Source |
|---|---|
| `entity_id` | Assigned by ROS Projector (`ACT-###`) |
| `position` | `activity_entries[].position_title` |
| `level` | `activity_entries[].level` |
| `duration_years` | `activity_entries[].duration` (numeric strings only) |

Leadership entries use `position` as the primary field because leadership entries typically have a `position_title` but may have a null `activity_name`.

### 7.6 Activity Projection Rules

- `duration_years` is included only if the canonical `duration` field is a numeric string (e.g. `"4"`, `"7"`). Non-numeric strings such as `"Mobile Number"` are parse artifacts and must be omitted
- Null fields are omitted from individual activity entries
- A sparse activity entry with no substantive content after null omission and artifact removal is excluded from the ROS entirely
- Entries are presented in canonical array order within each activity type section
- Parse artifact detection applies the following rules to activity fields:
  - **`duration_years`**: included only if the canonical `duration` value is a numeric string (e.g. `"4"`, `"10"`). Any non-numeric string (e.g. `"Mobile Number"`) is a parse artifact and is omitted.
  - **`roles_and_responsibilities`** and **`activity_name`**: excluded if the value contains a question mark, matches a known form label pattern (e.g. `"Mobile Number"`, `"Email Address"`, `"Date of Birth"`), or is a single generic word from the following blocklist: `["Organization", "Reference", "Position", "Role", "Title", "Name", "Duration", "Level"]`.
  - **`position_title`**: excluded only if it matches a known form label pattern. The generic word blocklist does not apply to `position_title` — legitimate position titles such as `"School Prefect"` or `"Captain"` may be single common words.

---

## 8. Page 3 — Essays

### 8.1 Full Schema

```json
{
  "page_3_essays": {
    "essays": [
      {
        "entity_id": "ESS-###",
        "prompt": "string | null",
        "full_text": "string | null",
        "word_count": "number | null",
        "highlights": [
          {
            "start_char": "number",
            "end_char": "number",
            "referenced_entity_ids": ["string"]
          }
        ]
      }
    ]
  }
}
```

### 8.2 Canonical Source Mapping

| ROS Field | Canonical Source |
|---|---|
| `entity_id` | Assigned by ROS Projector (`ESS-###`) |
| `prompt` | `essay_entries[].essay_identifier` |
| `full_text` | `essay_entries[].raw_text` |
| `word_count` | `essay_entries[].word_count` |
| `highlights` | Computed deterministically by the ROS Projector |

### 8.3 Essay Projection Rules

- An essay entry is included only if `placeholder_flag` is `false` and `raw_text` is non-null and non-empty
- An essay entry with `placeholder_flag: true` is excluded from Page 3 entirely
- Essay text is included verbatim — no summarization, no paraphrasing, no modification
- `word_count` is included as computed by Agent 6

### 8.4 Highlights

Highlights are character-span annotations computed deterministically by the ROS Projector. They identify portions of essay text that reference canonical entities.

- `start_char` and `end_char` are zero-indexed character positions within `full_text`
- `referenced_entity_ids` lists the entity IDs of canonical entries the highlighted span references
- All entity IDs in highlights must exist in the entity ID map
- Highlights contain no evaluative commentary
- No LLM is involved in highlight generation
- If no highlights are detected for an essay, `highlights` is an empty array

---

## 9. Page 4 — Focus Themes

### 9.1 Provenance

Page 4 is produced by LLM Call 2 (Agent 16) and validated by the Policy Guard before inclusion in the ROS artifact. In Stage 1.7, Page 4 is the product of signal-guided synthesis: LLM Call 2 receives a validated signal-evidence bundle — not the raw canonical projection — and derives themes from interpreted signals that are themselves grounded in deterministic observations from canonical data. This provides a traceable chain from canonical evidence to interview guidance.

This provenance note is informational. It does not change the Page 4 schema.

### 9.2 Full Schema

```json
{
  "page_4_focus_themes": {
    "themes": [
      {
        "theme_id": "THEME-###",
        "title": "string",
        "description": "string",
        "referenced_entity_ids": ["string"]
      }
    ]
  }
}
```

### 9.3 Field Rules

| Field | Rule |
|---|---|
| `theme_id` | Format `THEME-###`. Numbered sequentially. Unique within the themes array. |
| `title` | Neutral, concise theme label. No evaluative language. No prohibited terms. |
| `description` | Brief neutral description of what the theme covers. No evaluative language. No new facts. |
| `referenced_entity_ids` | Must contain only entity IDs present in the entity ID map for this application. No invented IDs. At least one per theme. |

### 9.4 Production Rules

- Page 4 is populated directly from validated LLM Call 2 output — no reformatting, no renaming, no restructuring by the ROS Assembly step
- Every `referenced_entity_id` has been validated by the Policy Guard against the entity ID map before the ROS is assembled
- No evaluative language is present — validated by the Policy Guard before the ROS is assembled
- If LLM Call 2 validation fails, Page 4 is not produced and no ROS artifact is assembled

---

## 10. Page 5 — Question Groups

### 10.1 Provenance

Page 5 is produced by LLM Call 2 (Agent 16) in the same call that produces Page 4. The same signal-guided provenance applies. Question groups are linked to the themes in Page 4 via `theme_id`.

### 10.2 Full Schema

```json
{
  "page_5_question_groups": {
    "question_groups": [
      {
        "theme_id": "THEME-###",
        "group_title": "string",
        "questions": ["string"]
      }
    ]
  }
}
```

### 10.3 Field Rules

| Field | Rule |
|---|---|
| `theme_id` | Must reference a `theme_id` defined in `page_4_focus_themes.themes`. No invented theme IDs. |
| `group_title` | Neutral label for the question group. No evaluative language. |
| `questions` | Non-empty array of open-ended, exploratory question strings. |

### 10.4 Production Rules

- Page 5 is populated directly from validated LLM Call 2 output — no reformatting or restructuring
- Every `theme_id` in Page 5 has been validated against the themes defined in Page 4 before the ROS is assembled
- No evaluative language is present — validated by the Policy Guard
- Questions must be exploratory — they invite the applicant to describe, explain, or reflect. They do not demand justification of grades, imply deficiency, or use comparative language
- If LLM Call 2 validation fails, Page 5 is not produced and no ROS artifact is assembled

---

## 11. Global Projection Rules

The following rules apply to the ROS artifact as a whole.

### 11.1 What the ROS Projection Must Not Do

- Modify any canonical field value
- Collapse or merge canonical collection entries
- Rewrite, paraphrase, or summarize canonical text
- Introduce fields not sourced from canonical or from LLM Call 2 output
- Infer missing values from context
- Reconstruct null fields heuristically
- Reclassify activity types
- Sort or reorder canonical collections
- Produce a partial ROS artifact if any pipeline stage has failed

### 11.2 What the ROS Does Not Contain

The following are explicitly absent from the ROS v1 artifact. Their absence is intentional.

| Absent Element | Reason |
|---|---|
| Applicant scores, rankings, or evaluations | System is non-evaluative |
| Admissions commentary | Out of scope |
| Comparative language | Non-evaluative constraint |
| Predictions or likelihood statements | Out of scope |
| Chain-of-thought or intermediate reasoning | Not stored in output |
| Deterministic signal collection | Pipeline-internal; not an output artifact |
| Interpreted signal collection | Pipeline-internal; not in ROS (optionally in `synthesis_output` per signal storage decision) |
| Gender, nationality, city, state, country | Not present in canonical identifiers |
| Normalized GPA equivalents | Not produced by the system |
| LLM commentary on essays | Page 3 is deterministic only |

### 11.3 Null Handling

If a canonical field is null, the corresponding ROS field is null. The ROS does not substitute default values, placeholder strings, or computed approximations for null canonical fields.

Exception: fields that are computed at ROS assembly time (e.g. `generated_at`, `entity_id` assignments) are always populated regardless of canonical content.

---

## 12. ROS Assembly

The ROS v1 artifact is assembled by the ROS Assembly Step (`app/ros/assembler.py`) after all pipeline stages complete successfully.

Assembly merges:
- `report_metadata` — system-generated at assembly time
- `page_1_background_profile`, `page_2_academic_and_engagement`, `page_3_essays` — from the deterministic ROS projection (produced before the signal pipeline begins)
- `page_4_focus_themes`, `page_5_question_groups` — from validated LLM Call 2 output

The ROS Assembly Step does not transform, reformat, or reinterpret any page content. It places each page into the top-level structure as-is.

Assembly only occurs when all of the following are true:
- All deterministic pages (1–3) were produced without error
- LLM Call 1 completed and passed signal validation
- LLM Call 2 completed and passed output validation

If any condition is not met, no ROS artifact is assembled and no partial artifact is persisted.

---

## 13. Invariant Check

| Invariant | Status |
|---|---|
| Five-page structure — all pages present in every assembled ROS | ✅ |
| `report_version` is always `"ROS_v1"` | ✅ |
| Pages 1–3 are deterministic — no LLM involvement | ✅ |
| Pages 4–5 are produced by LLM Call 2 only — validated before inclusion | ✅ |
| All entity IDs in Pages 4–5 validated against entity ID map | ✅ |
| No evaluative language in any page — validated by Policy Guard | ✅ |
| `TST-###` prefix for all test entries | ✅ |
| `ACT-###` prefix for all activity entries including leadership | ✅ |
| No hardcoded subject-specific breakdown fields — generic `sections[]` | ✅ |
| `field_of_employment` and `designation` used (not `occupation`) | ✅ |
| No fields sourced from outside canonical or LLM Call 2 output | ✅ |
| No partial ROS produced on pipeline failure | ✅ |
| Null canonical fields → null ROS fields, no substitution | ✅ |
| Activity classification not overridden by projection | ✅ |

---

*Report Output Specification Version: 1.7 | Artifact Version: ROS v1 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*