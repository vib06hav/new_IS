# `agent_pipeline_spec_v1.5.md`

**(Stage 1.5 — Logical Agent Responsibilities with ROS v1 Projection Layer, Canonical v1.1 Aligned)**

---

## 1. Purpose of This Document

This document defines the logical agent architecture of the system.

It specifies:

* Agent identities (0–13)
* Responsibilities
* Input → Output contracts
* Confidence discipline
* Deterministic-first boundary
* LLM boundary rules
* Non-evaluative enforcement

This document governs logical execution only.

It does not define:

* JSON storage schema
* Database structure
* Docker topology
* Infrastructure components

ROS v1 integration affects output projection only.

Canonical v1.1 extends canonical structure without altering deterministic-first principles.

---

## 2. Deterministic-First Principle

Agents 1–11 are strictly deterministic.

They:

* Extract structured information
* Preserve raw values
* Avoid normalization
* Avoid scoring
* Avoid interpretation
* Avoid inference
* Avoid evaluation

They operate exclusively on the uploaded PDF content.

No LLM involvement is permitted in Agents 1–11.

This invariant remains absolute.

---

## 3. Agent Definitions

---

### Agent 0 — Pipeline Orchestrator

**Input:** Uploaded PDF path

**Responsibility:**

* Execute Agents 1–11 sequentially
* Collect outputs
* Propagate confidence metadata
* Abort on critical failure
* Pass canonical to projection layer
* Invoke Agent 12 (single LLM call)

**Output:**

* Canonical representation
* Full ROS v1 artifact

No extraction logic permitted inside Agent 0.

---

### Agent 1 — Layout Block Extractor

**Input:** PDF

**Responsibility:**

* Extract ordered layout blocks
* Preserve page metadata
* Preserve positional metadata
* Assign block-level confidence

**Output:** Ordered layout block list

No interpretation.

---

### Agent 2 — Section Boundary Detector

**Input:** Layout blocks

**Responsibility:**

* Detect logical section boundaries
* Support fuzzy matching
* Preserve unknown labels

**Output:** Structured section segments with confidence

No structural inference.

---

### Agent 3 — Personal Information Extractor

**Input:** Personal section

**Responsibility:**

* Extract identifiers
* Preserve raw values
* Populate `identifiers`
* Extract structured `family_background` if present
* Populate `identifiers.family_background`
* Do not normalize beyond explicit yes/no flags

**Output:** `identifiers` (including `family_background`)

No enrichment.
No inference of missing family members.

---

### Agent 4 — Academic Records Extractor

**Input:** Academic sections

**Responsibility:**

* Extract academic entries as collections
* Preserve grading scheme labels
* Preserve subject-level granularity
* Assign per-entry confidence
* Extract institutional affiliation data into `schooling_history[]`
* Keep `academic_entries[]` (performance records) distinct from `schooling_history[]` (institutional history)

**Output:**

* `academic_entries[]`
* `schooling_history[]`

No GPA conversion.
No normalization.
No merging of schooling and academic performance data.

---

### Agent 5 — Standardized Test Extractor

**Input:** Test sections

**Responsibility:**

* Extract test entries as collection
* Preserve percentiles and breakdowns
* Preserve awaited results

**Output:** `test_entries[]`

No ranking or comparison.

---

### Agent 6 — Essay Extractor

**Input:** Essay sections

**Responsibility:**

* Extract full essay text
* Compute word count
* Compute character count
* Detect placeholders
* Detect duplication
* Assign confidence

**Output:** `essay_entries[]`

No summarization.
No commentary.

---

### Agent 7 — Activity Extractor

**Input:** Activity sections

**Responsibility:**

* Extract activity entries as collection
* Preserve raw descriptions
* Assign confidence
* Assign explicit `activity_type` classification

Allowed `activity_type` values:

* `"extracurricular"`
* `"co_curricular"`
* `"leadership"`
* `"other"`

Classification must be:

* Deterministic
* Rule-based
* Based solely on extracted content
* Non-evaluative

Projection must not reclassify activities.

**Output:** `activity_entries[]` (including `activity_type`)

No importance weighting.

---

### Agent 8 — Cross-Section Entity Detector

**Input:** All canonical collections

**Responsibility:**

* Detect shared tokens across sections
* Build entity map
* Assign source references

**Output:** `cross_references`

No interpretation.

---

### Agent 9 — Timeline Builder

**Input:** All canonical collections

**Responsibility:**

* Build chronological event entries
* Reference originating entry_id

**Output:** `timeline_entries[]`

No trend analysis.

---

### Agent 10 — Completeness & Integrity Analyzer

**Input:** Canonical collections

**Responsibility:**

* Detect structural anomalies
* Assign severity level
* Preserve structural discipline

**Output:** `integrity_report`

No qualitative evaluation.

---

### Agent 11 — Canonical Structure Assembler

**Input:** Outputs from Agents 1–10

**Responsibility:**

* Assemble full canonical representation
* Stamp `"canonical_version": "1.1"`
* Preserve array insertion order
* Separate identifiers from extracted data
* Attach extraction confidence metadata

Canonical must include:

* `identifiers`
* `academic_entries[]`
* `schooling_history[]`
* `test_entries[]`
* `essay_entries[]`
* `activity_entries[]`
* `timeline_entries[]`
* `cross_references`
* `integrity_report`
* `extraction_confidence`

Agent 11 does NOT:

* Produce ROS
* Modify canonical for presentation
* Introduce entity grouping for UI

Canonical remains presentation-agnostic.

---

## 4. Deterministic ROS Projection Layer (Stage 1.5 Addition)

This is a logical projection layer, not a microservice and not an inference agent.

**Input:** Canonical representation (v1.1)

**Responsibility:**

* Assign stable `entity_id` values
* Construct:

  * Page 1 — Background Profile
  * Page 2 — Academic + Engagement
  * Page 3 — Essays + Deterministic Highlights
* Preserve canonical ordering
* Generate deterministic highlight spans
* Avoid rewriting content

**Output:** Partial ROS v1 (Pages 1–3)

This layer:

* Does not call LLM
* Does not alter canonical
* Does not collapse collections
* Does not infer meaning

---

## 4A. Deterministic Entity ID Assignment

Entity IDs are derived from canonical collections during ROS projection.

### Source of Order

* Canonical array order produced by Agent 11
* Insertion order must be preserved
* Projection must not sort collections

### Assignment Algorithm

For each canonical collection independently:

For i from 1 to len(collection):

```
formatted_id = PREFIX + "-" + zero_pad(i, 3)
```

Prefix mapping:

| Collection        | Prefix |
| ----------------- | ------ |
| academic_entries  | ACA    |
| test_entries      | TEST   |
| essay_entries     | ESS    |
| activity_entries  | ACT    |
| schooling_history | SCH    |

Rules:

* entity_id is derived from canonical order only
* entity_id is regenerated per projection
* entity_id does not replace canonical `entry_id`
* entity_id must be stable across identical canonical input
* Agent 13 validates LLM references against this deterministic map

---

## 5. Agent 12 — Synthesis Agent (Updated for ROS v1)

**Input:** Canonical representation

**Responsibility:**

* Perform exactly one LLM call
* Generate structured output:

  * `themes[]`
  * `question_groups[]`
* Reference valid `entity_id` values only
* Avoid evaluation language
* Avoid ranking
* Avoid new facts
* Avoid rewriting essays
* Avoid modifying deterministic pages

**Output:**

```json
{
  "themes": [...],
  "question_groups": [...]
}
```

The LLM generates only ROS Page 4 and Page 5.

No additional LLM calls permitted.

---

## 6. Agent 13 — Output Validation Filter

**Input:** LLM output

**Responsibility:**

* Validate JSON structure
* Validate every `referenced_entity_id` exists
* Validate every `theme_id` exists
* Validate `question_groups.theme_id` linkage
* Reject invented IDs
* Enforce policy guard rules

**Output:**

* Validated ROS thematic section
* Structured violations log if necessary

No correction LLM call allowed.

---

## 7. ROS Assembly Step

After Agent 13 validation:

* Merge deterministic Pages 1–3
* Merge validated LLM Pages 4–5
* Attach `report_metadata`
* Persist full ROS v1

This is not a separate inference agent.

It is a deterministic assembly step.

---

## 8. Confidence Discipline

Confidence is tracked at extraction stage only.

No theme-level confidence is introduced.

No question-group confidence is introduced.

No evaluation score is introduced.

---

## 9. Prohibited Behaviors

Agents must not:

* Introduce academic normalization
* Introduce strength/weakness flags
* Introduce admissions commentary
* Perform recursive reasoning
* Call LLM more than once
* Modify canonical to match UI grouping
* Store chain-of-thought

---

## 10. Stage 1.5 Invariants

| Invariant                          | Status |
| ---------------------------------- | ------ |
| Deterministic-first preserved      | ✅      |
| Single LLM call preserved          | ✅      |
| Canonical unchanged structurally   | ✅      |
| Collection-based storage preserved | ✅      |
| No evaluation logic introduced     | ✅      |
| No async introduced                | ✅      |
| No infra change required           | ✅      |
| No schema migration required       | ✅      |

---

End of Document.

---
