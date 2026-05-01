# `canonical_model_philosophy_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. Purpose of This Document

This document defines the philosophical rules, structural invariants, and governing principles of the canonical representation in the AG_InterviewStandardiser system.

It defines:

- The core principle of what the canonical representation is
- Collection-based storage rules and why they exist
- The prohibition on fixed academic and test keys
- Separation of concerns within the canonical structure
- Versioning rules and the current version definition
- The complete structural inventory of canonical v1.1
- Extensibility and backward compatibility rules
- The entity ID philosophy — how canonical entry IDs and projection entity IDs coexist
- The canonical vs ROS distinction
- Projection governance — how canonical data is consumed by the projection layer without modification
- Non-evaluative enforcement

This document does not define:

- Database schema or table structure (governed by `database_schema_v1.7.md`)
- Projection field inclusion and exclusion rules (governed by `canonical_projection_spec_v1.7.md`)
- LLM call contracts (governed by `llm_synthesis_contract_v1.7.md`)
- ROS output page structure (governed by `ROS_v1.7.md`)
- API response formats
- Docker configuration or infrastructure

---

## 2. Core Principle — Canonical Is Internal Structural Truth

The canonical representation is the authoritative, structured form of all extracted applicant data. It is the single source of truth for everything the system knows about an applicant's application.

The canonical representation is:

- **Deterministically constructed** — produced entirely by Agents 1–11 without LLM involvement
- **Collection-based** — all repeating data stored as arrays, never as fixed keys
- **Non-evaluative** — contains extracted facts only, no assessments, rankings, or inferences
- **Presentation-agnostic** — structured for storage correctness, not for any output format
- **Versioned** — carries an explicit `canonical_version` field
- **Immutable downstream** — no component after Agent 11 modifies it
- **Stored as JSONB** — persisted in the `canonical_records` table

The canonical representation is not a report. It is not a UI contract. It is not modified to satisfy layout concerns or LLM token efficiency. It is not reshaped to match ROS page groupings. It is not restructured to make projection easier.

The ROS v1 artifact is derived from canonical. Canonical is never reshaped to match ROS grouping.

Canonical projections are read-only views derived from canonical for specific LLM reasoning tasks. They do not modify canonical. Canonical remains unchanged before and after projection construction.

---

## 3. Collection-Based Storage

All repeating structures in the canonical representation must be stored as collections — ordered arrays of entry objects. No collection may be collapsed into fixed named keys.

**Canonical collections:**

- `academic_entries[]`
- `schooling_history[]`
- `test_entries[]`
- `essay_entries[]`
- `activity_entries[]`
- `timeline_entries[]`

**Prohibited equivalents — these must never appear as canonical keys:**

| Prohibited Pattern | Correct Approach |
|---|---|
| `class_10`, `class_12`, `grade_11` | Entry in `academic_entries[]` with `academic_level` field |
| `undergraduate_year_1` | Entry in `academic_entries[]` |
| `sat_score`, `jee_percentile`, `act_score` | Entry in `test_entries[]` with `test_name` field |
| `career_essay`, `community_essay` | Entry in `essay_entries[]` with `essay_identifier` field |
| `extracurricular_1`, `leadership_role` | Entry in `activity_entries[]` with `activity_type` field |

**Why this rule exists:**

Fixed keys encode assumptions about educational systems, regional academic structures, and application formats. An applicant from a different country, board system, or schooling structure would break a fixed-key schema. Collection-based storage prevents schema rigidity, regional academic bias, and hardcoded institutional assumptions. It ensures the system can process applications from any educational background without modification.

This rule is absolute. It cannot be relaxed for any reason within Stage 1.7 or any future stage.

---

## 4. No Fixed Academic Keys Rule

Canonical must not include top-level or nested keys that encode specific academic levels, test names, or essay categories. This rule is restated explicitly because the violation pattern is subtle — it can appear as a "convenience" field that seems harmless.

**Prohibited key patterns anywhere in canonical JSONB:**

```
class_10, class_12, grade_9, grade_11, year_12
undergraduate_year_1, undergraduate_year_2
sat_score, jee_percentile, jee_advanced_rank
act_composite, gre_verbal, gmat_total
career_statement, community_essay, challenge_essay
```

**Correct representation:**

```json
{
  "entry_id": "UUID",
  "academic_level": "10TH",
  "board_name": "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS (ICSE)",
  "academic_year": "2023",
  "score_raw": "99"
}
```

The `academic_level` field is a string value inside a collection entry, not a key. This is the only permissible pattern.

---

## 5. Separation of Concerns

The canonical representation separates all extracted data into four distinct categories. Each category has a defined purpose and must not be merged with another.

| Category | Key | Purpose |
|---|---|---|
| Identity and background | `identifiers` | Applicant personal identifiers and family context |
| Extracted collections | `academic_entries[]`, `schooling_history[]`, `test_entries[]`, `essay_entries[]`, `activity_entries[]`, `timeline_entries[]` | All factual application data |
| Structural quality | `integrity_report` | Anomaly detection output from Agent 10 |
| Extraction metadata | `extraction_confidence` | Per-agent confidence scores and aggregate |

**Canonical must not contain:**

- ROS page groupings or page numbers
- Theme groupings or theme IDs
- Question groupings or question content
- UI ordering directives
- LLM-generated content of any kind
- Signal data (deterministic or interpreted)
- Entity IDs (projection-layer metadata — see Section 10)

Projection occurs after canonical assembly. It is a separate layer. Canonical does not embed projection outputs.

---

## 6. Versioning Rules

### 6.1 Version Field

Every canonical representation carries an explicit version field as the first key:

```json
"canonical_version": "1.1"
```

### 6.2 Version Format

```
major.minor
```

A major version increment indicates a structural change that may break backward compatibility. A minor version increment indicates an additive change that preserves backward compatibility.

### 6.3 Current Version

The canonical representation is at **version 1.1** as of Stage 1.7. Stage 1.7 does not introduce a new canonical version. The canonical schema is frozen at v1.1 for this stage.

### 6.4 What v1.1 Introduced

Canonical v1.1 introduced the following additions over v1.0:

- Structured `family_background` block under `identifiers`
- New `schooling_history[]` collection
- Explicit `activity_type` classification on every activity entry

These additions were additive. No existing field semantics were changed. No fields were renamed or removed.

### 6.5 Version Independence

ROS versioning is independent from canonical versioning. A change to the ROS output format does not require a canonical version bump. A change to canonical structure does not require a ROS version change. The two versioning systems are maintained separately.

### 6.6 Future Version Rules

Any future canonical version must:

- Increment the version string following the `major.minor` format
- Be additive if a minor increment (no field removal, no destructive renaming)
- Preserve all existing field meanings
- Not require retroactive modification of stored canonical records
- Not require a database schema migration (JSONB storage absorbs additive changes)

---

## 7. Canonical v1.1 — Complete Structural Definition

This section defines the complete structure of a canonical v1.1 document. Every field is defined here. This is the authoritative structural reference for Stage 1.7.

### 7.1 Top-Level Structure

```json
{
  "canonical_version": "1.1",
  "identifiers": {},
  "academic_entries": [],
  "schooling_history": [],
  "test_entries": [],
  "essay_entries": [],
  "activity_entries": [],
  "timeline_entries": [],
  "cross_references": {},
  "integrity_report": {},
  "extraction_confidence": {}
}
```

All keys are required. Empty collections are represented as empty arrays `[]`. Empty objects are represented as `{}`.

---

### 7.2 `identifiers`

Contains applicant identity and background metadata.

```json
{
  "application_id": "string",
  "full_name": "string | null",
  "date_of_birth": "string | null",
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
  "preferred_major": "string | null"
}
```

Field rules:

- `application_id`: Internal pipeline identifier. Always present.
- `full_name`: Extracted applicant name. Null if not found.
- `date_of_birth`: ISO 8601 date string where possible. Raw string otherwise. Null if not found.
- `family_background`: Always present as an object. Parent objects always present. Individual fields null if not found in source PDF.
- `preferred_major`: Extracted intended field of study. Null if not found.

---

### 7.3 `academic_entries[]`

One entry per distinct academic record found in the application.

```json
{
  "entry_id": "UUID",
  "academic_level": "string",
  "school_name": "string | null",
  "board_name": "string | null",
  "academic_year": "string | null",
  "marking_scheme_raw": "string | null",
  "grading_mode": "string",
  "score_raw": "string | null",
  "predicted_score_raw": "string | null",
  "subject_entries": [
    {
      "subject_name": "string",
      "score_raw": "string | null",
      "predicted_score_raw": "string | null"
    }
  ],
  "confidence_score": "number"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 4. Unique per entry. Stable within a pipeline run.
- `academic_level`: Raw level string as found in PDF (e.g. `"9TH"`, `"10TH"`, `"12TH"`).
- `grading_mode`: Normalized mode indicator (e.g. `"percentage"`, `"grade"`).
- `score_raw`: Overall score as a raw string. Not converted or normalized.
- `predicted_score_raw`: Present only if a predicted score was recorded. Null otherwise.
- `subject_entries`: Array of subject-level entries. May be empty.
- `confidence_score`: Extraction confidence assigned by Agent 4. Range 0–1.

---

### 7.4 `schooling_history[]`

One entry per distinct schooling record. Represents institutional affiliation separately from academic performance.

```json
{
  "entry_id": "UUID",
  "level": "string",
  "school_name": "string | null",
  "board_name": "string | null",
  "location": "string | null",
  "confidence_score": "number"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 4.
- `level`: Grade or schooling level string.
- `location`: School location if available. Null if not found.
- `confidence_score`: Extraction confidence.

This collection is distinct from `academic_entries[]`. It records where the applicant studied, not how they performed. The two collections must not be merged.

---

### 7.5 `test_entries[]`

One entry per distinct standardized test result.

```json
{
  "entry_id": "UUID",
  "test_name": "string",
  "test_date": "string | null",
  "total_score": "string | null",
  "sectional_scores": [
    {
      "label": "string",
      "raw_score": "string | null"
    }
  ],
  "percentile": "string | null",
  "rank": "string | null",
  "result_status": "string",
  "confidence_score": "number"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 5.
- `test_name`: Name of the test as extracted (e.g. `"JEE Mains"`, `"SAT"`).
- `test_date`: Date string if present. Null if not found.
- `total_score`: Raw overall score string. Not normalized.
- `sectional_scores`: Array of section breakdowns with original label strings.
- `percentile`, `rank`: Raw strings if present. Null otherwise.
- `result_status`: Extraction status indicator. Values include `"available"`, `"pending"`.
- `confidence_score`: Extraction confidence.

---

### 7.6 `essay_entries[]`

One entry per distinct essay response.

```json
{
  "entry_id": "UUID",
  "essay_identifier": "string | null",
  "raw_text": "string | null",
  "word_count": "number | null",
  "placeholder_flag": "boolean",
  "short_response_flag": "boolean",
  "confidence_score": "number"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 6.
- `essay_identifier`: The essay prompt or label as extracted from the PDF.
- `raw_text`: Full unmodified essay text. Null if not extractable.
- `word_count`: Computed word count. Null if `raw_text` is null.
- `placeholder_flag`: `true` if the extracted text is a form placeholder rather than a written response.
- `short_response_flag`: `true` if the response is below a defined minimum length threshold.
- `confidence_score`: Extraction confidence.

---

### 7.7 `activity_entries[]`

One entry per distinct activity record.

```json
{
  "entry_id": "UUID",
  "activity_type": "string",
  "activity_name": "string | null",
  "position_title": "string | null",
  "level": "string | null",
  "duration": "string | null",
  "achievement": "string | null",
  "roles_and_responsibilities": "string | null",
  "description_raw": "string | null",
  "confidence_score": "number"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 7.
- `activity_type`: Assigned by Agent 7 using deterministic classification. Allowed values: `"extracurricular"`, `"co_curricular"`, `"leadership"`, `"other"`. Always present.
- `activity_name`, `position_title`: One or both may be present. Both may be null for sparse entries.
- `level`: Participation level string (e.g. `"District"`, `"National"`, `"Personal"`). Null if not found.
- `duration`: Raw duration string as extracted. May contain parse artifacts in some cases.
- `achievement`, `roles_and_responsibilities`, `description_raw`: Raw extracted strings. Null if not found.
- `confidence_score`: Extraction confidence.

Note on `activity_type` immutability: The classification assigned by Agent 7 must not be overridden by any downstream component — not by the projection layer, not by LLM Call 1, not by LLM Call 2.

---

### 7.8 `timeline_entries[]`

One entry per datable canonical event. Derived from `academic_entries[]` and `activity_entries[]` by Agent 9.

```json
{
  "entry_id": "UUID",
  "year": "string",
  "event_label": "string",
  "source_type": "string",
  "source_reference": "UUID"
}
```

Field rules:

- `entry_id`: UUID assigned by Agent 9.
- `year`: Year string. `"Unknown"` where no date can be resolved.
- `event_label`: Descriptive label for the event.
- `source_type`: The collection the entry derives from (`"academic"`, `"activity"`, `"test"`, `"essay"`).
- `source_reference`: The `entry_id` of the originating canonical entry.

Note: `timeline_entries[]` is excluded from canonical projections. It contains redundant information and is susceptible to parse artifact year values. Its purpose is internal chronological reference within the pipeline.

---

### 7.9 `cross_references`

Contains the entity map produced by Agent 8 — word-level tokens appearing across multiple canonical sections.

```json
{
  "entity_map": [
    {
      "entity_token": "string",
      "source_references": [
        {
          "source_type": "string",
          "entry_id": "UUID"
        }
      ]
    }
  ]
}
```

Note: `cross_references` is excluded from canonical projections. The token extraction is word-level and frequently produces noise tokens (common words, stop words) that have no meaningful reasoning value in isolation. Its purpose is deterministic cross-section detection within the pipeline, not LLM input.

---

### 7.10 `integrity_report`

Produced by Agent 10. Contains structural anomaly flags.

```json
{
  "anomalies": [
    {
      "anomaly_id": "string",
      "anomaly_type": "string",
      "severity_level": "string",
      "source_reference": "UUID | null",
      "description": "string"
    }
  ]
}
```

Field rules:

- `anomaly_id`: UUID assigned by Agent 10. Unique per anomaly entry.
- `anomaly_type`: Category of anomaly.
- `severity_level`: Severity classification of the anomaly.
- `source_reference`: The `entry_id` of the canonical entry associated with the anomaly, if applicable. Null if the anomaly is not tied to a specific entry.
- `description`: Plain text description of the detected anomaly.

Note: `integrity_report` is excluded from canonical projections. It is internal pipeline metadata and must not influence LLM reasoning.

---

### 7.11 `extraction_confidence`

Produced by Agent 11. Contains per-agent confidence scores and an aggregate.

```json
{
  "agent_scores": [
    {
      "agent_id": "number",
      "agent_name": "string",
      "confidence_score": "number"
    }
  ],
  "aggregate_confidence": "number"
}
```

Field rules:

- `agent_scores`: One entry per extraction agent (Agents 1–10).
- `confidence_score`: Range 0–1.
- `aggregate_confidence`: Computed aggregate across all agent scores. Range 0–1.

Note: `extraction_confidence` is excluded from canonical projections. It is internal pipeline metadata and must not be passed to LLM components.

---

## 8. Extensibility Rules

The canonical model is designed for safe additive evolution.

**Permitted without a version bump:**

- Adding new optional fields inside existing entry objects (e.g. adding a new nullable field to `academic_entries[]`)
- Adding new optional fields to `identifiers`
- Adding new metadata to `extraction_confidence.agent_scores`

**Requires a minor version bump (e.g. v1.1 → v1.2):**

- Adding a new top-level collection (e.g. a new array at the same level as `academic_entries[]`)
- Adding a new required field to any entry schema
- Changing the structure of `identifiers`

**Requires a major version bump (e.g. v1.x → v2.0):**

- Removing an existing field
- Renaming an existing field
- Changing the semantics of an existing field's values
- Restructuring collection schemas in a way that breaks backward compatibility

Because canonical is stored as JSONB, minor and additive changes do not require database schema migrations. The JSONB column absorbs structural evolution within the version discipline defined here.

---

## 9. Backward Compatibility Rules

All canonical version increments must preserve backward compatibility at the minor level.

A new canonical version must:

- Preserve all existing field names without renaming
- Preserve all existing field semantics — the meaning of stored values must not change
- Preserve all existing collection structures
- Not retroactively normalize stored raw values
- Not require modification of canonical records stored under a prior version

Canonical v1.1 is fully additive over v1.0. No field was removed or renamed. No stored value semantics changed.

Any future version following v1.1 must meet the same standard at the minor level.

---

## 10. Entity ID Philosophy

The canonical representation and the projection layer use two distinct identifier systems that coexist without conflict.

### 10.1 `entry_id` — Canonical Storage Identity

Every entry in every canonical collection has an `entry_id` — a UUID assigned by the extraction agent that created it. This UUID is:

- Stored in the canonical representation
- Used for internal pipeline cross-referencing (e.g. `timeline_entries[].source_reference`)
- Stable within a pipeline run
- Not exposed to LLM components

### 10.2 `entity_id` — Projection-Layer Reference Identity

During ROS projection, the ROS projector assigns a formatted entity ID to each canonical entry. This formatted ID is:

- Derived deterministically from canonical array order (e.g. first entry in `academic_entries[]` → `ACA-001`)
- Used by LLM components to reference canonical entries
- Present in projections and the signal-evidence bundle
- Not stored in the canonical representation
- Not a replacement for `entry_id` — both coexist

### 10.3 Why Two Systems

`entry_id` UUIDs serve storage and pipeline tracing purposes. They are opaque identifiers that carry no semantic information and are not human-readable.

`entity_id` formatted IDs serve LLM reasoning purposes. They are compact, human-readable, and stable enough within a pipeline run for the LLM to reference and for the Policy Guard to validate against.

### 10.4 Canonical Does Not Store Entity IDs

Entity IDs are generated during the ROS projection step and live in the projection layer. They are never written back to the canonical representation. A canonical record in `canonical_records` contains only `entry_id` UUIDs — never `entity_id` formatted strings.

---

## 11. Canonical vs ROS Distinction

| Dimension | Canonical Representation | ROS v1 Artifact |
|---|---|---|
| Role | Internal structural truth | Presentation-layer output |
| Structure | Collection-based arrays | Five structured pages |
| Versioning | `canonical_version` field | `report_version` in metadata |
| Content type | Extraction facts | Interview preparation content |
| LLM content | Never | Pages 4–5 only |
| Storage location | `canonical_records.canonical_data` | `synthesis_records.synthesis_output` |
| Mutability | Immutable after Agent 11 | Produced once per pipeline run |

**Canonical must not embed:**

- Page numbers or page groupings
- Section titles from ROS
- Theme IDs or theme content
- Question group IDs or question content
- Any LLM-generated text

**ROS must never:**

- Modify canonical field values
- Collapse or merge canonical collections
- Rewrite canonical text
- Introduce new canonical fields
- Store canonical data redundantly

---

## 12. Projection Governance

Stage 1.7 introduces canonical projections as a mechanism for providing curated views of canonical data to LLM reasoning stages. This section defines the canonical model's relationship to the projection layer.

### 12.1 Canonical as Projection Source

The canonical representation is the exclusive source for all canonical projections. No projection may introduce data that does not originate in the canonical record for the same application. No projection may introduce data from another application's canonical record.

### 12.2 Canonical Is Never Modified by Projections

Projection construction is a read operation. The projection layer reads from the canonical representation and produces a new, separate data structure. It does not write to, update, or delete from the canonical representation in any way.

The canonical record stored in `canonical_records` is identical before projection construction begins and after all projections have been consumed and discarded.

### 12.3 Projections Are Pipeline-Ephemeral

Canonical projections are not stored. They exist in memory during pipeline execution and are discarded after the LLM call they serve completes. A canonical projection is never written to `canonical_records` or any other table.

### 12.4 Multiple Projections From One Canonical Record

Multiple distinct projections may be derived from the same canonical record within a single pipeline run. In Stage 1.7, two projection-derived contexts are produced:

- The Call 1 canonical projection (constructed by Agent 13, consumed by Agent 14)
- Evidence excerpts within the signal-evidence bundle (extracted by Agent 15, consumed by Agent 16)

Both derive from the same canonical record. Both apply read-only access. Neither modifies the canonical record.

### 12.5 Canonical Is Not Structured for Projection Efficiency

The canonical model is structured for deterministic storage correctness. It is not restructured, optimized, or reorganized to make projection construction more efficient. If projection construction finds certain canonical sections noisy or redundant, the projection layer handles that through its own field inclusion rules — the canonical model is not changed to accommodate it.

---

## 13. Non-Evaluative Enforcement

The canonical representation must not contain evaluative content of any kind.

**Canonical must not include:**

- Applicant scores, rankings, or ratings assigned by the system
- Strength or weakness indicators
- Risk flags or concern markers
- Predictive fields (e.g. likelihood of admission)
- Normalized GPA equivalents computed from raw grades
- Converted percentage fields (raw values are stored, not converted)
- Competitiveness metrics of any kind
- Comparative indicators relative to other applicants or benchmarks

Raw scores and grades are stored exactly as found in the source PDF. The system does not assess what a score means. That judgment belongs to the human interviewer, informed by the structured ROS artifact.

This rule is absolute. No stage boundary decision may introduce evaluative fields into the canonical representation.

---

## 14. Invariant Check

| Invariant | Status |
|---|---|
| Canonical is collection-based — no fixed academic or test keys | ✅ |
| Canonical version is at v1.1 — no bump in Stage 1.7 | ✅ |
| Canonical is presentation-agnostic — no ROS grouping embedded | ✅ |
| Canonical is immutable after Agent 11 produces it | ✅ |
| Projections are read-only views — canonical never modified by projection | ✅ |
| Projections are pipeline-ephemeral — never stored in canonical_records | ✅ |
| Entity IDs are projection-layer metadata — never stored in canonical | ✅ |
| `activity_type` classification is assigned by Agent 7 and never overridden | ✅ |
| No evaluative fields in canonical | ✅ |
| No LLM-generated content in canonical | ✅ |
| Backward compatibility preserved — v1.1 is additive over v1.0 | ✅ |
| JSONB storage absorbs additive evolution without schema migration | ✅ |

---

*Canonical Model Philosophy Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*