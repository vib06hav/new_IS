Below is the structured mitigation document for Stage 1 LLM synthesis boundary refinement.

This document strictly complies with:

*  (`architecture_lock.md`)
*  (`system_overview.md`)
*  (`agent_pipeline_spec.md`)
*  (`canonical_model_philosophy.md`)
*  (`llm_synthesis_contract.md`)
*  (`stage_1_migration_plan.md`)
*  (`env_config_spec.md`)

`architecture_lock.md` prevails in all cases of interpretation.

No prohibited changes are introduced.

---

# LLM Synthesis Boundary Structural Mitigation

(Stage 1 — Deterministic Projection Strategy)

---

# 1. Root Cause Analysis

## 1.1 Current Behavior

Agent 12 currently:

* Serializes the entire canonical representation.
* Injects the full JSON document into the LLM prompt.
* Includes:

  * All collections (academic, test, essay, activity, timeline).
  * All metadata.
  * Full essay raw text.
  * Full activity descriptions.
  * Full cross-reference structures.
  * Integrity anomalies.
  * Confidence metadata.

This produces:

* ~10,000+ tokens input.
* Model context window: 4096.
* Prompt truncation.
* Increased latency.
* Instability under synchronous Stage 1 constraints.

---

## 1.2 Why Token Explosion Occurs

The explosion is deterministic and structural:

### A. JSON Structural Overhead

Canonical is JSONB transport-level structure.

Each field includes:

* Key names
* Nested objects
* Repeated attribute labels
* UUIDs
* Confidence fields
* Structural metadata

JSON formatting alone can consume 20–30% of token budget.

---

### B. Essay Raw Text Duplication

Essays are included in full:

* raw_text
* word_count
* character_count
* duplication_ratio
* flags
* confidence_score

The LLM does not need structural metrics.
It needs content signal only.

Raw essays dominate token usage.

---

### C. High-Entropy Repetition

Collections:

* academic_entries
* subject_entries
* test_entries
* activity_entries

Contain repeated key labels for each object.

This compounds token waste.

---

### D. Metadata Leakage

The following reach the LLM unnecessarily:

* extraction_confidence
* anomaly severity levels
* duplication_ratio
* placeholder flags
* component_tags
* internal entry_id UUIDs

These are structural artifacts, not synthesis inputs.

---

## 1.3 Architectural Assessment

This is **not** a violation of:

* Deterministic-first
* Single LLM boundary
* Canonical philosophy
* Stage boundaries

It is an inefficient boundary serialization problem.

The canonical model remains correct.

The problem exists at the **projection layer** between canonical assembly and LLM prompt construction.

---

# 2. Deterministic Synthesis Projection Specification

This section defines a strict projection layer between Agent 11 and Agent 12.

This projection:

* Is deterministic.
* Introduces no inference.
* Introduces no evaluation.
* Preserves traceability.
* Does not modify canonical data.
* Exists only at the prompt-construction boundary.

---

## 2.1 Canonical Fields Retained for Synthesis

The following canonical categories must be retained:

### From `identifiers`

Retain:

* full_name
* declared_preferences (if relevant to interview framing)
* demographic_flags (label-only; no interpretation)

Exclude:

* internal application_id
* date_of_birth (unless explicitly relevant)
* any redundant metadata

---

### From `academic_entries`

Retain per entry:

* academic_level
* board_name
* academic_year
* marking_scheme_raw
* score_raw
* predicted_score_raw (if present)
* subject_entries:

  * subject_name
  * score_raw
  * predicted_score_raw

Exclude:

* entry_id
* grading_mode
* component_tags
* confidence_score

---

### From `test_entries`

Retain:

* test_name
* test_date
* total_score
* percentile
* rank
* result_status
* sectional_scores (label + raw_score only)

Exclude:

* entry_id
* confidence_score

---

### From `essay_entries`

Retain:

* essay_identifier
* raw_text

Exclude:

* word_count
* character_count
* duplication_ratio
* placeholder_flag
* short_response_flag
* confidence_score
* entry_id

---

### From `activity_entries`

Retain:

* category
* activity_name
* level
* duration
* description_raw

Exclude:

* upload_flag
* confidence_score
* entry_id

---

### From `timeline_entries`

Retain:

* year
* event_label
* source_type

Exclude:

* entry_id
* source_reference

---

### From `cross_references`

Retain:

* entity_token
* source_type only (not entry_id)

Exclude:

* source_reference entry_id

---

### From `integrity_report`

Retain:

* anomaly_type
* description (structural only)

Exclude:

* anomaly_id
* severity_level

---

### From `extraction_confidence`

Exclude entirely.

Confidence metadata must never reach the LLM.

---

## 2.2 Structures to Flatten

Flatten:

* subject_entries → inline under academic level
* sectional_scores → inline per test
* cross_references → entity → list of source_types only

Flattening reduces nested JSON overhead.

---

## 2.3 Structures to Compress

### Essays

Apply deterministic compression:

* Remove redundant whitespace.
* Normalize consecutive newlines to one.
* Strip leading/trailing whitespace.

No summarization.
No trimming.
No inference.

---

### Activities

If description_raw exceeds max_char_limit (see Section 4),
truncate deterministically at boundary.

No semantic trimming.
No summarization.

---

## 2.4 Metadata That Must Never Reach LLM

* extraction_confidence
* confidence_score (any agent)
* anomaly severity
* internal UUIDs
* canonical_version
* duplication metrics
* placeholder flags
* grading_mode
* upload_flag
* database identifiers
* pipeline_status

These are structural artifacts.

They are irrelevant to synthesis scope defined in .

---

# 3. Prompt Compaction Strategy

---

## 3.1 Remove JSON

JSON must not be passed verbatim.

Instead:

* Render structured text blocks.
* Use section headers.
* Use bullet lists.
* Avoid repeated key names.

Example format (conceptual):

```
ACADEMIC RECORDS
- Level: Class 12
  Board: CBSE
  Year: 2023
  Score: 92%
  Subjects:
    - Physics: 95
    - Chemistry: 90
```

This removes:

* Quotation marks
* Curly braces
* Repeated key strings
* JSON punctuation overhead

---

## 3.2 Structured Text Rendering Format

Canonical projection format:

1. SNAPSHOT INPUT
2. ACADEMIC ENTRIES
3. TEST ENTRIES
4. ESSAYS
5. ACTIVITIES
6. TIMELINE
7. STRUCTURAL NOTES

Each section rendered once.

No repeated object key names.

---

## 3.3 Semantic Grouping Strategy

Group by:

* Domain
* Chronology
* Explicit categories

Do not group by:

* Confidence
* Severity
* Derived metrics

---

## 3.4 Remove Redundant Repetition

If:

* marking_scheme_raw identical across multiple entries,
  render once at header level.

This is deterministic compression, not inference.

---

## 3.5 Explicit Token Minimization Design

Rules:

* No JSON.
* No UUIDs.
* No redundant field labels.
* No repeated empty fields.
* No null fields rendered.
* No empty arrays rendered.
* No default flags rendered.
* No "confidence_score" printed.

---

# 4. Hard Token Guard Strategy

No second LLM call allowed.

---

## 4.1 Deterministic Token Estimation

Before LLM call:

* Estimate token count via:

  * Character count / 4 heuristic (conservative)
  * Or tokenizer library if available

This is pre-flight only.
No model call.

---

## 4.2 Safe Threshold Policy

Given 4096 context:

Reserve:

* 800 tokens for system + instructions
* 500 tokens for response generation headroom

Input budget:

~2500 tokens max.

Hard stop at 3000 tokens estimated.

---

## 4.3 Priority-Based Truncation Order

If projection exceeds threshold:

Truncate in deterministic order:

1. Activity descriptions (truncate at N chars)
2. Essay raw_text (truncate at N chars)
3. Timeline entries (oldest first)
4. Cross-reference details
5. Subject-level granularity (retain aggregate only)
6. Remove predicted_score_raw
7. Remove percentile
8. Remove rank

Never remove:

* Academic levels
* Test names
* Essay identifiers
* Activity names

---

## 4.4 Maximum Character Rules

Define:

* Essay max_char_per_entry = 2000
* Activity description max_char = 500
* Total essay combined cap = 5000
* Total activity combined cap = 2000

Deterministic hard cut.
No summarization.
No inference.

---

## 4.5 Enforcement Order

Projection builder:

1. Build full projection.
2. Estimate tokens.
3. If > threshold:

   * Apply truncation rules in strict order.
4. Re-estimate.
5. If still > threshold:

   * Continue next truncation layer.
6. If still exceeds threshold after all layers:

   * Abort synthesis with structured error.
   * Do not call LLM.

No second call.
No retry.
No fallback.

---

# 5. Stage-Constrained Implementation Plan (Antigravity)

---

## 5.1 Modify Only Agent 12 Boundary

No changes to:

* Agents 1–11
* Canonical structure
* Policy guard
* Database schema
* Pipeline order
* LLM call count

---

## 5.2 Introduce Projection Builder Layer

Inside `synthesis_agent.py`:

Add deterministic function:

```
build_synthesis_projection(canonical_representation)
```

Steps:

1. Read canonical object.
2. Extract allowed fields only.
3. Flatten structures.
4. Compress text.
5. Remove excluded metadata.
6. Render structured text format.
7. Run token guard.
8. Return final prompt body.

This layer:

* Does not mutate canonical object.
* Does not persist changes.
* Exists only in-memory.

---

## 5.3 Preserve Single LLM Call Rule

LLM invocation remains:

```
generate_synthesis(projection_text)
```

Exactly one call.
No chaining.
No retry.

---

## 5.4 Preserve Canonical Invariants

* canonical_data remains unchanged in DB.
* canonical_version unchanged.
* JSONB storage unchanged.
* No schema change.
* No additional table.

---

## 5.5 Preserve Synchronous Behavior

Projection building:

* Pure Python.
* In-process.
* No async.
* No background tasks.
* No additional services.

Fully compliant with Stage 1 constraints.

---

# 6. Validation Checklist

---

| Constraint                             | Status                                                                    |
| -------------------------------------- | ------------------------------------------------------------------------- |
| Deterministic-first preserved          | Yes — projection is deterministic and does not modify extraction pipeline |
| Single LLM call preserved              | Yes — still exactly one invocation                                        |
| Canonical structure unchanged          | Yes — no schema or model changes                                          |
| No evaluation logic introduced         | Yes — no scoring, ranking, normalization added                            |
| No async introduced                    | Yes — projection runs synchronously                                       |
| No new infrastructure introduced       | Yes — no Redis, no services, no schema changes                            |
| No stage boundary violations           | Yes — modification limited to Agent 12 boundary only                      |
| No additional agents introduced        | Yes                                                                       |
| No summarization passes introduced     | Yes — only truncation, no semantic compression                            |
| No orchestration frameworks introduced | Yes                                                                       |

---

# Final Statement

This mitigation:

* Solves token explosion at the synthesis boundary.
* Preserves all architectural invariants.
* Complies with Stage 1 infrastructure discipline.
* Maintains single-LLM-boundary rule.
* Maintains deterministic-first identity.
* Introduces no evaluation logic.
* Introduces no async behavior.
* Introduces no schema change.
* Introduces no stage boundary violation.

It is a boundary compaction strategy, not an architectural redesign.

END OF DOCUMENT.
