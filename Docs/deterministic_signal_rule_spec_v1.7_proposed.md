# `deterministic_signal_rule_spec_v1.7_proposed.md`

**(Stage 1.7 Proposed Interview-First Deterministic Signal Rules)**

Note: the current implementation now differs from this earlier proposal in a few important ways:

- `9TH` remains in canonical only and is excluded from Call 1 projection and academic deterministic surfacing
- Call 1 `academic_profile` now includes all subjects for `10TH`, `11TH`, and `12TH`
- academic subject observations now cite exact subject names and normalized percentages
- extracurricular and co-curricular handling now prefers non-`Personal` levels, with `Personal` entries requiring duration + position + responsibilities
- leadership eligibility now starts from any filled `position`

---

## 1. Purpose

This document defines a proposed replacement rule set for Agent 12 deterministic signal detection.

The goal of the deterministic layer is **not** to interpret the applicant. It is to **surface mechanically detectable, interviewer-relevant structured patterns** that are:

- easy to miss in raw profile review
- difficult for the LLM to recover reliably from sparse or noisy structured data
- useful as anchors for LLM Call 1
- low-noise and high-precision relative to the current count-style rules

This document is a design and rule-spec artifact only. It does not implement code changes.

---

## 2. Design Intent

### 2.1 What the Deterministic Layer Should Do

The deterministic layer should behave as a **structured-data surfacing engine**.

It should identify patterns that can be detected without NLP or semantic interpretation, including:

- score deltas
- transitions
- within-entry score spread
- duration-backed commitment
- duration-backed leadership depth
- sectional test imbalance

### 2.2 What the Deterministic Layer Should Not Do

The deterministic layer must not:

- extract or compare essay claims
- infer motivation, authenticity, resilience, or character
- interpret free-text descriptions for meaning
- restate obvious counts when those counts do not create interview value
- emit raw totals as signals unless a thresholded pattern is present

Examples of explicitly excluded work:

- essay-to-activity corroboration via claim matching
- keyword-driven semantic pattern detection
- role-title interpretation beyond explicit structured field presence
- activity ranking by inferred prestige or importance

---

## 3. Operating Principles

### 3.1 Precision Bias

The rule set should be **balanced with a bias toward precision**.

It should prefer:

- fewer strong surfaced cues
- stable fixed thresholds
- omission over weak or noisy signals

### 3.2 Output Volume

Output volume should follow these expectations:

- **Typical target:** 3 to 5 deterministic signals
- **Hard ceiling:** 5 or 6 signals
- **Permitted minimum:** 0 signals when the structured profile is too thin

The detector must not force a minimum count by padding with weak signals.

### 3.3 Stable Thresholds

Thresholds should remain fixed in logic/spec for stability.

This proposal does not introduce configurable threshold tuning.

---

## 4. Proposed Signal Set

The current broad count-style signals should be replaced by a smaller set of interview-first structured signals.

### 4.1 Proposed Allowed Signal Types

```text
"academic_trajectory_shift"
"academic_transition_event"
"subject_imbalance"
"leadership_depth"
"sustained_commitment"
"test_section_imbalance"
```

### 4.2 Types to Deprecate

The following current signal types should be removed or phased out from the default rule set:

- `domain_concentration`
- `leadership_presence`
- `activity_volume`
- `test_performance_pattern` when used only to restate raw totals
- `cross_section_pattern`
- `essay_characteristic`

`academic_distribution` should be replaced by more specific academic delta and imbalance signals.

---

## 5. Shared Rule Conventions

### 5.1 Existing Schema Retained

This proposal keeps the existing deterministic signal schema:

```json
{
  "signal_id": "DET-###",
  "signal_type": "string",
  "observation": "string",
  "referenced_entity_ids": ["string"],
  "source_collection": "string"
}
```

No schema expansion is proposed in this phase.

### 5.2 Field Hygiene

All observations must remain:

- factual
- non-evaluative
- mechanically grounded
- free of admissions or quality language

### 5.3 Entity Referencing

Signals may only reference canonical entity IDs already present in the entity map.

Because subject rows do not currently have their own entity IDs, any subject-level deterministic signal must reference the parent academic entry entity ID.

### 5.4 Normalization Rules

Where score comparisons are made:

- compare percentages to percentages
- compare raw section scores only within the same test
- when subject `max_score` differs, normalize by percentage before comparing

---

## 6. Rule Definitions

## 6.1 `academic_trajectory_shift`

### Purpose

Surface meaningful movement between consecutive academic levels.

### Inputs

- `academic_entries[]`
- `score_raw`
- `max_score_raw` if present, otherwise default denominator of 100
- `academic_level`
- `academic_year`

### Detection Rule

For each consecutive pair of academic entries with numeric overall scores:

1. normalize each entry to a percentage
2. compute percentage-point delta
3. emit a signal if the absolute delta is greater than or equal to `7.0` percentage points

### Observation Format

- decline:
  `Performance shifted downward from {LEVEL_A} to {LEVEL_B} by {DELTA} percentage points.`
- improvement:
  `Performance shifted upward from {LEVEL_A} to {LEVEL_B} by {DELTA} percentage points.`

### Referenced Entity IDs

- both academic entry IDs involved in the shift

### Notes

- This is a surfacing rule, not an assessment of whether a shift is good or bad.
- If multiple consecutive shifts qualify, emit up to the strongest two by absolute delta before global ranking is applied.

---

## 6.2 `academic_transition_event`

### Purpose

Surface structural academic context changes that could matter in interview discussion.

### Inputs

- `academic_entries[]`
- `board_name`
- `school_name`
- `academic_level`
- `academic_year`

### Detection Rule

For each consecutive pair of academic entries:

- emit a signal if `board_name` changes
- emit a signal if `school_name` changes

If both change in the same transition window, emit a single combined signal.

### Observation Format

- board change only:
  `Board changed between {LEVEL_A} and {LEVEL_B}.`
- school change only:
  `School changed between {LEVEL_A} and {LEVEL_B}.`
- both:
  `School and board changed between {LEVEL_A} and {LEVEL_B}.`

### Referenced Entity IDs

- both academic entry IDs involved in the transition

### Notes

- This should not be treated as inherently positive or negative.
- This rule exists because transitions are interview-salient and easy to overlook in raw tabular review.

---

## 6.3 `subject_imbalance`

### Purpose

Surface large within-entry spread between the strongest and weakest scored subjects.

### Inputs

- `academic_entries[].subject_entries[]`
- `score_raw`
- `max_score_raw`

### Detection Rule

For each academic entry:

1. collect all subjects with numeric `score_raw`
2. normalize each subject to percentage score
3. require at least `3` scored subjects in the entry
4. compute:
   - highest normalized subject percentage
   - lowest normalized subject percentage
   - spread = highest - lowest
5. emit a signal if spread is greater than or equal to `12.0` percentage points

### Observation Format

`Within {LEVEL}, subject performance shows a {SPREAD}-point spread between the highest and lowest scored subjects.`

### Referenced Entity IDs

- the parent academic entry ID

### Notes

- No hard-coded subject pair logic should be used.
- This is a generic spread detector, not a “Math vs Verbal” rule.
- Subject names may still be included in the observation if that remains non-evaluative and consistent with current schema discipline, but the rule does not require it.

---

## 6.4 `leadership_depth`

### Purpose

Surface leadership entries that have enough structured detail to plausibly support interview exploration.

### Inputs

- `activity_entries[]`
- `activity_type`
- `position_title` or projected `position`
- `duration`
- `level`
- `activity_name` or projected `name`

### Structured Completeness Gate

A leadership entry is signal-eligible only if:

- `activity_type == "leadership"`
- a non-empty structured role field is present
- numeric duration is present
- at least one additional structured field is present:
  - `level`
  - `activity_name`

### Detection Threshold

Emit a signal if:

- duration is greater than or equal to `1.0` year
- and the completeness gate is satisfied

### Observation Format

`A leadership activity includes a structured role with {DURATION}-year duration and supporting activity detail.`

### Referenced Entity IDs

- the leadership activity entry ID

### Notes

- This rule does not interpret the role title semantically.
- It uses role presence and duration as evidence quality, not merit.
- One-year leadership is allowed because structured role plus duration already represents a meaningful surfacing cue when detail is adequate.

---

## 6.5 `sustained_commitment`

### Purpose

Surface long-duration, evidence-rich non-leadership activities that suggest durable engagement.

### Inputs

- `activity_entries[]`
- `activity_type`
- `activity_name`
- `duration`
- `level`
- `position_title` if present

### Structured Completeness Gate

An activity is signal-eligible only if:

- numeric duration is present
- non-empty `activity_name` is present
- and at least one of the following is present:
  - `level`
  - `position_title`

### Detection Threshold

Emit a signal if:

- `activity_type` is not `leadership`
- duration is greater than or equal to `3.0` years
- and the completeness gate is satisfied

### Observation Format

`An activity shows sustained participation over {DURATION} years with structured supporting detail.`

### Referenced Entity IDs

- the activity entry ID

### Notes

- This rule is intended to surface durable engagement, not to claim passion or seriousness.
- Activities lacking structured detail remain visible in the projection but should not create deterministic signals.

---

## 6.6 `test_section_imbalance`

### Purpose

Surface large internal spread across section scores within the same test.

### Inputs

- `test_entries[]`
- `sectional_scores[]`

### Detection Rule

For each test entry:

1. collect all numeric section scores
2. require at least `2` scored sections
3. compute highest and lowest section scores within that test
4. emit a signal if the absolute spread is greater than or equal to `8.0` points

### Observation Format

`Test section scores show an {SPREAD}-point spread between the highest and lowest sections within {TEST_NAME}.`

### Referenced Entity IDs

- the test entry ID

### Notes

- Comparison is allowed because sections within a given test share a comparable scale.
- This rule replaces raw score restatement.
- No cross-test normalization is proposed.

---

## 7. Activity Evidence Richness Model

This section defines how activity completeness should be used without NLP.

### 7.1 Why It Exists

Activities with richer structured fields are better deterministic surfacing candidates because:

- they are less ambiguous
- they are easier to ground
- they provide stronger anchors to LLM Call 1

### 7.2 What Counts as Structured Detail

The following fields count as structured detail:

- `name`
- `position`
- `duration_years`
- `level`

Free-text description should not be required for eligibility and should not be interpreted.

### 7.3 Intended Use

Activity detail should be used in two places only:

1. **eligibility gate**
   Sparse activities do not generate deterministic signals.

2. **candidate ranking**
   If multiple activity-derived signals compete for limited slots, richer entries rank ahead of sparse ones.

This is an evidence-quality mechanism, not a value judgment.

---

## 8. Candidate Generation and Selection Policy

The detector should generate candidate signals first, then select a bounded final set.

### 8.1 Candidate Generation

Run all six rule families independently and collect valid candidates.

### 8.2 De-duplication

Apply the following de-duplication rules:

- if an academic transition already appears in `academic_trajectory_shift` and `academic_transition_event`, both may coexist only if one is a context change and the other is a score shift
- do not emit duplicate `sustained_commitment` signals for multiple near-identical sparse activities
- prefer the richer candidate if two activity candidates are functionally equivalent

### 8.3 Selection Priority

When candidate count exceeds the desired output range, use the following priority order:

1. `academic_trajectory_shift`
2. `academic_transition_event`
3. `subject_imbalance`
4. `leadership_depth`
5. `sustained_commitment`
6. `test_section_imbalance`

### 8.4 Volume Policy

- soft target: 3 to 5
- hard cap: 6
- no minimum enforced

If only 1 or 2 strong signals qualify, return only those.

If no strong signal qualifies, return zero.

---

## 9. Expected Behavior on the Current Example Profile

Using the current projection in `tests/pipeline_stages/14_call_1_projection.json`, likely surfaced candidates would include:

- `academic_trajectory_shift`
  because 9TH to 10TH shows a large percentage movement

- `academic_transition_event`
  because the board changes between 10TH and 11TH

- `subject_imbalance`
  because 9TH includes a visible spread between stronger and weaker subjects

- `sustained_commitment`
  for multi-year structured activities such as Olympiads or Music Piano if the completeness gate is satisfied

- `leadership_depth`
  for School House Captain if role, duration, and supporting structured detail are sufficient

`test_section_imbalance` would likely not fire on the shown JEE percentile spread because the internal section spread appears below the proposed threshold.

This is the intended shape of output: not many signals, but sharper ones.

---

## 10. Non-Goals

This proposal does not attempt to solve:

- essay claim extraction
- activity meaning inference from prose
- semantic similarity across sections
- prestige or competitiveness estimation
- holistic profile interpretation
- signal schema redesign
- threshold configurability

Those belong either to LLM Call 1 or to a later architecture revision.

---

## 11. Recommended Documentation Impact

If this proposal is accepted, the following documents should be updated before implementation:

- `Docs/signal_architecture_spec_v1.7.md`
  - Section 6 deterministic signal examples
  - Section 6.5 allowed signal types

- `Docs/agent_pipeline_spec_v1.7.md`
  - Agent 12 allowed signal types and responsibilities

- `Docs/canonical_projection_spec_v1.7.md`
  - confirm compatibility of projected fields used by these rules

No database schema changes are required.

---

## 12. Decision Log

### D1. Deterministic signals should shift from counts to surfaced structured patterns

- **Alternatives considered:** keep count-based signals and improve prompting
- **Chosen because:** count signals add little interview value and duplicate what raw profile review already shows

### D2. The deterministic layer should avoid NLP-style cross-section claim matching

- **Alternatives considered:** limited keyword matching or essay-claim templates
- **Chosen because:** this work is better handled by LLM Call 1 and increases brittle logic/noise

### D3. Activity-derived signals should use structured completeness gates

- **Alternatives considered:** allow all activities to generate signals equally
- **Chosen because:** sparse activities generate noisy, low-trust deterministic output

### D4. Thresholds should remain fixed

- **Alternatives considered:** configurable thresholds
- **Chosen because:** stable behavior is preferred over tuning flexibility in this phase

### D5. Output volume should be soft-targeted, not forced

- **Alternatives considered:** minimum output count
- **Chosen because:** padding with weak signals is worse than returning fewer strong ones

### D6. Subject imbalance should be generic, not subject-pair-specific

- **Alternatives considered:** hard-coded subject pairs such as math vs verbal or physics vs chemistry
- **Chosen because:** generic spread is more robust and less brittle across profile shapes

### D7. Test surfacing should focus on internal imbalance, not raw score restatement

- **Alternatives considered:** keep current raw test score signal
- **Chosen because:** restating totals adds little signal value for interview preparation

---

## 13. Final Summary

This proposed rule set redefines deterministic signals as a **precision-biased structured surfacing layer**.

The new rules:

- surface deltas, transitions, spread, duration, and imbalance
- avoid semantic interpretation
- prioritize evidence-rich activity entries
- reduce noise from obvious counts and raw restatement
- preserve the LLM's role as the interpretation engine

This gives Call 1 better anchors while keeping the deterministic layer stable, narrow, and auditable.
