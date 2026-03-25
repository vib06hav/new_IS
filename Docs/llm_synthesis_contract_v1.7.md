# `llm_synthesis_contract_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. Purpose of This Document

This document defines the binding contracts governing LLM behavior in the AG_InterviewStandardiser system as of Stage 1.7.

It specifies:

- The LLM boundary principle — what the LLM is and is not permitted to do
- The complete input contract for LLM Call 1 (Signal Interpretation)
- The complete input contract for LLM Call 2 (Interview Generation)
- The required output schema for each call
- The output rules and prohibited behaviors for each call
- The unified prohibited language list governing both calls
- Validation enforcement rules at each call
- Storage and token discipline

This contract is binding. No agent may invoke the LLM outside this contract. No component may pass inputs to the LLM that are not defined here. No component may accept LLM output that has not passed the validation rules defined here.

This document does not define:

- Canonical projection field construction rules (governed by `canonical_projection_spec_v1.7.md`)
- Agent responsibilities and script locations (governed by `agent_pipeline_spec_v1.7.md`)
- ROS page structure and schemas (governed by `ROS_v1.7.md`)
- Database schema (governed by `database_schema_v1.7.md`)

---

## 2. LLM Boundary Principle

### 2.1 What the LLM Is Used For

The LLM is used for exactly two reasoning tasks in Stage 1.7:

**Call 1 — Signal Interpretation:** Analyzing a curated projection of canonical applicant data together with deterministic observational signals to identify higher-level behavioral patterns. This is an analysis task. The LLM produces structured interpreted signals — it does not produce any interviewer-facing output.

**Call 2 — Interview Generation:** Transforming validated themes and grouped signal-evidence packets into structured interview question groups for use by human interviewers. This is a communication task. The LLM produces ROS Page 5 content, while ROS Page 4 comes from validated Call 1 themes.

### 2.2 What the LLM Is Not Used For

The LLM is not used for:

- Scoring applicants
- Ranking applicants
- Evaluating applicant quality
- Predicting admissions outcomes
- Normalizing academic grades
- Rewriting or paraphrasing essay content
- Modifying canonical data of any kind
- Validating its own output
- Summarizing canonical data as a pre-processing step
- Any task not explicitly assigned to Call 1 or Call 2

### 2.3 Call Count Invariant

Exactly two LLM calls are made per application. No more, no fewer.

- No retries on failure
- No fallback models
- No secondary or refinement passes
- No recursive prompting
- No chaining of LLM output back into any LLM call

This invariant is absolute. It cannot be relaxed for any application under any circumstance.

---

## 3. Call 1 Contract — Signal Interpretation

### 3.1 Purpose

LLM Call 1 is the interpretation engine. It receives a curated view of the applicant's canonical data and a collection of deterministic observational signals. Its sole responsibility is to identify higher-level behavioral patterns — interpreted signals — that are grounded in the canonical evidence.

Call 1 performs analysis only. It produces no interview questions, no question groups, and no narrative summaries.

### 3.2 Input to Call 1

LLM Call 1 receives the Call 1 canonical projection constructed by Agent 13. The projection contains the following:

**Applicant context:**
- `full_name`
- `preferred_major`
- `family_background` — the following fields included for both father and mother objects where non-null: `name`, `education`, `field_of_employment`, `organization`, `designation`

**Academic profile** — one entry per grade level, containing:
- Assigned entity ID (format `ACA-###`)
- Grade level, school name, board name, academic year
- Grading mode and overall score
- Subject-level entries with subject name and score

**Test profile** — one entry per test, containing:
- Assigned entity ID (format `TST-###`)
- Test name, total score
- Sectional score breakdowns with labels

**Essay profile** — one entry per essay, containing:
- Assigned entity ID (format `ESS-###`)
- Essay prompt
- Full essay text (unmodified)

**Activity profile** — one entry per activity, containing:
- Assigned entity ID (format `ACT-###`)
- Activity type (`"extracurricular"`, `"co_curricular"`, `"leadership"`, or `"other"`)
- Activity name and/or position title (where non-null and non-artifact)
- Level and duration (where non-null and non-artifact)

**Entity ID map** — a flat lookup of all assigned entity IDs with descriptors:
```json
[
  { "entity_id": "ACA-001", "collection": "academic_entries", "descriptor": "string" },
  { "entity_id": "TST-001", "collection": "test_entries", "descriptor": "string" },
  { "entity_id": "ESS-001", "collection": "essay_entries", "descriptor": "string" },
  { "entity_id": "ACT-001", "collection": "activity_entries", "descriptor": "string" }
]
```

**Deterministic signals** — the complete collection produced by Agent 12:
```json
[
  {
    "signal_id": "DET-###",
    "signal_type": "string",
    "observation": "string",
    "referenced_entity_ids": ["string"],
    "source_collection": "string"
  }
]
```

**LLM Call 1 does not receive:**

- Internal canonical UUIDs (`entry_id` values)
- Confidence scores of any kind
- Integrity report or anomaly data
- Extraction confidence metadata
- `schooling_history[]` (redundant with academic entries)
- `timeline_entries[]` (contains parse artifacts, redundant)
- `cross_references.entity_map` (word-level token noise)
- Raw canonical JSONB
- Output from any prior LLM call
- Content from any other application

### 3.3 Required Output Schema — Call 1

LLM Call 1 must return a strictly valid JSON object with the following structure:

```json
{
  "interpreted_signals": [
    {
      "signal_id": "INT-###",
      "theme_id": "THEME-###",
      "title": "string",
      "essay_claim": "string",
      "evidence_observation": "string",
      "tension_or_coherence": "string",
      "interview_hook": "string",
      "referenced_entity_ids": ["string"],
      "supporting_det_signal_ids": ["string"]
    }
  ],
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "string",
      "description": "string",
      "referenced_entity_ids": ["string"]
    }
  ]
}
```

**Field rules:**

| Field | Rule |
|---|---|
| `signal_id` | Format `INT-###`. Numbered sequentially from `INT-001`. Unique within the collection. No duplicates. |
| `theme_id` | Format `THEME-###`. Must reference a theme defined in the same Call 1 response. |
| `title` | Neutral, concise label for the interpreted signal. Maximum one sentence. No evaluative language. No prohibited terms. |
| `essay_claim` | Specific claim or implication from the essay that the signal is testing. |
| `evidence_observation` | Factual observation grounded in canonical evidence. No evaluative language. No new facts not present in the canonical projection. |
| `tension_or_coherence` | Neutral statement of whether the essay claim and evidence align or conflict. |
| `interview_hook` | The uncertainty an interviewer needs to resolve. |
| `referenced_entity_ids` | Must reference only entity IDs present in the entity ID map provided. No invented entity IDs. At least one reference required per signal. |
| `supporting_det_signal_ids` | Must reference only `signal_id` values from the deterministic signal collection provided. No invented deterministic signal IDs. At least one reference required per signal. |

**Field rules — themes:**

| Field | Rule |
|---|---|
| `theme_id` | Format `THEME-###`. Numbered sequentially. Unique within the collection. |
| `title` | Neutral, concise theme label. No evaluative language. No prohibited terms. |
| `description` | Brief neutral description of what the interviewer is trying to understand through the theme. |
| `referenced_entity_ids` | Must reference only entity IDs present in the entity ID map provided. No invented entity IDs. At least one reference required per theme. |

### 3.4 Output Rules — Call 1

**Each interpreted signal must:**

- Represent a behavioral pattern observable from canonical evidence
- Reference at least one valid entity ID
- Reference at least one deterministic signal that anchors it
- Use language that describes behavior without evaluating it

**Each interpreted signal must not:**

- Contain interview questions or question groups of any kind
- Contain narrative summaries or prose portraits of the applicant
- Introduce facts not present in the canonical projection
- Reference entity IDs not provided in the entity ID map
- Reference deterministic signal IDs not provided in the input
- Use any term from the prohibited language list (Section 5)
- Assess whether a pattern is positive or negative
- Compare the applicant to any benchmark or other applicant
- Make predictions or likelihood statements
- Reclassify activity types assigned by Agent 7
- Contain admissions commentary of any kind

### 3.5 Call 1 Constraints

- Exactly one LLM invocation per application
- No retries on output failure
- No fallback to any alternative synthesis approach
- No recursive prompting
- Call 1 output must not be fed back into Call 1
- Call 1 raw output must not be passed directly to Call 2 — it must pass through Policy Guard validation and bundle construction first

---

## 4. Call 2 Contract — Interview Generation

### 4.1 Purpose

LLM Call 2 is the presentation engine. It receives the validated theme-first signal-evidence bundle — validated themes together with grouped supporting signals and evidence. Its sole responsibility is to transform that input into structured interview question groups for use by interviewers.

Because interpretation has already occurred in Call 1, Call 2 focuses entirely on communication. It does not re-analyze the applicant's profile. It works from what the validated signals have already identified.

### 4.2 Input to Call 2

LLM Call 2 receives the theme-first signal-evidence bundle constructed by Agent 15. The bundle contains:

**Validated themes** — the exact Call 1 themes that must be used for question generation.

**Theme signal-evidence groups** — one group per validated theme:
```json
{
  "application_id": "string",
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "string",
      "description": "string",
      "referenced_entity_ids": ["string"]
    }
  ],
  "theme_signal_evidence_groups": [
    {
      "theme": {
        "theme_id": "THEME-###",
        "title": "string",
        "description": "string",
        "referenced_entity_ids": ["string"]
      },
      "signal_evidence_pairs": [
        {
          "signal": {
            "signal_id": "INT-###",
            "theme_id": "THEME-###",
            "title": "string",
            "essay_claim": "string",
            "evidence_observation": "string",
            "tension_or_coherence": "string",
            "interview_hook": "string",
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
  ]
}
```

**Entity ID map** — the same entity ID map provided to Call 1, used for reference validation.

**LLM Call 2 does not receive:**

- The full canonical representation
- The canonical projection passed to Call 1
- Confidence scores or extraction metadata
- The raw unvalidated output of Call 1
- Deterministic signal collection directly
- `schooling_history[]`, `timeline_entries[]`, or `cross_references`
- Internal canonical UUIDs
- Content from any other application

### 4.3 Required Output Schema — Call 2

LLM Call 2 must return a strictly valid JSON object with the following structure:

```json
{
  "question_groups": [
    {
      "theme_id": "THEME-###",
      "group_title": "string",
      "questions": ["string"]
    }
  ]
}
```

**Field rules — question groups:**

| Field | Rule |
|---|---|
| `theme_id` | Must reference a `theme_id` supplied in the Call 2 input bundle. No invented theme IDs. |
| `group_title` | Neutral label for the question group. No evaluative language. |
| `questions` | Array of open-ended, exploratory questions. Each question must be non-evaluative. No empty array. |

**Output mapping to ROS:**

| Call 2 Output Field | ROS Page |
|---|---|
| `question_groups[]` | `page_5_question_groups` |

The Call 2 output is placed into the ROS artifact by the ROS Assembly Step without modification, reformatting, or reinterpretation. The schema defined here is therefore identical to ROS Page 5. ROS Page 4 is assembled from validated Call 1 themes.

### 4.4 Output Rules — Call 2

**Each question group must:**

- Reference a valid `theme_id` from the supplied bundle
- Have a neutral group title
- Contain at least one question
- Appear exactly once per supplied theme

**Each question must:**

- Be open-ended and exploratory
- Invite the applicant to describe, explain, or reflect
- Avoid evaluative framing
- Avoid accusatory tone
- Avoid assumptions not supported by the signal-evidence bundle
- Not demand justification of grades or scores
- Not imply deficiency or inadequacy
- Not contain comparative language
- Not introduce new facts about the applicant
- Not use any term from the prohibited language list (Section 5)

### 4.5 Call 2 Constraints

- Exactly one LLM invocation per application
- No retries on output failure
- No fallback to any alternative synthesis approach
- No recursive prompting
- Call 2 output must not be fed back into Call 2 or into Call 1

---

## 5. Prohibited Language

The following terms must not appear in any LLM-generated content at either Call 1 or Call 2. This list is the authoritative prohibited term reference for the system. All other documents that reference prohibited language point to this section.

The Policy Guard enforces this list against all LLM output. Detection of any term from this list in any field of either call's output is a validation failure.

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

**Rules governing this list:**

- Term matching is case-insensitive
- Partial matches count — a term embedded within a longer word is a violation (e.g. "weakness" within "key weakness areas")
- The list may be extended in future stages via a formal stage boundary decision
- The list may not be shortened without a formal stage boundary decision
- No LLM prompt instruction may override or exempt any term on this list
- No application-specific configuration may override this list

---

## 6. Validation Enforcement

### 6.1 Call 1 Validation — Policy Guard Invocation

After Agent 14 returns the LLM response, the Policy Guard (`app/policy/guard.py`) validates it before any downstream step proceeds.

**Structural validation:**
- Response is valid JSON
- `interpreted_signals` key is present and is an array
- Each signal contains all required fields: `signal_id`, `title`, `description`, `referenced_entity_ids`, `supporting_det_signal_ids`
- No required field is null or empty

**Signal ID validation:**
- All `signal_id` values follow the `INT-###` format
- No duplicate `signal_id` values exist within the collection

**Entity ID validation:**
- Every `referenced_entity_id` in every signal exists in the entity ID map provided to Call 1
- No invented entity IDs are present

**Deterministic signal ID validation:**
- Every value in `supporting_det_signal_ids` exists in the deterministic signal collection provided to Call 1
- No invented deterministic signal IDs are present

**Language validation:**
- No term from Section 5 appears in any `title` or `description` field
- Matching is case-insensitive and partial-match aware

**On validation success:**
- Validated interpreted signal collection is passed to Agent 15
- Violations log records zero violations

**On validation failure:**
- The entire interpreted signal collection is rejected — no partial acceptance
- No corrective LLM call is triggered
- The pipeline is marked as failed for this application
- The failure reason and failing field(s) are logged with the application ID
- No ROS artifact is produced

### 6.2 Call 2 Validation — Policy Guard Invocation

After Agent 16 returns the LLM response, the Policy Guard validates it before ROS assembly.

**Structural validation:**
- Response is valid JSON
- `question_groups` key is present and is an array
- Each question group contains all required fields: `theme_id`, `group_title`, `questions`
- `questions` is a non-empty array of strings

**Theme ID validation:**
- All `question_groups[].theme_id` values reference a `theme_id` supplied in the Call 2 input bundle
- Exactly one question group must be present for every supplied theme
- No duplicate or invented theme IDs are permitted in `question_groups`

**Language validation:**
- No term from Section 5 appears in any theme title, theme description, group title, or question
- Matching is case-insensitive and partial-match aware

**On validation success:**
- Validated question groups are passed to the ROS Assembly Step together with validated Call 1 themes
- Violations log records zero violations

**On validation failure:**
- The Call 2 output is rejected in its entirety
- No corrective LLM call is triggered
- The pipeline is marked as failed for this application
- The failure reason and failing field(s) are logged with the application ID
- No ROS artifact is produced

---

## 7. Deterministic Boundary Preservation

Neither LLM call may violate the canonical–presentation separation or alter any deterministic pipeline output.

**Neither call may:**

- Modify ROS Pages 1–3 produced by the deterministic ROS projection layer
- Rewrite, paraphrase, or summarize essay text
- Collapse or merge academic entries
- Merge activity entries
- Remove or omit canonical entries from consideration
- Reorder canonical data
- Reclassify activity types assigned by Agent 7
- Alter family background data
- Alter schooling history data
- Modify test score values or sectional breakdowns
- Introduce academic normalization or grade conversion

**Call 1 specifically may not** produce any output that resembles interviewer-facing question content — no question groups, no interview guidance prose, and no interview questions of any kind.

**Call 2 specifically may not** re-analyze the canonical projection — it works only from the signal-evidence bundle. It may not introduce reasoning that bypasses the interpreted signals.

---

## 8. Token Discipline

The projection layer (Agent 13) is responsible for ensuring that the Call 1 projection remains within the model's context window. This is achieved through the field inclusion rules defined in `canonical_projection_spec_v1.7.md` — removing internal metadata, excluding redundant sections, and omitting null fields.

The signal-evidence bundle (Agent 15) is structurally scoped to the validated signals only. Because the bundle contains only the canonical entries referenced by validated signals — not the full canonical dataset — Call 2 token overhead is consistently lower than Call 1.

**Neither call permits:**

- A summarization pre-pass to reduce token count
- A multi-stage reduction of input content
- Truncation of essay text or canonical field values
- Any LLM involvement in preparing its own input

If a projection exceeds model context limits due to an unusually large application, the pipeline must fail cleanly with a logged reason. No silent truncation is permitted.

---

## 9. Storage Discipline

**Call 1 output (interpreted signals)** is pipeline-ephemeral by default. It is not stored in a dedicated table or column. If signal data is required for auditability or debugging, it may be embedded as a structured key within `synthesis_records.synthesis_output` alongside the ROS artifact. This requires no schema change. This decision must be made explicitly before Stage 1.7 goes to production and must not be left ambiguous.

**Call 2 output (question groups)** is merged into the final ROS v1 artifact by the ROS Assembly Step and persisted in `synthesis_records.synthesis_output` as part of the complete five-page ROS JSON. Validated Call 1 themes are persisted alongside it in the assembled ROS artifact.

**Neither call permits:**

- Storage of intermediate chain-of-thought reasoning
- Storage of raw LLM prompt text in the synthesis record
- Storage of unvalidated LLM output

The canonical representation remains stored separately in `canonical_records` and is not modified by either call.

---

## 10. Two-Call Invariant Check

| Invariant | Status |
|---|---|
| Exactly two LLM calls per application | ✅ |
| No retries on failure for either call | ✅ |
| No recursive prompting at either call | ✅ |
| Call 1 performs interpretation only — no interview output | ✅ |
| Call 2 performs generation only — no profile analysis | ✅ |
| Call 2 receives only validated signal-evidence bundle | ✅ |
| Call 2 does not receive raw canonical data | ✅ |
| Call 2 does not receive raw Call 1 output | ✅ |
| Prohibited language list governs both calls | ✅ |
| Policy Guard invoked after both calls — not bypassable | ✅ |
| Validation failure at either call aborts pipeline entirely | ✅ |
| No partial ROS artifact produced on failure | ✅ |
| Canonical representation unchanged by both calls | ✅ |
| Activity type classifications not overridden by either call | ✅ |
| No chain-of-thought storage permitted | ✅ |

---

*LLM Synthesis Contract Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*
