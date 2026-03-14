# `canonical_model_philosophy_v1.5.md`

**(Stage 1.5 — Canonical Representation Philosophy with ROS Projection Separation, Canonical v1.1)**

---

## 1. Purpose of This Document

This document defines the philosophical rules governing the canonical representation.

It does not define:

* Database schema
* API responses
* LLM prompt templates
* Docker configuration
* Presentation formatting

It defines:

* Structural invariants
* Collection discipline
* Versioning rules
* Separation principles
* Extensibility rules

Stage 1.5 introduces ROS v1 as a presentation-layer artifact.

Canonical version 1.1 evolves the canonical structure to support ROS v1 while preserving all deterministic-first and collection-based principles.

---

## 2. Core Principle — Canonical Is Internal Structural Truth

The canonical representation is the authoritative, structured form of extracted application data.

It is:

* Deterministically constructed
* Collection-based
* Non-evaluative
* Presentation-agnostic
* Versioned
* Stored as JSONB

Canonical representation is not a report.

Canonical representation is not a UI contract.

Canonical representation is not modified to satisfy layout concerns.

ROS v1 is derived from canonical.

Canonical is never reshaped to match ROS grouping.

---

## 3. Collection-Based Storage

All repeating structures must be represented as collections (arrays).

Examples:

* `academic_entries[]`
* `test_entries[]`
* `essay_entries[]`
* `activity_entries[]`
* `schooling_history[]`
* `timeline_entries[]`

No collection may be collapsed into:

* Fixed academic level keys (e.g., `class_12`)
* Fixed test names (e.g., `sat`)
* Fixed essay labels (e.g., `career_statement`)
* Fixed activity categories

Collection discipline prevents:

* Schema rigidity
* Regional academic bias
* Hardcoded institutional assumptions

This remains unchanged in Canonical v1.1.

---

## 4. No Fixed Academic Keys Rule

Canonical must not include:

* `class_10`
* `class_12`
* `grade_11`
* `undergraduate_year_1`
* `sat_score`
* `jee_percentile`

Instead, canonical uses entry objects with:

```json
{
  "entry_id": "UUID",
  "academic_level": "string",
  "board_name": "string",
  ...
}
```

This rule remains absolute in Stage 1.5.

---

## 5. Separation of Concerns

Canonical representation separates:

| Category              | Purpose                             |
| --------------------- | ----------------------------------- |
| identifiers           | Identity and background metadata    |
| extracted collections | Academic, tests, essays, activities |
| integrity_report      | Structural anomalies                |
| extraction_confidence | Agent-level confidence              |

ROS v1 introduces a projection layer.

However:

* Canonical does not include page grouping
* Canonical does not include theme grouping
* Canonical does not include question grouping
* Canonical does not include UI ordering logic

Projection occurs after canonical assembly.

---

## 6. Versioning Rule

Canonical representation includes:

```json
"canonical_version": "1.1"
```

Version string format:

```
major.minor
```

Canonical version 1.1 introduces:

* Structured `family_background` under identifiers
* New `schooling_history[]` collection
* Explicit `activity_type` classification inside activity_entries

These additions:

* Do not alter collection discipline
* Do not require schema migration
* Do not collapse collections
* Do not introduce evaluation logic

ROS versioning remains independent from canonical versioning.

---

## 7. Extensibility Requirement

Canonical must allow:

* Additional fields inside entry objects
* New entry types added in future stages
* Additional metadata fields

Without:

* Database schema migration
* Collection collapse
* Breaking backward compatibility

Because canonical is stored as JSONB, structural evolution is permitted within version discipline.

Canonical v1.1 preserves this extensibility model.

---

## 8. Backward Compatibility Rule

New canonical versions must:

* Preserve existing field meanings
* Avoid renaming fields destructively
* Avoid reinterpreting stored raw values
* Avoid retroactive normalization

Canonical v1.1 is additive only.

No existing field semantics are changed.

---

## 9. Entity ID Philosophy (Clarified for Stage 1.5)

Canonical stores stable `entry_id` values as UUIDs.

Projection derives formatted `entity_id` values deterministically.

Important:

* `entity_id` does not replace `entry_id`
* `entity_id` is not stored in canonical
* `entity_id` is generated during projection only
* `entity_id` must be derived deterministically from canonical array order

Canonical remains storage structure.

Entity IDs exist to support:

* Cross-reference anchoring
* LLM theme referencing
* Highlight mapping

They are projection-layer metadata, not canonical schema shifts.

---

## 10. Canonical v1.1 Structural Additions

### 10.1 family_background (Identifiers Extension)

Canonical now includes:

```json
identifiers.family_background
```

Structure:

```json
{
  "father": {
    "name": "string|null",
    "education": "string|null",
    "occupation": "string|null",
    "organization": "string|null"
  },
  "mother": {
    "name": "string|null",
    "education": "string|null",
    "occupation": "string|null",
    "organization": "string|null"
  }
}
```

This field is:

* Deterministically extracted
* Non-evaluative
* Optional (null-safe)
* Stored within canonical JSONB
* Independent from presentation-layer grouping

---

### 10.2 schooling_history (New Collection)

Canonical now includes:

```json
schooling_history[]
```

Structure:

```json
{
  "entry_id": "UUID",
  "level": "string",
  "school_name": "string|null",
  "board_name": "string|null",
  "location": "string|null",
  "confidence_score": "number"
}
```

This collection:

* Represents institutional affiliation
* Is distinct from academic_entries (performance records)
* Is collection-based
* Does not collapse into academic_entries
* Preserves deterministic ordering

---

### 10.3 activity_type (Explicit Classification)

Each activity entry must include:

```json
activity_type
```

Allowed values:

```
"extracurricular"
"co_curricular"
"leadership"
"other"
```

Classification:

* Occurs during deterministic extraction
* Must not be inferred during projection
* Must not be inferred by LLM
* Must remain non-evaluative

Projection groups activities strictly by this field.

---

## 11. Canonical vs ROS Distinction

| Canonical                       | ROS v1                         |
| ------------------------------- | ------------------------------ |
| Internal structural model       | Presentation-layer artifact    |
| Collection-based                | Page-grouped                   |
| Versioned via canonical_version | Versioned via report_version   |
| Extraction truth                | Interview preparation artifact |
| Stored in canonical_records     | Stored in synthesis_records    |

Canonical must not embed:

* Page numbers
* Section titles
* Theme grouping
* Question grouping
* LLM-generated content

ROS must never mutate canonical content.

---

## 12. Non-Evaluative Enforcement

Canonical representation must not include:

* Applicant scoring
* Ranking
* Strength/weakness flags
* Risk indicators
* Predictive fields
* Normalized GPA equivalents
* Converted percentage fields
* Competitiveness metrics

This remains absolute in Canonical v1.1.

---

## 13. Stage 1.5 Invariants

| Invariant                            | Status |
| ------------------------------------ | ------ |
| Collection-based structure preserved | ✅      |
| No fixed academic keys introduced    | ✅      |
| Canonical independent from ROS       | ✅      |
| Canonical version incremented safely | ✅      |
| No evaluation logic introduced       | ✅      |
| No schema change required            | ✅      |
| No infra change required             | ✅      |

---

End of Document.

---
