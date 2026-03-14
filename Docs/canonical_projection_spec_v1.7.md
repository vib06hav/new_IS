# `canonical_projection_spec_v1.7.md`

**(Stage 1.7 — Canonical Projection Layer Specification)**

---

## 1. Purpose of This Document

This document defines the canonical projection layer introduced in Stage 1.7 of the AG_InterviewStandardiser system.

It specifies:

- What a canonical projection is and why it exists
- The rules that govern all projection construction
- The exact field-level mapping from canonical representation to each projection
- What is included, what is excluded, and why
- How entity IDs are assigned and carried into projections
- The two distinct projections used in the Stage 1.7 pipeline
- Edge case handling for null fields, parse artifacts, and sparse entries

This document does not define:

- The canonical representation itself (governed by `canonical_model_philosophy_v1.7.md`)
- The deterministic signal schema or signal detection rules (governed by `signal_architecture_spec_v1.7.md`)
- The LLM call contracts or prompts (governed by `llm_synthesis_contract_v1.7.md`)
- The signal-evidence bundle schema (governed by `signal_architecture_spec_v1.7.md`, Section 10)
- The ROS output structure (governed by `ROS_v1.7.md`)
- Database schema or persistence rules (governed by `database_schema_v1.7.md`)

---

## 2. Foundational Definitions

The following terms are used throughout this document. All terms are defined here before use.

**Canonical Representation** — The authoritative, structured, versioned (v1.1) output of the deterministic extraction pipeline (Agents 1–11). Contains all extracted applicant data in collection-based form. Stored as JSONB in the `canonical_records` table. Never modified by any downstream component.

**Canonical Projection** — A curated, read-only view of the canonical representation constructed for a specific LLM reasoning task. A projection contains a purposeful subset of canonical fields. It is not stored. It does not modify canonical data. It is constructed fresh for each pipeline run and discarded after use.

**Entity ID** — A stable, formatted identifier assigned to each canonical entry by the deterministic ROS projection layer prior to projection construction. Format: `PREFIX-###` where PREFIX is collection-specific (see Section 5). Entity IDs are derived deterministically from canonical array order. They are the mechanism by which LLM components reference canonical entries.

**Pipeline-Ephemeral** — An artifact that exists only within the memory of a single pipeline execution. Pipeline-ephemeral artifacts are not persisted to the database and are not available after the pipeline completes.

**Parse Artifact** — A field value that is present in the canonical representation but contains extraction noise rather than genuine applicant data. Parse artifacts arise when the PDF parser encounters form labels, placeholder text, or structural elements and incorrectly populates a data field with that text. Examples: a `duration` field containing `"Mobile Number"`, a `year` field containing `"Mobi"`, a `roles_and_responsibilities` field containing `"In what capacity does this reference"`. Parse artifacts are identified by deterministic rules and excluded from projections.

**Null Field** — A canonical field with a `null` value. Null fields indicate that the extraction pipeline could not find a value for the field in the source PDF. They are omitted from projections entirely — they are not passed as `null`.

**Sparse Entry** — A canonical collection entry in which most fields are null or contain parse artifacts but at least one meaningful field is present. Sparse entries are included in projections in reduced form using whatever substantive fields are available. They are not silently dropped.

**ROS Projector** — The deterministic component (`app/projection/ros_projector.py`) that maps canonical data to ROS Pages 1–3 and assigns all entity IDs. The ROS projector runs before projection construction and its entity ID assignments are inherited by all canonical projections.

---

## 3. Why Projections Exist

The canonical representation is structured for deterministic storage correctness, not for LLM reasoning. Its structure optimizes for completeness, auditability, and machine-readable consistency. When passed directly to an LLM, it introduces several categories of problem.

### 3.1 Internal Metadata Noise

The canonical representation contains fields that are meaningful to the extraction pipeline but irrelevant or misleading to an LLM reasoning about an applicant.

- **Confidence scores** — `"confidence_score": 0.85` is an extraction pipeline signal. It does not help an LLM understand an applicant's profile and could incorrectly influence reasoning if present.
- **Entry UUIDs** — Internal identifiers like `"entry_id": "257f54dc-0842-4d5e-8881-a8f70c93a75c"` serve database and pipeline tracing functions. They add token overhead and have no reasoning value. Entity IDs (`ACA-001`, `ACT-003`) replace them for LLM-facing use.
- **Extraction flags** — Fields like `placeholder_flag` and `short_response_flag` are internal quality indicators. They must not be passed to an LLM.

### 3.2 Parse Artifacts

The extraction pipeline operates on raw PDFs that may contain form labels, field headers, or structural text that the parser misidentifies as applicant data. These values enter the canonical representation without modification because the canonical layer records what was extracted, not what was intended.

Examples of parse artifacts observed in real canonical outputs:

- `"duration": "Mobile Number"` — a form field label captured as an activity duration value
- `"year": "Mobi"` — a truncated form label captured as a timeline year
- `"roles_and_responsibilities": "In what capacity does this reference"` — a form prompt captured as a responsibility description

If passed to an LLM, these artifacts would appear as genuine applicant data and could produce incoherent or misleading signal interpretations. The projection layer identifies and excludes them deterministically.

### 3.3 Structural Redundancy

The canonical representation contains several sections that duplicate or partially duplicate content already present in other sections:

- `schooling_history[]` records the same school name, board, and level as `academic_entries[]` but without score or subject data. It adds no reasoning value beyond what `academic_entries[]` already provides.
- `timeline_entries[]` references the same entries as `academic_entries[]` and `activity_entries[]` by source reference, but adds parse-artifact-prone fields like `year` and the redundant `event_label` string. It provides no additional applicant content.

Including these sections in a projection increases token consumption without improving reasoning quality.

### 3.4 Cross-Reference Noise

The `cross_references.entity_map` section contains word-level tokens shared across canonical sections. While this structure is useful for deterministic cross-section analysis, the tokens it contains are frequently single common words extracted without semantic context — for example: `"This"`, `"Applications"`, `"Social"`, `"Studies"`, `"School"`. These tokens are not meaningful reasoning inputs and must not be passed to an LLM.

### 3.5 Token Economy

Each LLM call in the Stage 1.7 pipeline must be bounded in scope. LLM Call 1 should reason about the applicant's profile and signals. LLM Call 2 should generate interview guidance from a signal-evidence bundle. Neither call benefits from receiving the full canonical document. The projection layer ensures that each LLM stage receives exactly the context it needs to perform its task — no more, no less.

---

## 4. Projection Principles

All canonical projections are governed by the following rules without exception.

**Read-only.** The projection layer reads from the canonical representation. It does not modify, update, append to, or delete from it under any circumstances.

**Purpose-scoped.** Each projection is constructed for a specific LLM stage. The Call 1 projection serves signal interpretation. The Call 2 input serves interview generation. No projection is general-purpose.

**Entity ID preserving.** All entity IDs assigned by the ROS projector are carried into projections exactly as assigned. The projection layer does not assign, modify, or re-index entity IDs.

**No inference.** The projection layer makes no judgments about the quality, significance, or relevance of canonical entries. It does not filter by duration, performance, or any other criterion. It applies mechanical inclusion and exclusion rules only.

**Null omission, not null passing.** Fields with `null` values are omitted from projections entirely. The LLM receives a projection with no null fields. This reduces noise and prevents the LLM from treating missing data as a meaningful signal.

**Sparse entry inclusion.** An entry that is partially populated is included in reduced form. Only the non-null, non-artifact fields of a sparse entry are included. An entry is dropped entirely only if it contains no substantive fields after null omission and artifact removal.

**Parse artifact exclusion.** Fields identified as containing parse artifacts are excluded. Artifact identification rules are defined in Section 7.4.

**No reordering.** Collections are presented in the same order as they appear in the canonical representation. The projection layer does not sort, rank, or reorder entries.

**No summarization.** The projection layer does not summarize, paraphrase, or condense field values. Field values are included as-is from canonical, subject to null omission and artifact exclusion.

**Pipeline-ephemeral.** Projections are not stored in any database table or column. They exist only in memory during pipeline execution and are discarded after the LLM call they serve completes.

**Canonical immutability.** No action taken by the projection layer, including null omission or artifact exclusion, modifies the canonical record. The canonical representation stored in `canonical_records` remains unchanged.

---

## 5. Entity ID Assignment

Entity IDs are assigned by the deterministic ROS projector before projection construction begins. The projection layer inherits these assignments and does not create new ones.

### 5.1 Assignment Rules

Entity IDs are assigned by iterating over each collection in the canonical representation in array order. The first entry in each collection receives index `001`, the second `002`, and so on. Assignment is zero-padded to three digits.

### 5.2 Prefix Mapping

| Canonical Collection | Entity ID Prefix | Example |
|---|---|---|
| `academic_entries[]` | `ACA` | `ACA-001`, `ACA-002` |
| `activity_entries[]` | `ACT` | `ACT-001`, `ACT-003` |
| `test_entries[]` | `TST` | `TST-001` |
| `essay_entries[]` | `ESS` | `ESS-001`, `ESS-002` |
| `schooling_history[]` | `SCH` | `SCH-001`, `SCH-002` |

`SCH` entity IDs are assigned by the ROS projector for use in ROS Page 1 construction (`schooling_history` entries appear in Page 1). They are not included in the entity_id_map passed to LLM Call 1 or LLM Call 2. `schooling_history[]` is excluded from all canonical projections and from the signal-evidence bundle. LLM components never reference `SCH` entity IDs.

### 5.3 Entity ID Map

The ROS projector produces an entity ID map for each application: a flat lookup structure pairing each entity ID with a brief descriptor of its canonical entry. This map is included in projections and in the signal-evidence bundle so that LLM components can resolve entity ID references without access to the full canonical document.

Entity ID map entry format:

```json
{
  "entity_id": "ACA-001",
  "collection": "academic_entries",
  "descriptor": "9TH grade — The Shri Ram School, Vasant Vihar — 91%"
}
```

The descriptor is constructed deterministically from canonical field values. It is not generated by an LLM.

### 5.4 Stability Guarantee

Entity IDs for a given application are stable within a pipeline run. The same canonical array entry always receives the same entity ID. If the canonical representation is regenerated (i.e., the pipeline is re-run on the same PDF), entity IDs are reassigned by the same rules and produce the same values provided the canonical array order is the same.

---

## 6. Canonical Projection for LLM Call 1

### 6.1 Purpose

The Call 1 projection provides LLM Call 1 with the context it needs to identify interpreted signals. It contains all substantive applicant data from the canonical representation in a cleaned, token-efficient form, together with the deterministic signal collection generated before projection construction.

LLM Call 1 uses this projection to reason about observable patterns in the applicant's academic record, test performance, activity profile, and essay content.

### 6.2 Structure

The Call 1 projection is a JSON object with the following top-level keys:

```json
{
  "applicant_context": {},
  "academic_profile": [],
  "test_profile": [],
  "essay_profile": [],
  "activity_profile": [],
  "entity_id_map": [],
  "deterministic_signals": []
}
```

Each section is defined below.

---

### 6.3 `applicant_context`

Derived from `canonical.identifiers`.

**Included fields:**

| Canonical Field | Projection Field | Notes |
|---|---|---|
| `identifiers.full_name` | `full_name` | Always included |
| `identifiers.preferred_major` | `preferred_major` | Always included |
| `identifiers.family_background.father.name` | `father.name` | Included if non-null |
| `identifiers.family_background.father.education` | `father.education` | Included if non-null |
| `identifiers.family_background.father.field_of_employment` | `father.field_of_employment` | Included if non-null |
| `identifiers.family_background.father.organization` | `father.organization` | Included if non-null |
| `identifiers.family_background.father.designation` | `father.designation` | Included if non-null |
| `identifiers.family_background.mother.name` | `mother.name` | Included if non-null |
| `identifiers.family_background.mother.education` | `mother.education` | Included if non-null |
| `identifiers.family_background.mother.field_of_employment` | `mother.field_of_employment` | Included if non-null |
| `identifiers.family_background.mother.organization` | `mother.organization` | Included if non-null |
| `identifiers.family_background.mother.designation` | `mother.designation` | Included if non-null |

**Excluded fields:**

| Canonical Field | Reason |
|---|---|
| `identifiers.application_id` | Internal pipeline identifier, not applicant data |
| `identifiers.date_of_birth` | Not relevant to signal interpretation |

**Null handling:** If all father fields are null, the `father` key is omitted from `applicant_context`. The same applies to `mother`. If both are null, the `family_background` key is omitted entirely. Individual null fields within a partially populated parent are omitted; the parent key is retained.

**Example — fully populated father, null mother:**

Canonical input:
```json
"family_background": {
  "father": {
    "name": "Rohit Kapoor",
    "education": "MBA",
    "field_of_employment": "Finance and Consulting",
    "organization": "KPMG India",
    "designation": "Partner"
  },
  "mother": {
    "name": null,
    "education": null,
    "field_of_employment": null,
    "organization": null,
    "designation": null
  }
}
```

Projection output:
```json
"applicant_context": {
  "full_name": "Ananya Kapoor",
  "preferred_major": "Computer Science and Artificial Intelligence",
  "family_background": {
    "father": {
      "name": "Rohit Kapoor",
      "education": "MBA",
      "field_of_employment": "Finance and Consulting",
      "organization": "KPMG India",
      "designation": "Partner"
    }
  }
}
```

---

### 6.4 `academic_profile`

Derived from `canonical.academic_entries[]`. One entry per canonical academic record.

**Included fields per entry:**

| Canonical Field | Projection Field | Notes |
|---|---|---|
| *(assigned by ROS projector)* | `entity_id` | e.g. `ACA-001` |
| `academic_level` | `level` | e.g. `"9TH"`, `"10TH"` |
| `school_name` | `school_name` | Included if non-null |
| `board_name` | `board_name` | Included if non-null |
| `academic_year` | `year` | Included if non-null |
| `grading_mode` | `grading_mode` | e.g. `"percentage"` |
| `score_raw` | `overall_score` | Included if non-null |
| `subject_entries[].subject_name` | `subjects[].subject` | Included for all subjects |
| `subject_entries[].score_raw` | `subjects[].score` | Included if non-null |

**Excluded fields per entry:**

| Canonical Field | Reason |
|---|---|
| `entry_id` | Internal UUID, replaced by entity ID |
| `confidence_score` | Extraction metadata |
| `marking_scheme_raw` | Redundant with `grading_mode` |
| `predicted_score_raw` | Included only if non-null (see note below) |
| `subject_entries[].predicted_score_raw` | Included only if non-null (see note below) |

**Note on predicted scores:** `predicted_score_raw` at both overall and subject level is included in the projection if and only if it is non-null. If null, it is omitted. This means predicted scores appear in the projection only for entries where a predicted score was actually recorded.

**Example — single academic entry:**

Canonical input:
```json
{
  "entry_id": "257f54dc-0842-4d5e-8881-a8f70c93a75c",
  "academic_level": "9TH",
  "school_name": "The Shri Ram School, Vasant Vihar",
  "board_name": "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS (ISC)",
  "academic_year": "2022",
  "marking_scheme_raw": "Percentage",
  "grading_mode": "percentage",
  "score_raw": "91",
  "predicted_score_raw": null,
  "subject_entries": [
    { "subject_name": "Mathematics", "score_raw": "92", "predicted_score_raw": null },
    { "subject_name": "Computer Applications", "score_raw": "95", "predicted_score_raw": null }
  ],
  "confidence_score": 0.85
}
```

Projection output:
```json
{
  "entity_id": "ACA-001",
  "level": "9TH",
  "school_name": "The Shri Ram School, Vasant Vihar",
  "board_name": "COUNCIL FOR THE INDIAN SCHOOL CERTIFICATE EXAMINATIONS (ISC)",
  "year": "2022",
  "grading_mode": "percentage",
  "overall_score": "91",
  "subjects": [
    { "subject": "Mathematics", "score": "92" },
    { "subject": "Computer Applications", "score": "95" }
  ]
}
```

---

### 6.5 `test_profile`

Derived from `canonical.test_entries[]`. One entry per canonical test record.

**Included fields per entry:**

| Canonical Field | Projection Field | Notes |
|---|---|---|
| *(assigned by ROS projector)* | `entity_id` | e.g. `TST-001` |
| `test_name` | `test_name` | Always included |
| `total_score` | `total_score` | Included if non-null |
| `sectional_scores[].label` | `sections[].label` | Included for all sections |
| `sectional_scores[].raw_score` | `sections[].score` | Included if non-null |
| `percentile` | `percentile` | Included if non-null |
| `rank` | `rank` | Included if non-null |

**Excluded fields per entry:**

| Canonical Field | Reason |
|---|---|
| `entry_id` | Internal UUID, replaced by entity ID |
| `test_date` | Not relevant to signal interpretation |
| `result_status` | Extraction pipeline status flag, not applicant data |
| `confidence_score` | Extraction metadata |

**Example — JEE Mains entry:**

Canonical input:
```json
{
  "entry_id": "21d0f287-4e7b-4e81-b01e-cb8c6cee0176",
  "test_name": "JEE Mains",
  "test_date": null,
  "total_score": "98.4",
  "sectional_scores": [
    { "label": "Physics Percentile", "raw_score": "96.9" },
    { "label": "Maths Percentile", "raw_score": "98.4" },
    { "label": "Chemistry Percentile", "raw_score": "97.0" }
  ],
  "percentile": null,
  "rank": null,
  "result_status": "available",
  "confidence_score": 0.9
}
```

Projection output:
```json
{
  "entity_id": "TST-001",
  "test_name": "JEE Mains",
  "total_score": "98.4",
  "sections": [
    { "label": "Physics Percentile", "score": "96.9" },
    { "label": "Maths Percentile", "score": "98.4" },
    { "label": "Chemistry Percentile", "score": "97.0" }
  ]
}
```

---

### 6.6 `essay_profile`

Derived from `canonical.essay_entries[]`. One entry per canonical essay record.

**Included fields per entry:**

| Canonical Field | Projection Field | Notes |
|---|---|---|
| *(assigned by ROS projector)* | `entity_id` | e.g. `ESS-001` |
| `essay_identifier` | `prompt` | The essay question or prompt |
| `raw_text` | `text` | Full essay text, unmodified |

**Excluded fields per entry:**

| Canonical Field | Reason |
|---|---|
| `entry_id` | Internal UUID, replaced by entity ID |
| `word_count` | Derivable by LLM if needed; not a reasoning input |
| `placeholder_flag` | Extraction quality flag; not applicant data |
| `short_response_flag` | Extraction quality flag; not applicant data |
| `confidence_score` | Extraction metadata |

**Inclusion condition:** An essay entry is included if `placeholder_flag` is `false` and the `raw_text` field is non-null and non-empty. An essay entry with `placeholder_flag: true` is excluded because it does not represent genuine applicant writing.

**Example — essay entry:**

Canonical input:
```json
{
  "entry_id": "e6700163-939d-420a-80c7-710f2e96540d",
  "essay_identifier": "What excites you about a career in engineering/technology?",
  "raw_text": "My interest in technology has grown over the years...",
  "word_count": 398,
  "placeholder_flag": false,
  "short_response_flag": false,
  "confidence_score": 0.9
}
```

Projection output:
```json
{
  "entity_id": "ESS-001",
  "prompt": "What excites you about a career in engineering/technology?",
  "text": "My interest in technology has grown over the years..."
}
```

---

### 6.7 `activity_profile`

Derived from `canonical.activity_entries[]`. One entry per canonical activity record.

This section requires the most careful handling because activity entries exhibit the widest variation in canonical completeness and are the most susceptible to parse artifacts.

**Included fields per entry:**

| Canonical Field | Projection Field | Condition |
|---|---|---|
| *(assigned by ROS projector)* | `entity_id` | Always |
| `activity_type` | `type` | Always (canonical guarantees presence) |
| `activity_name` | `name` | If non-null |
| `position_title` | `position` | If non-null |
| `level` | `level` | If non-null |
| `duration` | `duration_years` | If non-null and passes artifact check (see Section 7.4) |
| `achievement` | `achievement` | If non-null |
| `roles_and_responsibilities` | `responsibilities` | If non-null and passes artifact check (see Section 7.4) |

**Excluded fields per entry:**

| Canonical Field | Reason |
|---|---|
| `entry_id` | Internal UUID, replaced by entity ID |
| `description_raw` | Raw extracted text not structured for reasoning |
| `confidence_score` | Extraction metadata |

**Sparse entry handling:** An activity entry is included if it has at least one of: a non-null `activity_name`, a non-null `position_title`, or a non-null `achievement`. An entry with none of these fields after artifact removal is dropped entirely — it has no substantive content to contribute.

**Example 1 — well-populated extracurricular entry:**

Canonical input:
```json
{
  "entry_id": "ae001894-a1e5-4d0f-8d85-bc5c88d82808",
  "activity_type": "extracurricular",
  "activity_name": "Chess",
  "position_title": "Ranked 3rd in School and top 10 in 2023 event",
  "level": "District",
  "duration": "4",
  "achievement": null,
  "roles_and_responsibilities": null,
  "description_raw": null,
  "confidence_score": 0.95
}
```

Projection output:
```json
{
  "entity_id": "ACT-001",
  "type": "extracurricular",
  "name": "Chess",
  "position": "Ranked 3rd in School and top 10 in 2023 event",
  "level": "District",
  "duration_years": "4"
}
```

**Example 2 — leadership entry with valid position, no name:**

Canonical input:
```json
{
  "entry_id": "83613426-facc-4543-b490-92a7b465a5ea",
  "activity_type": "leadership",
  "activity_name": null,
  "position_title": "School Prefect",
  "level": null,
  "duration": null,
  "achievement": null,
  "roles_and_responsibilities": null,
  "description_raw": null,
  "confidence_score": 0.95
}
```

Projection output:
```json
{
  "entity_id": "ACT-005",
  "type": "leadership",
  "position": "School Prefect"
}
```

**Example 3 — leadership entry with parse artifacts:**

Canonical input:
```json
{
  "entry_id": "af7dfd9d-6a97-4f8e-9abb-1720613e08f9",
  "activity_type": "leadership",
  "activity_name": null,
  "position_title": "Organization",
  "level": null,
  "duration": "Mobile Number",
  "achievement": null,
  "roles_and_responsibilities": "In what capacity does this reference",
  "description_raw": null,
  "confidence_score": 0.95
}
```

After artifact removal: `duration` is excluded (parse artifact), `roles_and_responsibilities` is excluded (parse artifact), `activity_name` is null. `position_title` value `"Organization"` is marginal but is a non-null string — it is retained as the only substantive field. The entry remains included in reduced form.

Projection output:
```json
{
  "entity_id": "ACT-006",
  "type": "leadership",
  "position": "Organization"
}
```

---

### 6.8 `entity_id_map`

A flat array of entity ID descriptors for all entries included in the projection. Constructed deterministically by the ROS projector.

```json
"entity_id_map": [
  { "entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "9TH — The Shri Ram School, Vasant Vihar — 91%" },
  { "entity_id": "ACA-002", "collection": "academic_entries", "descriptor": "10TH — The Shri Ram School, Vasant Vihar — 99%" },
  { "entity_id": "TST-001", "collection": "test_entries", "descriptor": "JEE Mains — 98.4" },
  { "entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "Essay: What excites you about a career in engineering/technology?" },
  { "entity_id": "ACT-001", "collection": "activity_entries", "descriptor": "Chess — extracurricular — District" }
]
```

The entity ID map is the reference against which all signal entity ID citations are validated. Any entity ID referenced by LLM Call 1 that does not appear in this map is treated as an invented ID and fails validation.

---

### 6.9 `deterministic_signals`

Each deterministic signal in this collection conforms to the following schema:
```json
{
  "signal_id": "DET-###",
  "signal_type": "string",
  "observation": "string",
  "referenced_entity_ids": ["string"],
  "source_collection": "string"
}
```

- `signal_id`: Format `DET-###`, numbered sequentially from `DET-001`
- `signal_type`: One of the allowed signal type values defined in `signal_architecture_spec_v1.7.md` Section 6.5
- `observation`: Plain factual statement. No evaluative language.
- `referenced_entity_ids`: Valid entity IDs from the entity ID map
- `source_collection`: The canonical collection from which the signal was derived

The signals appended here are the direct output of deterministic signal detection, unchanged.

---

### 6.10 Sections Excluded from Call 1 Projection

The following canonical sections are excluded from the Call 1 projection entirely.

| Canonical Section | Reason for Exclusion |
|---|---|
| `schooling_history[]` | Redundant with `academic_entries[]`. Contains the same school name, board, and level data without scores or subjects. Adds no reasoning value. |
| `timeline_entries[]` | Derives from `academic_entries[]` and `activity_entries[]` by reference. Adds no new content. Frequently contains parse artifact year values (e.g. `"Mobi"`, `"Unknown"`). |
| `cross_references.entity_map` | Contains word-level tokens extracted across sections. Token quality is low — includes common words and stop words (e.g. `"This"`, `"Social"`, `"Studies"`) that provide no meaningful reasoning signal. |
| `integrity_report` | Internal extraction quality report. Not applicant data. |
| `extraction_confidence` | Internal pipeline confidence reporting. Not applicant data. |

---

## 7. Parse Artifact Detection

### 7.1 Purpose

Parse artifact detection is a deterministic check applied during projection construction to identify field values that contain extraction noise rather than genuine applicant data. Fields identified as parse artifacts are excluded from the projection.

### 7.2 Scope

Parse artifact detection is applied to the following fields:

- `activity_entries[].duration`
- `activity_entries[].roles_and_responsibilities`
- `activity_entries[].activity_name`
- `activity_entries[].position_title`

It is not applied to essay `raw_text`, academic scores, or test scores because those fields have structural constraints that prevent artifact contamination.

### 7.3 Duration Artifact Rule

An `activity_entries[].duration` value is treated as a parse artifact if it is a non-null string that cannot be interpreted as a number.

- `"4"` — valid, numeric string. Included.
- `"7"` — valid, numeric string. Included.
- `"10"` — valid, numeric string. Included.
- `"Mobile Number"` — not a numeric string. Parse artifact. Excluded.
- `""` — empty string. Treated as null. Excluded.

The check is: attempt to parse the string as a float. If parsing succeeds, the value is included as `duration_years`. If parsing fails, the value is excluded.

### 7.4 Text Field Artifact Rules

A text field (`roles_and_responsibilities`, `activity_name`, `position_title`) is treated as a parse artifact if it matches any of the following conditions:

- It contains a question mark (characteristic of form prompt text, e.g. `"In what capacity does this reference"`)
- It is a single generic word with no applicant-specific meaning in context (evaluated against a fixed blocklist: `["Organization", "Reference", "Position", "Role", "Title", "Name", "Duration", "Level"]`)
- It matches a known form label pattern (e.g. `"Mobile Number"`, `"Email Address"`, `"Date of Birth"`)

**Note on the single generic word rule:** This rule applies only to `activity_name` and `roles_and_responsibilities`. It does not apply to `position_title` — because legitimate position titles like `"School Prefect"`, `"Captain"`, or `"President"` may be single words or short phrases that are also common words. The `position_title` field is therefore included if non-null regardless of the generic word check, with the exception of known form label matches.

**Applying this to Example 3 from Section 6.7:**
- `position_title: "Organization"` — matches the blocklist for generic words, but since this is `position_title`, the generic word rule does not apply. The known form label check: `"Organization"` does not match known form labels. Result: retained.
- `duration: "Mobile Number"` — matches known form label pattern. Result: excluded.
- `roles_and_responsibilities: "In what capacity does this reference"` — contains a question mark. Result: excluded.

### 7.5 Behavior on Full Artifact Removal

If artifact removal eliminates all fields of an activity entry except `activity_type`, and there is no non-null `activity_name`, `position_title`, or `achievement`, the entry is dropped entirely from the projection. An entry with only a `type` field provides no reasoning value.

---

## 8. Canonical Projection for LLM Call 2

### 8.1 What LLM Call 2 Receives

LLM Call 2 does not receive a canonical projection. It receives the **signal-evidence bundle** — a distinct artifact constructed after signal validation.

The signal-evidence bundle is defined in `signal_architecture_spec_v1.7.md`, Section 10. The projection layer does not construct it; the bundle construction step (Agent 15) does.

This distinction is architecturally significant: LLM Call 2 is intentionally isolated from the raw canonical data. It sees only what the validated interpreted signals identify as relevant, paired with the canonical evidence that supports each signal. This ensures that interview generation is grounded in interpretation-layer reasoning, not in direct access to the full applicant record.

The signal-evidence bundle conforms to the following schema:
```json
{
  "application_id": "string",
  "signal_evidence_pairs": [
    {
      "signal": {
        "signal_id": "INT-###",
        "title": "string",
        "description": "string",
        "referenced_entity_ids": ["string"]
      },
      "evidence": [
        {
          "entity_id": "string",
          "collection": "string",
          "content": {}
        }
      ]
    }
  ]
}
```

Each `signal_evidence_pair` contains one validated interpreted signal and the canonical evidence entries it references. The `content` object follows the same field inclusion rules as the canonical projection — no confidence scores, no internal UUIDs, no null fields.

### 8.2 Evidence Excerpts Within the Bundle

When Agent 15 constructs evidence excerpts for the bundle, it extracts content from the canonical representation using the same field inclusion rules as the Call 1 projection. Specifically:

- Confidence scores are excluded
- Internal UUIDs are excluded, entity IDs are used
- Null fields are omitted
- Parse artifact fields are excluded
- Full essay text is included if the signal references an essay entity

The bundle is not a projection in the formal sense — it is scoped to signals, not to the full applicant profile — but it applies the same data hygiene rules as the projection layer when extracting canonical content.

---

## 9. Field Stripping Reference Table

The following table provides a complete field-by-field reference for implementers.

### 9.1 `identifiers`

| Field | Included in Projection | Reason if Excluded |
|---|---|---|
| `application_id` | No | Internal pipeline identifier |
| `full_name` | Yes | — |
| `date_of_birth` | No | Not relevant to signal interpretation |
| `preferred_major` | Yes | — |
| `family_background.father.*` | Yes (if non-null) | — |
| `family_background.mother.*` | Yes (if non-null) | — |

### 9.2 `academic_entries[]`

| Field | Included in Projection | Reason if Excluded |
|---|---|---|
| `entry_id` | No | Internal UUID; replaced by entity ID |
| `academic_level` | Yes | — |
| `school_name` | Yes (if non-null) | — |
| `board_name` | Yes (if non-null) | — |
| `academic_year` | Yes (if non-null) | — |
| `marking_scheme_raw` | No | Redundant with `grading_mode` |
| `grading_mode` | Yes | — |
| `score_raw` | Yes (if non-null) | — |
| `predicted_score_raw` | Yes (if non-null) | Omitted if null |
| `subject_entries[].subject_name` | Yes | — |
| `subject_entries[].score_raw` | Yes (if non-null) | — |
| `subject_entries[].predicted_score_raw` | Yes (if non-null) | Omitted if null |
| `confidence_score` | No | Extraction metadata |

### 9.3 `test_entries[]`

| Field | Included in Projection | Reason if Excluded |
|---|---|---|
| `entry_id` | No | Internal UUID; replaced by entity ID |
| `test_name` | Yes | — |
| `test_date` | No | Not relevant to signal interpretation |
| `total_score` | Yes (if non-null) | — |
| `sectional_scores[].label` | Yes | — |
| `sectional_scores[].raw_score` | Yes (if non-null) | — |
| `percentile` | Yes (if non-null) | — |
| `rank` | Yes (if non-null) | — |
| `result_status` | No | Extraction pipeline status flag |
| `confidence_score` | No | Extraction metadata |

### 9.4 `essay_entries[]`

| Field | Included in Projection | Reason if Excluded |
|---|---|---|
| `entry_id` | No | Internal UUID; replaced by entity ID |
| `essay_identifier` | Yes | — |
| `raw_text` | Yes (if non-null and non-placeholder) | — |
| `word_count` | No | Derivable; not a reasoning input |
| `placeholder_flag` | No | Extraction quality flag; entry excluded entirely if true |
| `short_response_flag` | No | Extraction quality flag |
| `confidence_score` | No | Extraction metadata |

### 9.5 `activity_entries[]`

| Field | Included in Projection | Reason if Excluded |
|---|---|---|
| `entry_id` | No | Internal UUID; replaced by entity ID |
| `activity_type` | Yes | — |
| `activity_name` | Yes (if non-null, post-artifact check) | — |
| `position_title` | Yes (if non-null, post-artifact check) | — |
| `level` | Yes (if non-null) | — |
| `duration` | Yes (if numeric string) | Excluded if parse artifact |
| `achievement` | Yes (if non-null) | — |
| `roles_and_responsibilities` | Yes (if non-null, post-artifact check) | Excluded if parse artifact |
| `description_raw` | No | Unstructured raw extraction text |
| `confidence_score` | No | Extraction metadata |

### 9.6 Excluded Canonical Sections

| Section | Included | Reason |
|---|---|---|
| `schooling_history[]` | No | Redundant with `academic_entries[]` |
| `timeline_entries[]` | No | Redundant; contains parse artifact year values |
| `cross_references.entity_map` | No | Word-level token noise |
| `integrity_report` | No | Internal extraction quality report |
| `extraction_confidence` | No | Internal pipeline metadata |

---

## 10. What a Projection Is Not

The following behaviors are explicitly prohibited for the projection layer.

**A projection does not filter by quality.** An activity entry with a short duration or sparse fields is not dropped because it appears less significant. The projection layer has no concept of significance. Entries are included or excluded by deterministic rules, not by value judgments.

**A projection does not summarize content.** Essay text is passed as-is. Academic records are passed as-is. The projection layer does not condense, paraphrase, or reduce content.

**A projection does not reorder evidence.** Collections are presented in canonical array order. The projection layer does not sort academic entries by score, prioritize activities by duration, or reorder any collection to imply a ranking or narrative.

**A projection does not introduce new fields.** All fields in a projection must trace to a canonical field or to the entity ID map. The projection layer does not compute derived values (e.g. GPA, score delta, duration sum) or append analytical observations.

**A projection does not evaluate performance.** The academic profile section contains scores. These are passed as raw values. The projection layer makes no determination about whether a score is high, low, improving, or declining. That is the responsibility of LLM Call 1 and the deterministic signal layer.

**A projection does not make decisions about what the LLM should notice.** The projection layer does not emphasize certain entries over others, does not bold or annotate notable values, and does not pre-label patterns. Its role is to provide clean, structured context — not to guide interpretation.

---

## 11. Projection Construction Verification

Before passing a completed projection to an LLM call, the following deterministic checks must pass.

| Check | Rule |
|---|---|
| Entity ID completeness | Every entry included in the projection has an entity ID. No entry is present without one. |
| Entity ID map coverage | Every entity ID appearing in the projection body also appears in `entity_id_map`. |
| No null fields | No field in the projection has a `null` value. Null fields were omitted at construction time. |
| No empty arrays | A section array (e.g. `academic_profile`) is omitted entirely if it would be empty rather than included as an empty array. |
| Deterministic signals attached | `deterministic_signals` is present and non-empty before the projection is passed to Call 1. |
| No internal metadata | No `confidence_score`, `entry_id`, `placeholder_flag`, `short_response_flag`, `result_status`, or `extraction_confidence` fields are present anywhere in the projection. |

If any check fails, the projection is not passed to the LLM and the pipeline is halted. The failure reason is logged.

---

## 12. Projection Lifecycle

```
Canonical Representation (from canonical_records)
    ↓
Entity ID Assignment (ROS Projector)
    ↓
Deterministic Signal Detection (Agent 12)
    ↓
Call 1 Projection Construction (Agent 13)
    [Apply field inclusion rules]
    [Apply null omission]
    [Apply parse artifact detection]
    [Attach entity ID map]
    [Attach deterministic signals]
    ↓
Projection Verification
    ↓
LLM Call 1 — Signal Interpretation (Agent 14)
    [Projection consumed]
    [Projection discarded after call completes]
    ↓
Signal Validation (Policy Guard — Call 1 invocation)
    ↓
Signal–Evidence Bundle Construction (Agent 15)
    [Evidence excerpts extracted from canonical]
    [Same field hygiene rules applied]
    ↓
LLM Call 2 — Interview Generation (Agent 16)
    [Bundle consumed]
    [Bundle discarded after call completes]
```

Neither the Call 1 projection nor the signal-evidence bundle is stored to the database. Both are pipeline-ephemeral. The canonical representation in `canonical_records` is unchanged throughout this lifecycle.

---

*Canonical Projection Specification Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*