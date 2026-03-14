# `signal_architecture_spec_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis Architecture)**

---

## 1. Purpose of This Document

This document defines the signal-guided two-stage LLM synthesis architecture introduced in Stage 1.7.

It specifies:

- The reasoning architecture that governs LLM synthesis from Stage 1.7 onward
- All new pipeline layers and their responsibilities
- All artifact schemas that pass between layers
- Validation and failure behavior at each stage
- Prohibited behaviors for each LLM stage
- Invariants governing the two-call model

This document is the primary reference for Stage 1.7. All other Stage 1.7 documents derive from the definitions and decisions made here.

This document does not define:

- Database schema
- Docker topology
- API route structure
- ROS page structure (governed by `ROS_v1.7.md`)
- Individual agent implementation details (governed by `agent_pipeline_spec_v1.7.md`)

---

## 2. System Context

### 2.1 What the System Does

The system processes structured application PDFs submitted by applicants and produces a structured interview preparation report for use by human interviewers.

It does not evaluate, score, rank, or assess applicants. It does not predict admissions outcomes. It standardizes applicant data into a structured format that supports informed, consistent interviewer preparation.

The system produces a **Report Output Specification (ROS v1)** artifact as its final output. This artifact contains five pages:

- Pages 1–3: Deterministically projected from extracted applicant data
- Pages 4–5: Generated through LLM synthesis — interview themes and question groups

### 2.2 The Extraction Foundation

All factual applicant data originates from a deterministic extraction pipeline consisting of Agents 1–11. These agents operate exclusively on the uploaded PDF without any LLM involvement. They produce a **Canonical Representation** — the authoritative, structured, versioned (v1.1) form of all extracted data.

The Canonical Representation is:

- Collection-based
- Non-evaluative
- Presentation-agnostic
- Stored as JSONB in `canonical_records`

The Canonical Representation is the source of truth for all downstream processing. No LLM component may modify it.

### 2.3 Why a Two-Stage Architecture Was Introduced

Prior to Stage 1.7, the system performed a single LLM call per application. That call received the canonical representation and produced themes and question groups directly. This compressed interpretation and presentation into a single step.

Stage 1.7 replaces this single call with a two-stage synthesis model. The single-call model is no longer used.

---

## 3. Motivation for Two-Stage Architecture

The single-call synthesis model produced functional output but exhibited structural weaknesses.

**Interpretation and presentation were compressed into one step.** A single LLM call was required to simultaneously analyze the applicant's profile and produce interviewer-facing questions. These are distinct cognitive tasks that benefit from separation.

**Theme quality was limited by shallow evidence grounding.** Without an explicit interpretation stage, themes were generated directly from raw canonical data, producing generic outputs that did not reflect identifiable applicant-specific patterns.

**Traceability between evidence and interview guidance was weak.** There was no intermediate layer that explicitly connected canonical evidence to the themes it supported.

The two-stage architecture resolves these problems by separating:

```
Stage 1 — Interpretation: What does this applicant's profile signal?
Stage 2 — Presentation: How should an interviewer explore those signals?
```

---

## 4. Vocabulary Definitions

The following terms are used throughout this document. All terms are defined here before use.

**Canonical Representation** — The authoritative structured output of Agents 1–11. Contains all extracted applicant data in versioned, collection-based form. Stored in `canonical_records`. Never modified by LLM components.

**Canonical Projection** — A curated, read-only view of the Canonical Representation constructed for a specific LLM reasoning task. Contains a subset of canonical fields. Never modifies canonical data. Pipeline-ephemeral.

**Deterministic Signal** — An observable, measurable pattern derived from canonical data without LLM involvement. Examples: sustained activity participation across multiple years, subject performance distribution, leadership role presence. Deterministic signals do not represent interpretations.

**Interpreted Signal** — A higher-level behavioral inference produced by LLM Call 1. Derived from deterministic signals and canonical projection. Must reference valid canonical entity IDs. Must not contain evaluative language. Represents a pattern of behavior, not an assessment of it.

**Signal Schema** — The required structure for both deterministic signals and interpreted signals. Defined in Sections 6.4 and 8.3 respectively.

**Signal Validation** — A deterministic post-Call-1 step that verifies interpreted signals conform to schema, reference valid entity IDs, and contain no prohibited language.

**Signal–Evidence Bundle** — A structured artifact produced after signal validation. Pairs each validated interpreted signal with its supporting canonical evidence. The sole input to LLM Call 2.

**Entity ID** — A stable, formatted identifier assigned to each canonical entry during ROS projection. Format: `PREFIX-###` (e.g., `ACA-001`, `ACT-003`). Entity IDs are derived deterministically from canonical array order. LLM components must only reference entity IDs they have been explicitly provided.

**Policy Guard** — The deterministic validation module (`policy/guard.py`) that enforces prohibited language rules and entity ID reference validity. Invoked at two points in the Stage 1.7 pipeline.

**ROS Assembly** — The deterministic step that merges deterministic ROS Pages 1–3 with LLM-generated Pages 4–5 into the final ROS v1 artifact.

---

## 5. Updated Pipeline Architecture

### 5.1 Full Pipeline Flow

```
PDF Upload
    ↓
Agent 0 — Orchestrator
    ↓
Agents 1–11 — Deterministic Extraction
    ↓
Canonical Representation (v1.1)
    ↓
Deterministic ROS Projection (Pages 1–3)
    ↓
Deterministic Signal Detection
    ↓
Canonical Projection Construction (Call 1 context)
    ↓
LLM Call 1 — Signal Interpretation
    ↓
Signal Validation (Policy Guard — Call 1 invocation)
    ↓
Signal–Evidence Bundle Construction
    ↓
LLM Call 2 — Interview Generation
    ↓
Output Validation (Policy Guard — Call 2 invocation)
    ↓
ROS Assembly
(Pages 1–3 from deterministic projection + Pages 4–5 from Call 2 output)
    ↓
Persist Canonical + ROS v1
    ↓
Return ROS v1
```

### 5.2 Execution Model

The pipeline is strictly sequential and synchronous. All stages execute within a single request lifecycle. There is no parallel execution, no background processing, and no deferred stages. LLM Call 1 must complete and its output must be validated before LLM Call 2 is invoked.

### 5.3 Boundary Classification

| Stage | Type | LLM Involved |
|---|---|---|
| Agents 1–11 | Deterministic extraction | No |
| ROS Projection (Pages 1–3) | Deterministic projection | No |
| Deterministic Signal Detection | Deterministic analysis | No |
| Canonical Projection Construction | Deterministic view construction | No |
| LLM Call 1 — Signal Interpretation | LLM synthesis | Yes |
| Signal Validation | Deterministic validation | No |
| Signal–Evidence Bundle Construction | Deterministic assembly | No |
| LLM Call 2 — Interview Generation | LLM synthesis | Yes |
| Output Validation | Deterministic validation | No |
| ROS Assembly | Deterministic assembly | No |

The LLM boundary is precisely two calls. No other component invokes an LLM.

---

## 6. Deterministic Signal Detection Layer

### 6.1 Purpose

Before LLM reasoning begins, the system derives observable patterns from the canonical representation without any inference. These are deterministic signals — structured observations that anchor the interpretation stage in measurable data.

### 6.2 What Deterministic Signals Are

Deterministic signals represent observable facts about the canonical dataset that a rule-based analysis can identify. They are not interpretations. They are structured observations.

Examples of valid deterministic signals:

- An activity entry spans more than three years of participation
- Subject performance shows a distribution concentrated in one domain
- A leadership role entry is present
- An essay entry has a word count significantly below the typical range
- Academic entries show consistent performance across levels
- Multiple activity entries share a common domain keyword

### 6.3 What Deterministic Signals Are Not

Deterministic signals must not:

- Interpret the meaning of an observation
- Assess whether an observation is positive or negative
- Rank or compare observations
- Introduce facts not present in canonical data
- Reference entity IDs that do not exist in canonical

### 6.4 Deterministic Signal Schema

Each deterministic signal must conform to the following structure:

```json
{
  "signal_id": "DET-###",
  "signal_type": "string",
  "observation": "string",
  "referenced_entity_ids": ["string"],
  "source_collection": "string"
}
```

Field rules:

- `signal_id`: Formatted identifier assigned sequentially. Prefix `DET`.
- `signal_type`: Category of observation. Allowed values defined in Section 6.5.
- `observation`: Plain factual description of what was observed. No evaluative language.
- `referenced_entity_ids`: Entity IDs of the canonical entries that produced this signal. Must all be valid.
- `source_collection`: The canonical collection from which the signal was derived.

### 6.5 Allowed Signal Types

```
"duration_pattern"
"domain_concentration"
"leadership_presence"
"academic_distribution"
"essay_characteristic"
"cross_section_pattern"
"activity_volume"
"test_performance_pattern"
"timeline_characteristic"
```

New signal types may be added in future stages. Unlisted types must not be used.

### 6.6 Output

The deterministic signal detection layer produces a collection:

```
deterministic_signals[]
```

This collection is passed to the canonical projection construction step for Call 1.

---

## 7. Canonical Projection Layer

### 7.1 Purpose

The Canonical Representation is optimized for deterministic storage, not for LLM reasoning. Passing the full canonical document to an LLM introduces unnecessary token overhead, structural noise, and metadata irrelevant to the reasoning task.

The canonical projection layer produces curated, read-only views of canonical data tailored to each LLM call's reasoning context.

### 7.2 Projection Rules

A canonical projection:

- Is a strict subset of the canonical representation
- Preserves entity IDs for all included entries
- Removes internal metadata (confidence scores, extraction flags, integrity severity levels)
- Removes raw layout and positional data
- Does not reorder collections
- Does not collapse collections
- Does not introduce fields not present in canonical
- Does not modify field values
- Is pipeline-ephemeral — not stored as a canonical record
- Is not stored in `canonical_records`

The canonical representation is never modified by projection construction.

### 7.3 Call 1 Projection

The projection provided to LLM Call 1 includes:

- `identifiers` (excluding internal extraction metadata)
- `identifiers.family_background`
- `academic_entries[]` (including subject-level data, excluding confidence scores)
- `schooling_history[]` (excluding confidence scores)
- `test_entries[]` (including breakdown data, excluding confidence scores)
- `essay_entries[]` (full text included, excluding duplication ratio, placeholder flags, character count)
- `activity_entries[]` (including `activity_type`, excluding confidence scores)
- `deterministic_signals[]` (appended to projection context, not a canonical field)
- Entity ID map derived from canonical array order

The Call 1 projection does not include:

- `timeline_entries[]`
- `cross_references`
- `integrity_report`
- `extraction_confidence`
- Any raw layout block data

### 7.4 Call 2 Projection

LLM Call 2 does not receive a canonical projection directly. It receives only the signal-evidence bundle. The bundle contains curated evidence excerpts derived from canonical data — it is not the projection itself. This is defined in Section 10.

---

## 8. LLM Call 1 — Signal Interpretation

### 8.1 Purpose

LLM Call 1 is the interpretation engine. Its sole responsibility is to analyze the canonical projection and deterministic signals and produce a structured collection of interpreted signals.

This call performs analysis only. It does not generate interview questions, narrative summaries, or thematic groupings. Those responsibilities belong to LLM Call 2.

### 8.2 Input

LLM Call 1 receives:

- The Call 1 canonical projection (as defined in Section 7.3)
- The deterministic signal collection (as defined in Section 6.4)
- The entity ID map for the current application

LLM Call 1 does not receive:

- Raw canonical JSONB
- Confidence scores
- Integrity anomaly data
- Any output from a prior LLM call
- Any content from prior applications

### 8.3 Required Output

LLM Call 1 must return a strictly valid JSON object:

```json
{
  "interpreted_signals": [
    {
      "signal_id": "INT-###",
      "title": "string",
      "description": "string",
      "referenced_entity_ids": ["string"],
      "supporting_det_signal_ids": ["string"]
    }
  ]
}
```

Field rules:

- `signal_id`: Formatted identifier. Prefix `INT`. Numbered sequentially.
- `title`: A neutral, concise label for the interpreted signal. No evaluative language.
- `description`: A factual behavioral observation grounded in evidence. No evaluative language. No new facts.
- `referenced_entity_ids`: Must reference only entity IDs provided in the Call 1 projection. No invented IDs.
- `supporting_det_signal_ids`: Must reference only `signal_id` values from the deterministic signal collection provided as input.

### 8.4 Prohibited Outputs — Call 1

LLM Call 1 must not produce:

- Interview questions of any kind
- Narrative summaries
- Thematic groupings
- Evaluative language (see Section 13 for prohibited term list)
- New facts not present in canonical
- Invented entity IDs
- Invented deterministic signal IDs
- Admissions commentary
- Comparative language between applicants
- Predictions or likelihood statements
- Strength or weakness assessments

### 8.5 Call Constraints

- Exactly one invocation per application
- No retries on failure
- No fallback to any alternative synthesis approach
- No recursive prompting
- No chaining of Call 1 output back into Call 1

---

## 9. Signal Validation Layer

### 9.1 Purpose

Before interpreted signals can influence interview preparation, they are subjected to deterministic validation. This layer ensures that LLM Call 1 output conforms to the required schema, references valid entities, and contains no prohibited language.

### 9.2 Validation Rules

The signal validation layer must verify all of the following.

**Structural validation:**
- The response is valid JSON
- The `interpreted_signals` key is present
- Each signal contains all required fields: `signal_id`, `title`, `description`, `referenced_entity_ids`, `supporting_det_signal_ids`
- No required field is null or empty

**Entity ID validation:**
- Every `referenced_entity_id` in every signal exists in the entity ID map provided to Call 1
- No invented entity IDs are present

**Deterministic signal ID validation:**
- Every `supporting_det_signal_ids` value exists in the deterministic signal collection that was provided to Call 1
- No invented deterministic signal IDs are present

**Language validation:**
- No prohibited term (as defined in Section 13) appears in any `title` or `description` field

**Signal ID format validation:**
- All `signal_id` values follow the `INT-###` format
- No duplicate `signal_id` values exist

### 9.3 Failure Behavior

If validation fails for any reason:

- The interpreted signal collection is rejected in its entirety
- No partial acceptance of signals is permitted
- No corrective LLM call is triggered
- The pipeline is marked as failed
- The failure reason is logged with the application ID
- No ROS artifact is produced for this application

There is no fallback synthesis path. Failure at signal validation is a terminal pipeline failure.

### 9.4 Success Output

If all validation rules pass, the signal validation layer produces:

- A validated interpreted signal collection
- A structured violations log confirming zero violations

The validated signal collection is passed to the signal-evidence bundle construction step.

---

## 10. Signal–Evidence Bundle Construction

### 10.1 Purpose

The signal-evidence bundle is the sole input to LLM Call 2. It pairs each validated interpreted signal with the canonical evidence that supports it.

This layer is deterministic. It performs no inference. It assembles a structured context document from validated signals and canonical data.

### 10.2 Construction Rules

For each validated interpreted signal:

- Extract the canonical entries corresponding to its `referenced_entity_ids` from the canonical representation
- Include the relevant fields from those entries (full text for essays, scores and breakdowns for tests, descriptions for activities, performance data for academic entries)
- Exclude confidence scores, extraction metadata, and integrity data
- Preserve entity IDs on all included entries
- Pair the signal metadata with its evidence entries as a single bundle unit

### 10.3 Bundle Schema

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

### 10.4 Bundle Rules

- The bundle must not include canonical entries not referenced by any validated signal
- The bundle must not include the full canonical representation
- The bundle must not include deterministic signal metadata beyond the `supporting_det_signal_ids` references
- The bundle must not include confidence scores or extraction metadata
- The bundle must not introduce new entity IDs
- The bundle is pipeline-ephemeral

---

## 11. LLM Call 2 — Interview Generation

### 11.1 Purpose

LLM Call 2 is the presentation engine. Its sole responsibility is to transform validated, evidence-grounded signals into interviewer-facing themes and question groups.

Because interpretation has already occurred in Call 1, Call 2 focuses entirely on communication — producing structured outputs that help interviewers explore the applicant's experiences and motivations.

### 11.2 Input

LLM Call 2 receives:

- The signal-evidence bundle (as defined in Section 10)
- The entity ID map for the current application

LLM Call 2 does not receive:

- The full canonical representation
- Raw canonical projection
- Confidence scores
- Deterministic signal collection directly
- The raw output of LLM Call 1
- Any content from prior applications

### 11.3 Required Output

LLM Call 2 must return a strictly valid JSON object conforming to the ROS Pages 4–5 schema:

```json
{
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "string",
      "description": "string",
      "referenced_entity_ids": ["string"]
    }
  ],
  "question_groups": [
    {
      "theme_id": "THEME-###",
      "group_title": "string",
      "questions": ["string"]
    }
  ]
}
```

Field rules:

- `theme_id`: Unique identifier per theme. Format `THEME-###`.
- All `referenced_entity_ids` must exist in the entity ID map provided with the bundle.
- Each `question_groups` entry must reference a valid `theme_id` from the `themes` array.
- Questions must be open-ended and exploratory.

The output of LLM Call 2 maps directly to the ROS artifact as follows:

- `themes[]` becomes `page_4_focus_themes`
- `question_groups[]` becomes `page_5_question_groups`

These two objects are passed to the ROS Assembly step unchanged, provided they pass output validation. No reformatting, renaming, or restructuring of these objects occurs between Call 2 output and ROS page population. The schema defined here is therefore identical to the ROS Pages 4–5 schema defined in `ROS_v1.7.md`.

### 11.4 Prohibited Outputs — Call 2

LLM Call 2 must not produce:

- Evaluative language (see Section 13)
- New facts not present in the signal-evidence bundle
- Invented entity IDs
- Invented theme IDs referenced in question groups but not defined in themes
- Admissions commentary
- Comparative language
- Predictions or likelihood statements
- Strength or weakness assessments
- Rewritten essay content
- Modified academic records

### 11.5 Call Constraints

- Exactly one invocation per application
- No retries on failure
- No recursive prompting
- No chaining of Call 2 output back into Call 1 or Call 2

### 11.6 Relationship to ROS Output

LLM Call 2 is the sole source of ROS Pages 4 and 5. No other pipeline component contributes to these pages.

ROS Pages 1–3 are produced independently by the deterministic ROS projection layer before the signal pipeline begins. Pages 1–3 and Pages 4–5 are produced through entirely separate paths and merged only at the ROS Assembly step.

The complete five-page ROS v1 artifact is therefore composed as:

| ROS Page | Source | Pipeline Stage |
|---|---|---|
| Page 1 — Background Profile | Canonical projection | Deterministic ROS Projection |
| Page 2 — Academic + Engagement | Canonical projection | Deterministic ROS Projection |
| Page 3 — Essays | Canonical projection + deterministic highlights | Deterministic ROS Projection |
| Page 4 — Focus Themes | LLM Call 2 output (`themes[]`) | Interview Generation |
| Page 5 — Question Groups | LLM Call 2 output (`question_groups[]`) | Interview Generation |

Pages 4–5 are populated directly from validated Call 2 output without modification. The ROS assembly step does not transform, reformat, or reinterpret the Call 2 output — it places it into the final artifact structure as-is.

This means the quality and validity of Pages 4–5 is entirely determined by the signal pipeline — the deterministic signals, the interpreted signals, the signal-evidence bundle, and the constraints enforced by the two validation layers.

---

## 12. Output Validation Layer

### 12.1 Purpose

After LLM Call 2, the output is validated by the policy guard before ROS assembly. This is the same policy guard module used throughout the system, invoked here for Call 2 output.

### 12.2 Validation Rules

**Structural validation:**
- Response is valid JSON
- `themes` and `question_groups` keys are present
- All required fields per theme and question group are present

**Theme ID validation:**
- All `theme_id` values are unique
- All `question_groups.theme_id` values reference a defined theme

**Entity ID validation:**
- All `referenced_entity_ids` in themes exist in the entity ID map provided to Call 2
- No invented entity IDs

**Language validation:**
- No prohibited term appears in any theme title, description, group title, or question

### 12.3 Failure Behavior

If validation fails:

- The Call 2 output is rejected
- No corrective LLM call is triggered
- The pipeline is marked as failed
- Failure reason is logged
- No ROS artifact is produced

---

## 13. Prohibited Language

The following terms must not appear in any LLM-generated content at either call. This list applies to both interpreted signal output (Call 1) and theme and question output (Call 2).

```
"Strength"
"Weakness"
"Outstanding"
"Exceptional"
"Deficiency"
"Below average"
"Underperformance"
"High potential"
"Top candidate"
"Risk factor"
"Admit"
"Reject"
"Likelihood"
"Impressive"
"Concerning"
"Excellent"
"Poor"
"Weak"
"Strong"
"Competitive"
"Uncompetitive"
```

This list may be extended in future stages. It may not be shortened without a formal stage boundary decision.

---

## 14. Two-Call Invariants

The following rules are absolute for Stage 1.7 and are locked in `architecture_lock_v1.7.md`.

**Exactly two LLM calls per application.** No more, no fewer. Call 1 performs interpretation. Call 2 performs interview generation. No additional calls are permitted for refinement, correction, summarization, or any other purpose.

**Call independence.** Call 2 receives only the validated signal-evidence bundle. It does not receive raw Call 1 output. It does not receive the full canonical representation. It does not receive any content that has not passed through the signal validation layer.

**Sequential execution.** Call 1 must complete and its output must be validated before Call 2 is invoked. No parallel execution.

**No recursion.** Call 1 output must not be fed back into Call 1. Call 2 output must not be fed back into Call 2 or into Call 1.

**No fallback.** There is no fallback to any alternative synthesis approach.

**Canonical immutability.** No LLM component at any stage modifies the canonical representation.

---

## 15. Signal Storage Decision

Interpreted signals are pipeline-ephemeral by default. They are not persisted in a dedicated table or column.

If signal data is required for auditability or debugging, it may be embedded as a structured key within the existing `synthesis_records.synthesis_output` JSONB field alongside the ROS artifact. This requires no schema migration, no new tables, and no new columns.

The decision to include or exclude signal data in `synthesis_output` is a deployment configuration decision and must be made explicitly before Stage 1.7 goes to production. It must not be left ambiguous.

---

## 16. Invariant Check

| Invariant | Status |
|---|---|
| Deterministic extraction unchanged (Agents 1–11) | ✅ |
| Exactly two LLM calls per application | ✅ |
| Call 2 receives only validated signal-evidence bundle | ✅ |
| No recursive LLM calls | ✅ |
| Sequential synchronous execution | ✅ |
| Canonical representation never modified by LLM | ✅ |
| No evaluative language permitted in any LLM output | ✅ |
| Entity ID references validated deterministically | ✅ |
| No new tables or schema migrations introduced | ✅ |
| No infrastructure changes introduced | ✅ |
| ROS Pages 4–5 output schema unchanged | ✅ |
| LLM Call 2 output maps directly to ROS Pages 4–5 | ✅ |
| No fallback to any alternative synthesis approach | ✅ |

---

*Signal Architecture Specification Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*