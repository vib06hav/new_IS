# `llm_synthesis_contract_v1.5.md`

*(Canonical v1.1 Aligned — Audit Flags Resolved)*

---

# `llm_synthesis_contract_v1.5.md`

**(Stage 1.5 — Structured Thematic Synthesis for ROS v1, Canonical v1.1 Aligned)**

---

## 1. Purpose of This Document

This document defines:

* The single permitted LLM invocation
* The input structure provided to the model
* The required output structure
* The prohibitions governing model behavior
* Validation and enforcement rules

This contract is binding.

No agent may invoke the LLM outside this contract.

---

## 2. LLM Boundary Principle

The LLM is used for:

* Thematic pattern abstraction
* Structured grouping of discussion areas
* Generating interview questions aligned to themes

The LLM is not used for:

* Scoring
* Ranking
* Evaluation
* Prediction
* Academic normalization
* Essay rewriting
* Narrative rewriting
* Canonical modification

The LLM performs exactly one call per application.

No retries.
No fallback models.
No secondary passes.
No recursive prompting.

This invariant is absolute.

---

## 3. Input to LLM

The LLM receives a projection-cleaned canonical representation (v1.1).

The input includes the following deterministic collections:

* `academic_entries[]`
* `schooling_history[]`
* `test_entries[]`
* `essay_entries[]`
* `activity_entries[]` (including `activity_type`)
* `identifiers.family_background`

The LLM does not receive:

* Confidence scores
* Integrity severity levels
* Internal extraction metadata
* Raw layout blocks
* Raw PDF text

### 3.1 Deterministic Ordering

All collections are passed:

* In canonical array order
* Without sorting
* Without collapsing
* Without normalization

Entity IDs are derived deterministically from canonical array order prior to LLM invocation.

The LLM must reference only the provided `entity_id` values.

The LLM must not invent new entity IDs.

---

## 4. Output Structure (Stage 1.5 — ROS v1)

The LLM must return strictly valid JSON with the following structure:

```json id="c8g7pv"
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

This corresponds to:

* ROS Page 4 — Focus Themes
* ROS Page 5 — Question Groups

Full ROS structure is defined in `ROSv1.md`.

The LLM generates only thematic structure.

It does not generate Pages 1–3.

---

## 5. Required Output Rules

### 5.1 Theme Rules

Each theme must:

* Have a unique `theme_id`
* Have a neutral `title`
* Have a neutral `description`
* Reference at least one valid `entity_id`

Each `referenced_entity_id` must:

* Exist in canonical
* Correspond to a real extracted entity
* Not be invented
* Not reference non-existent entries

Themes must not:

* Rank the applicant
* Indicate strength or weakness
* Predict outcomes
* Provide advice
* Introduce new facts
* Reinterpret grades
* Reclassify activities

The LLM must respect the canonical `activity_type` classification.

---

### 5.2 Question Group Rules

Each question group must:

* Reference a valid `theme_id`
* Have a neutral `group_title`
* Contain an array of open-ended questions

Questions must:

* Be exploratory
* Avoid evaluative framing
* Avoid accusatory tone
* Avoid assumptions not present in canonical

Questions must not:

* Demand justification of grades
* Imply deficiency
* Predict failure
* Contain comparative language
* Introduce new applicant facts

---

## 6. Prohibited Language

The LLM must not generate:

* "Strength"
* "Weakness"
* "Outstanding"
* "Deficiency"
* "Below average"
* "Underperformance"
* "High potential"
* "Top candidate"
* "Risk factor"
* "Admit"
* "Reject"
* "Likelihood"

No admissions commentary is permitted.

---

## 7. Validation Enforcement

After LLM response, Agent 13 must validate:

1. JSON structure matches contract
2. All `theme_id` values are unique
3. All `referenced_entity_ids` exist in deterministic entity map
4. All `question_groups.theme_id` values exist in themes
5. No invented entity IDs
6. No prohibited language detected

If validation fails:

* The response is rejected
* No second LLM call is triggered
* Error is logged
* Application is marked failed

No corrective LLM pass allowed.

---

## 8. Deterministic Boundary Preservation

The LLM must not:

* Modify deterministic Pages 1–3
* Rewrite essays
* Collapse academic entries
* Merge activities
* Remove entries
* Reorder canonical data
* Reclassify activity types
* Alter family_background data
* Alter schooling_history data

The LLM produces thematic abstraction only.

---

## 9. Token Discipline

Projection layer must:

* Remove unnecessary metadata
* Flatten nested JSON where possible
* Ensure token count remains within model limits

LLM input size must not exceed model context window.

No summarization pre-pass allowed.
No multi-stage reduction allowed.

---

## 10. Single-Call Invariant

Exactly one LLM invocation per application.

This invariant is absolute.

Stage 1.5 does not introduce:

* Multi-step reasoning
* Theme refinement pass
* Question refinement pass
* Secondary model usage

---

## 11. Storage Discipline

The LLM output is:

* Merged with deterministic ROS Pages 1–3
* Stored as full ROS v1 JSON
* Persisted inside `synthesis_records.synthesis_output`

No intermediate chain-of-thought storage permitted.

Canonical remains stored separately in `canonical_records`.

---

## 12. Stage 1.5 Invariants

| Invariant                      | Status |
| ------------------------------ | ------ |
| Single LLM call preserved      | ✅      |
| No recursive reasoning         | ✅      |
| No evaluation logic introduced | ✅      |
| Canonical remains unchanged    | ✅      |
| No async introduced            | ✅      |
| No infra change required       | ✅      |
| ROS v1 contract enforced       | ✅      |
| Deterministic entity_id usage  | ✅      |

---

This version:

* Resolves audit input mismatch (schooling_history now explicitly passed)
* Resolves activity classification ambiguity (LLM cannot reclassify)
* Locks entity_id deterministic referencing
* Keeps single-call invariant airtight
* Keeps canonical–presentation separation intact
* Keeps infra frozen
* Keeps schema untouched

---

End of Document. 

---
