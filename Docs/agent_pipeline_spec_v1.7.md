# `agent_pipeline_spec_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. Purpose of This Document

This document defines the logical agent architecture of the AG_InterviewStandardiser system as of Stage 1.7.

It specifies:

- All agent identities (0–16) and their responsibilities
- Input and output contracts per agent
- The deterministic-first boundary and what it requires
- The LLM boundary and what it permits
- The Policy Guard module — its identity, location, and two invocation points
- Non-pipeline components: ROS Projection Layer, ROS Assembly Step
- Confidence discipline
- Prohibited behaviors across all agents

This document governs logical pipeline execution. It does not define:

- Database schema or table structure (governed by `database_schema_v1.7.md`)
- Docker topology or infrastructure (frozen — no changes in Stage 1.7)
- API route structure
- LLM prompt contracts (governed by `llm_synthesis_contract_v1.7.md`)
- Canonical projection field rules (governed by `canonical_projection_spec_v1.7.md`)
- ROS output page structure (governed by `ROS_v1.7.md`)

---

## 2. Codebase Structure

Understanding agent identity requires understanding the directory layout. Not every pipeline component is an agent. Agent numbers correspond to scripts in `app/agents/`. Components in other directories are modules invoked by the orchestrator — they are documented here but do not carry agent numbers.

```
app/
├── agents/
│   ├── orchestrator.py         Agent 0
│   ├── layout_extractor.py     Agent 1
│   ├── section_detector.py     Agent 2
│   ├── personal_extractor.py   Agent 3
│   ├── academic_extractor.py   Agent 4
│   ├── test_extractor.py       Agent 5
│   ├── essay_extractor.py      Agent 6
│   ├── activity_extractor.py   Agent 7
│   ├── cross_section_detector.py  Agent 8
│   ├── timeline_builder.py     Agent 9
│   ├── integrity_analyzer.py   Agent 10
│   ├── assembler.py            Agent 11
│   ├── signal_detector.py      Agent 12
│   ├── projection_builder.py   Agent 13
│   ├── signal_interpreter.py   Agent 14  ← LLM Call 1
│   ├── bundle_constructor.py   Agent 15
│   └── interview_generator.py  Agent 16  ← LLM Call 2
├── policy/
│   ├── guard.py                Policy Guard Module (not a numbered agent)
│   └── config.py               Prohibited terms and validation rules
├── projection/
│   └── ros_projector.py        ROS Projection Layer (not a numbered agent)
├── ros/
│   └── assembler.py            ROS Assembly Step (not a numbered agent)
├── canonical/
│   ├── model.py                Canonical Pydantic models
│   └── version.py              Canonical version tracking
├── api/
│   ├── applications.py         POST /upload, GET /{application_id}
│   └── schemas.py              API Pydantic models
├── auth/
│   ├── security.py             Password hashing, JWT generation/decoding
│   ├── service.py              User registration and authentication logic
│   ├── router.py               /login and /register routes
│   └── schemas.py              Auth Pydantic models
├── models/
│   ├── user.py                 users table
│   ├── application.py          applications table
│   ├── canonical_record.py     canonical_records table
│   └── synthesis_record.py     synthesis_records table
├── utils/
│   ├── layout_normalizer.py    Merges fragmented PDF blocks
│   └── sanitizer.py            JSON serialization utility
└── database.py                 SQLAlchemy engine and session setup
```

---

## 3. Deterministic-First Principle

Agents 1–11 are strictly deterministic. They extract structured data from the application PDF without any LLM involvement.

These agents must:

- Perform structured data extraction only
- Preserve raw field values as found in the source PDF
- Avoid normalization that introduces judgment
- Avoid scoring or ranking of any kind
- Avoid interpretation of applicant data
- Avoid inference beyond what is structurally present in the PDF
- Never invoke an LLM under any circumstances

No part of the deterministic extraction pipeline may depend on LLM output. The canonical representation produced by Agent 11 must be entirely derivable from the PDF alone.

Agent 12 (signal detection) and Agent 13 (projection construction) are also deterministic — they operate on the canonical representation without LLM involvement. Agent 15 (bundle construction) is also deterministic.

The LLM boundary is exactly two agents: Agent 14 (LLM Call 1) and Agent 16 (LLM Call 2).

---

## 4. Agent 0 — Pipeline Orchestrator

**Script:** `app/agents/orchestrator.py`

**Input:** Uploaded PDF path, application ID

**Responsibilities:**

- Execute Agents 1–11 sequentially
- Collect and propagate outputs between agents
- Pass canonical representation to the ROS Projection Layer
- Pass canonical representation to Agent 12
- Invoke the Policy Guard after Agent 14 completes
- Invoke Agent 15 with validated signals
- Invoke Agent 16 with the signal-evidence bundle
- Invoke the Policy Guard after Agent 16 completes
- Invoke the ROS Assembly Step with validated Pages 1–3 and Pages 4–5
- Persist canonical record and ROS v1 artifact
- Abort pipeline on critical agent failure and log failure reason
- Propagate confidence metadata from extraction agents

**Output:**

- Persisted canonical record (`canonical_records`)
- Persisted ROS v1 artifact (`synthesis_records`)

**Constraints:**

- No extraction logic permitted inside the orchestrator
- The orchestrator manages flow only — it does not process or transform data
- On any agent failure or validation failure, the orchestrator aborts and logs; it does not retry

---

## 5. Agents 1–11 — Deterministic Extraction Pipeline

### Agent 1 — Layout Block Extractor

**Script:** `app/agents/layout_extractor.py`

**Input:** Raw PDF file

**Responsibilities:**

- Extract ordered layout blocks from the PDF using PDF parsing libraries
- Preserve page metadata (page number, block position)
- Preserve positional metadata (coordinates, reading order)
- Assign block-level confidence scores based on extraction clarity

**Output:** Ordered layout block list with positional and page metadata

**Prohibited:** Interpretation of block content. Inference of section meaning.

---

### Agent 2 — Section Boundary Detector

**Script:** `app/agents/section_detector.py`

**Input:** Layout blocks from Agent 1

**Responsibilities:**

- Detect logical section boundaries using regex and keyword matching
- Support fuzzy matching for non-standard section header formats
- Preserve unknown section labels rather than discarding them
- Assign confidence per detected boundary

**Output:** Structured section segments with boundary labels and confidence scores

**Prohibited:** Structural inference. Reordering of detected sections.

---

### Agent 3 — Personal Information Extractor

**Script:** `app/agents/personal_extractor.py`

**Input:** Personal section segment from Agent 2

**Responsibilities:**

- Extract applicant identifiers: full name, date of birth, preferred major
- Extract structured `family_background` if present in the section
- Populate `identifiers.family_background` with individual parent fields
- Preserve raw values as extracted — do not normalize or infer
- Do not infer missing family members from partial data

**Output:** `identifiers` block including `family_background`

**Prohibited:** Enrichment of missing fields. Inference of unstated family information. Normalization beyond explicit extraction.

---

### Agent 4 — Academic Records Extractor

**Script:** `app/agents/academic_extractor.py`

**Input:** Academic section segments from Agent 2

**Responsibilities:**

- Extract academic entries as a collection, one entry per grade level
- Preserve grading scheme labels and grading mode exactly as found
- Preserve subject-level score granularity within each entry
- Assign per-entry confidence scores
- Extract institutional affiliation data into `schooling_history[]` separately from performance data
- Keep `academic_entries[]` (performance records) strictly distinct from `schooling_history[]` (institutional records)
- Record predicted scores where present

**Output:**

- `academic_entries[]`
- `schooling_history[]`

**Prohibited:** GPA conversion. Grade normalization. Merging of schooling history and academic performance into a single structure.

---

### Agent 5 — Standardized Test Extractor

**Script:** `app/agents/test_extractor.py`

**Input:** Test section segments from Agent 2

**Responsibilities:**

- Extract test entries as a collection, one entry per test
- Preserve sectional score breakdowns with their original labels
- Preserve percentile values, rank values, and result status where present
- Record awaited or pending results as `result_status: "pending"`
- Assign per-entry confidence scores

**Output:** `test_entries[]`

**Prohibited:** Ranking or comparison of scores across tests. Normalization of scores to a common scale.

---

### Agent 6 — Essay Extractor

**Script:** `app/agents/essay_extractor.py`

**Input:** Essay section segments from Agent 2

**Responsibilities:**

- Extract full essay text for each essay prompt without modification
- Extract the essay prompt or identifier associated with each response
- Compute word count per essay
- Detect placeholder responses (entries where the text is a form placeholder rather than a written response) and set `placeholder_flag: true`
- Detect short responses below a defined minimum threshold and set `short_response_flag: true`
- Assign per-entry confidence scores

**Output:** `essay_entries[]`

**Prohibited:** Summarization of essay content. Commentary on essay quality. Any modification of raw text.

---

### Agent 7 — Activity Extractor

**Script:** `app/agents/activity_extractor.py`

**Input:** Activity section segments from Agent 2

**Responsibilities:**

- Extract activity entries as a collection
- Preserve raw activity descriptions, position titles, duration values, and level designations as found
- Assign `activity_type` classification to each entry using deterministic, rule-based logic

Allowed `activity_type` values:

| Value | Description |
|---|---|
| `"extracurricular"` | Activities outside formal curriculum, not assessed for academic credit |
| `"co_curricular"` | Activities directly connected to academic subjects or competitions |
| `"leadership"` | Entries primarily describing a leadership role or formal position |
| `"other"` | Entries that do not fit any of the above categories |

Classification rules must be:

- Deterministic — same input always produces same classification
- Rule-based — derived from field content only
- Non-evaluative — classification does not imply importance or quality

**Output:** `activity_entries[]` with `activity_type` assigned on every entry

**Prohibited:** Importance weighting of activities. Reclassification of activities by the projection layer. Any inference about the significance of an activity.

---

### Agent 8 — Cross-Section Entity Detector

**Script:** `app/agents/cross_section_detector.py`

**Input:** All canonical collections assembled to this point

**Responsibilities:**

- Detect shared entity tokens appearing across two or more canonical sections
- Build an entity map pairing each shared token with its source section references
- Assign source entry IDs to each cross-reference

**Output:** `cross_references.entity_map`

**Prohibited:** Interpretation of what a shared entity token means. Filtering of tokens by perceived significance.

---

### Agent 9 — Timeline Builder

**Script:** `app/agents/timeline_builder.py`

**Input:** All canonical collections assembled to this point

**Responsibilities:**

- Build a chronological event entry for each datable canonical entry
- Normalize date representations where possible
- Reference the originating `entry_id` on each timeline entry
- Record year as `"Unknown"` where no date can be resolved

**Output:** `timeline_entries[]`

**Prohibited:** Trend analysis or inference about chronological patterns. Dropping entries because they have unknown dates.

---

### Agent 10 — Completeness and Integrity Analyzer

**Script:** `app/agents/integrity_analyzer.py`

**Input:** All canonical collections assembled to this point

**Responsibilities:**

- Detect structural anomalies in the canonical data (e.g. date of birth in the future, academic year sequence gaps)
- Assign a severity level to each detected anomaly
- Produce a structured integrity report

**Output:** `integrity_report` with `anomalies[]`

**Prohibited:** Qualitative evaluation of the applicant. Any language that characterizes the quality of the application.

---

### Agent 11 — Canonical Structure Assembler

**Script:** `app/agents/assembler.py`

**Input:** Outputs from Agents 1–10

**Responsibilities:**

- Consolidate all agent outputs into the complete canonical representation
- Stamp `"canonical_version": "1.1"` on the assembled document
- Preserve array insertion order for all collections — order must not be modified after assembly
- Attach `extraction_confidence` metadata including per-agent confidence scores and aggregate confidence
- Separate `identifiers` from collection data

The assembled canonical representation must contain all of the following:

| Key | Source |
|---|---|
| `canonical_version` | Stamped by Agent 11 |
| `identifiers` | Agent 3 |
| `academic_entries[]` | Agent 4 |
| `schooling_history[]` | Agent 4 |
| `test_entries[]` | Agent 5 |
| `essay_entries[]` | Agent 6 |
| `activity_entries[]` | Agent 7 |
| `cross_references` | Agent 8 |
| `timeline_entries[]` | Agent 9 |
| `integrity_report` | Agent 10 |
| `extraction_confidence` | Agent 11 (compiled from all agents) |

**Agent 11 must not:**

- Produce any ROS output
- Modify canonical data for presentation purposes
- Introduce entity groupings for UI or output layout
- Remove or collapse any collection

The canonical representation produced by Agent 11 is presentation-agnostic. It is optimized for deterministic storage, not for LLM reasoning or output rendering.

---

## 6. ROS Projection Layer

**Script:** `app/projection/ros_projector.py`

**Note:** This is not a numbered agent. It is a deterministic module invoked by the orchestrator after Agent 11 completes.

**Input:** Canonical representation (v1.1)

**Responsibilities:**

- Assign stable entity IDs to all canonical entries (see Section 6.1)
- Construct ROS Page 1 — Background Profile from `identifiers`
- Construct ROS Page 2 — Academic and Engagement Profile from `academic_entries[]`, `test_entries[]`, `activity_entries[]`
- Construct ROS Page 3 — Essays from `essay_entries[]` with deterministic highlight spans
- Preserve canonical array ordering in all projected collections
- Produce the entity ID map for use by downstream signal and LLM stages

**Output:**

- ROS Pages 1–3 (partial ROS v1 artifact)
- Entity ID map

**This layer must not:**

- Invoke an LLM
- Modify the canonical representation
- Collapse or merge canonical collections
- Rewrite or paraphrase canonical field values
- Infer or summarize content

### 6.1 Entity ID Assignment

Entity IDs are assigned by iterating over each canonical collection in array order. The first entry receives index `001`, the second `002`, and so on. Assignment is zero-padded to three digits.

**Prefix mapping:**

| Canonical Collection | Prefix | Example |
|---|---|---|
| `academic_entries[]` | `ACA` | `ACA-001` |
| `test_entries[]` | `TST` | `TST-001` |
| `essay_entries[]` | `ESS` | `ESS-001` |
| `activity_entries[]` | `ACT` | `ACT-001` |
| `schooling_history[]` | `SCH` | `SCH-001` |

**Assignment algorithm:**

```
for i from 1 to len(collection):
    entity_id = PREFIX + "-" + zero_pad(i, 3)
```

**Rules:**

- Entity IDs are derived from canonical array order only
- Entity IDs are regenerated per pipeline run
- Entity IDs do not replace the canonical `entry_id` UUID — both coexist
- Entity IDs must be stable across identical canonical input (same array order → same IDs)
- All entity IDs produced here are the authoritative reference against which the Policy Guard validates LLM entity references
- No downstream component may assign or modify entity IDs

---

## 7. Agent 12 — Deterministic Signal Detector

**Script:** `app/agents/signal_detector.py`

**Input:** Canonical representation (v1.1) from Agent 11

**Responsibilities:**

- Analyze the canonical representation using rule-based logic to derive observable patterns
- Produce a collection of deterministic signals — structured observations about measurable characteristics of the data
- Assign a `signal_id` to each signal in the format `DET-###` (sequentially from `DET-001`)
- Assign a `signal_type` from the allowed type list
- Reference the entity IDs of the canonical entries that produced each signal

**Allowed `signal_type` values:**

| Type | Description |
|---|---|
| `"academic_trajectory_shift"` | Meaningful percentage-point change across consecutive academic levels |
| `"academic_transition_event"` | School or board transition across consecutive academic levels |
| `"subject_imbalance"` | Large spread between the highest and lowest scored subjects within one academic entry |
| `"leadership_depth"` | Leadership entry with structured role, duration, and supporting detail |
| `"sustained_commitment"` | Non-leadership activity showing multi-year participation with structured detail |
| `"test_section_imbalance"` | Large spread between the highest and lowest sections within one test |

**Output schema per signal:**

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

- `signal_id`: Sequential, `DET-001` onward
- `signal_type`: Must be one of the allowed values above
- `observation`: Plain factual statement of what was observed. No evaluative language.
- `referenced_entity_ids`: Must all be valid entity IDs from the entity ID map
- `source_collection`: The canonical collection from which the signal was derived

**Output:** `deterministic_signals[]`

**Agent 12 must not:**

- Interpret the meaning or significance of an observation
- Assess whether an observation is positive or negative
- Use evaluative language in any signal field
- Introduce facts not present in canonical data
- Reference entity IDs not present in the entity ID map
- Invoke an LLM

---

## 8. Agent 13 — Canonical Projection Builder

**Script:** `app/agents/projection_builder.py`

**Input:**

- Canonical representation (v1.1)
- Entity ID map (from ROS Projection Layer)
- Deterministic signal collection (from Agent 12)

**Responsibilities:**

- Construct the Call 1 canonical projection following the field inclusion rules defined in `canonical_projection_spec_v1.7.md`. The projection includes: applicant context (full_name, preferred_major, non-null family background fields), academic_entries (level, school, board, year, grading mode, scores, subjects), test_entries (name, total score, sectional breakdowns), essay_entries (prompt and full text, non-placeholder only), and activity_entries (type, name, position, level, numeric duration). The projection excludes: all entry_id UUIDs, all confidence_score fields, schooling_history, timeline_entries, cross_references, integrity_report, extraction_confidence, predicted scores where null, and all parse artifact field values.
- Apply null field omission — no null values pass through to the projection
- Apply parse artifact detection and exclusion for activity fields
- Attach the entity ID map to the projection
- Attach the deterministic signal collection to the projection
- Run projection verification checks before passing to Agent 14

**Projection verification checks (all must pass):**

- Every included entry has an entity ID
- Every entity ID in the projection body appears in the entity ID map
- No null fields are present anywhere in the projection
- No section array is empty (empty sections are omitted entirely)
- `deterministic_signals` key is present (it may be an empty array)
- No internal metadata fields are present (`confidence_score`, `entry_id`, `placeholder_flag`, `short_response_flag`, `result_status`, `extraction_confidence`)

If any check fails, the pipeline is halted and the failure is logged. The projection is not passed to Agent 14.

**Output:** Call 1 canonical projection (pipeline-ephemeral)

**Agent 13 must not:**

- Modify the canonical representation
- Filter entries by quality, significance, or any value judgment
- Summarize, paraphrase, or condense field values
- Reorder canonical collections
- Introduce derived or computed fields
- Invoke an LLM

---

## 9. Agent 14 — Signal Interpreter (LLM Call 1)

**Script:** `app/agents/signal_interpreter.py`

**Input:**

- Call 1 canonical projection (from Agent 13)
- Deterministic signal collection (embedded in projection)
- Entity ID map (embedded in projection)

**Responsibilities:**

- Make exactly one LLM call per application
- Provide the canonical projection, deterministic signals, and entity ID map to the LLM
- Receive structured interpreted signal output from the LLM
- Pass raw LLM output to the Policy Guard for validation — Agent 14 does not validate the output itself

**LLM Call 1 is the interpretation engine.** Its sole function is to analyze the projected canonical context and deterministic signals to identify higher-level behavioral patterns in the applicant's profile.

**Required output schema from the LLM:**

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

- `signal_id`: Format `INT-###`, numbered sequentially from `INT-001`, unique within the collection
- `title`: Neutral, concise label for the interpreted signal. No evaluative language.
- `description`: Factual behavioral observation grounded in evidence. No evaluative language. No new facts.
- `referenced_entity_ids`: Must reference only entity IDs provided in the projection. No invented IDs.
- `supporting_det_signal_ids`: Must reference only signal IDs from the deterministic signal collection. No invented IDs.

**LLM Call 1 must not produce:**

- Interview questions of any kind
- Narrative summaries
- Thematic groupings
- Evaluative language (prohibited language list in Section 15 of this document)
- New facts not present in canonical data
- Invented entity IDs
- Invented deterministic signal IDs
- Admissions commentary
- Comparative language between applicants
- Predictions or likelihood statements
- Strength or weakness assessments

**Call constraints:**

- Exactly one LLM invocation per application
- No retries on failure
- No recursive prompting
- No chaining of Call 1 output back into Call 1

**Output:** Raw LLM response (passed immediately to Policy Guard — Call 1 invocation)

---

## 10. Policy Guard Module

**Script:** `app/policy/guard.py`
**Configuration:** `app/policy/config.py`

**Note:** The Policy Guard is not a numbered agent. It is a validation module invoked by the orchestrator at two pipeline points: after Agent 14 (Call 1 validation) and after Agent 16 (Call 2 validation). It does not reside in `app/agents/`.

### 10.1 Call 1 Invocation — Signal Validation

**Input:** Raw output from Agent 14 (LLM Call 1)

**Validation rules applied:**

**Structural validation:**
- Response is valid JSON
- `interpreted_signals` key is present
- Each signal contains all required fields: `signal_id`, `title`, `description`, `referenced_entity_ids`, `supporting_det_signal_ids`
- No required field is null or empty

**Signal ID validation:**
- All `signal_id` values follow the `INT-###` format
- No duplicate `signal_id` values exist

**Entity ID validation:**
- Every `referenced_entity_id` in every signal exists in the entity ID map provided to Agent 14
- No invented entity IDs are present

**Deterministic signal ID validation:**
- Every `supporting_det_signal_ids` value exists in the deterministic signal collection provided to Agent 14
- No invented deterministic signal IDs are present

**Language validation:**
- No prohibited term appears in any `title` or `description` field
- Prohibited language list in Section 15 of this document

**On validation success:**
- Produces validated interpreted signal collection
- Produces structured violations log confirming zero violations
- Passes validated signals to Agent 15

**On validation failure:**
- Entire signal collection is rejected — no partial acceptance
- Pipeline is marked as failed
- Failure reason is logged with application ID
- No ROS artifact is produced
- No corrective LLM call is triggered

### 10.2 Call 2 Invocation — Output Validation

**Input:** Raw output from Agent 16 (LLM Call 2)

**Validation rules applied:**

**Structural validation:**
- Response is valid JSON
- `themes` and `question_groups` keys are present
- All required fields per theme and question group are present

**Theme ID validation:**
- All `theme_id` values are unique
- All `question_groups[].theme_id` values reference a defined theme

**Entity ID validation:**
- All `referenced_entity_ids` in themes exist in the entity ID map provided to Agent 16
- No invented entity IDs are present

**Language validation:**
- No prohibited term appears in any theme title, description, group title, or question
- Prohibited language list in Section 15 of this document

**On validation success:**
- Produces validated ROS Pages 4–5 content
- Passes to ROS Assembly Step

**On validation failure:**
- Call 2 output is rejected
- Pipeline is marked as failed
- Failure reason is logged
- No ROS artifact is produced
- No corrective LLM call is triggered

---

## 11. Agent 15 — Signal–Evidence Bundle Constructor

**Script:** `app/agents/bundle_constructor.py`

**Input:**

- Validated interpreted signal collection (from Policy Guard — Call 1 invocation)
- Canonical representation (v1.1)
- Entity ID map

**Responsibilities:**

- For each validated interpreted signal, extract the canonical entries corresponding to its `referenced_entity_ids`
- Apply the same field hygiene rules as the canonical projection layer: exclude confidence scores, exclude internal UUIDs, omit null fields, exclude parse artifacts, preserve entity IDs
- Pair each signal with its extracted evidence entries as a single bundle unit
- Construct the complete signal-evidence bundle

**Output schema:**

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

**Bundle rules:**

- Must not include canonical entries not referenced by any validated signal
- Must not include the full canonical representation
- Must not include deterministic signal metadata beyond `supporting_det_signal_ids` references
- Must not include confidence scores or extraction metadata
- Must not introduce new entity IDs
- Is pipeline-ephemeral — not stored

**Output:** Signal-evidence bundle (pipeline-ephemeral, passed to Agent 16)

**Agent 15 must not:**

- Modify validated signal content
- Introduce new signals or evidence not supported by canonical data
- Invoke an LLM

---

## 12. Agent 16 — Interview Generator (LLM Call 2)

**Script:** `app/agents/interview_generator.py`

**Input:**

- Signal-evidence bundle (from Agent 15)
- Entity ID map

**Responsibilities:**

- Make exactly one LLM call per application
- Provide the signal-evidence bundle and entity ID map to the LLM
- Receive structured themes and question groups output from the LLM
- Pass raw LLM output to the Policy Guard for validation — Agent 16 does not validate the output itself

**LLM Call 2 is the presentation engine.** Its sole function is to transform validated, evidence-grounded signals into structured interview themes and question groups for the interviewer.

**LLM Call 2 does not receive:**

- The full canonical representation
- The raw canonical projection from Agent 13
- Confidence scores or extraction metadata
- The unvalidated output of Agent 14
- Any content from prior applications

**Required output schema from the LLM:**

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
- All `referenced_entity_ids` must exist in the entity ID map provided to Agent 16
- Each `question_groups` entry must reference a valid `theme_id` from the `themes` array
- Questions must be open-ended and exploratory

**LLM Call 2 must not produce:**

- Evaluative language (prohibited language list in Section 15 of this document)
- New facts not present in the signal-evidence bundle
- Invented entity IDs
- Invented theme IDs referenced in question groups but not defined in themes
- Admissions commentary
- Comparative language between applicants
- Predictions or likelihood statements
- Strength or weakness assessments
- Rewritten essay content
- Modified academic records

**Call constraints:**

- Exactly one LLM invocation per application
- No retries on failure
- No recursive prompting
- No chaining of Call 2 output back into Call 1 or Call 2

**Output schema maps directly to ROS:**

| LLM Output Field | ROS Page |
|---|---|
| `themes[]` | `page_4_focus_themes` |
| `question_groups[]` | `page_5_question_groups` |

**Output:** Raw LLM response (passed immediately to Policy Guard — Call 2 invocation)

---

## 13. ROS Assembly Step

**Script:** `app/ros/assembler.py`

**Note:** This is not a numbered agent. It is a deterministic pure-function utility invoked by the orchestrator after both Policy Guard validations succeed.

**Input:**

- ROS Pages 1–3 (from ROS Projection Layer)
- Validated ROS Pages 4–5 content (from Policy Guard — Call 2 invocation)
- `report_metadata`

**Responsibilities:**

- Merge Pages 1–3 and Pages 4–5 into the complete five-page ROS v1 artifact
- Attach `report_metadata`
- Produce the final ROS v1 JSON document

**This step must not:**

- Transform, reformat, or reinterpret Pages 4–5 content
- Modify Pages 1–3 content
- Invoke an LLM

**Output:** Complete ROS v1 artifact (five pages) — passed to the orchestrator for persistence

---

## 14. Confidence Discipline

Confidence scores are tracked at the extraction stage only. They exist in the canonical representation as internal pipeline metadata and are excluded from all projections, bundles, and output artifacts.

- No theme-level confidence is introduced
- No question-group confidence is introduced
- No signal-level confidence is introduced
- No evaluation score of any kind is introduced

Confidence scores serve auditing and debugging purposes within the extraction pipeline. They do not influence LLM reasoning and must not appear in any LLM input.

---

## 15. Prohibited Language

The following terms must not appear in any LLM-generated content at either LLM Call 1 (Agent 14) or LLM Call 2 (Agent 16). The Policy Guard enforces this list at both validation points. Detection of any term below in any field of either call's output is a validation failure.
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

Term matching is case-insensitive and partial-match aware. The authoritative definition of this list including full enforcement rules is in `llm_synthesis_contract_v1.7.md` Section 5.

---

## 16. Prohibited Behaviors — All Agents

The following behaviors are prohibited across all pipeline agents regardless of input or context.

- Introducing academic normalization or GPA conversion
- Introducing strength or weakness flags or language
- Introducing admissions commentary of any kind
- Performing recursive reasoning or chaining LLM calls
- Invoking an LLM from any agent other than Agent 14 and Agent 16
- Modifying the canonical representation after Agent 11 produces it
- Storing chain-of-thought or intermediate reasoning artifacts
- Producing a partial ROS artifact when a pipeline stage has failed
- Retrying a failed LLM call
- Comparing applicants against one another or against any benchmark

---

## 17. Invariant Check

| Invariant | Status |
|---|---|
| Agents 1–11 are strictly deterministic — no LLM involvement | ✅ |
| Agents 12, 13, 15 are deterministic — no LLM involvement | ✅ |
| Exactly two LLM calls per application (Agents 14 and 16) | ✅ |
| Agent 16 receives only the validated signal-evidence bundle | ✅ |
| Policy Guard invoked after both LLM calls — not bypassable | ✅ |
| Signal validation rejects entire collection on any failure | ✅ |
| No partial ROS artifact produced on pipeline failure | ✅ |
| No retry of failed LLM calls | ✅ |
| Canonical representation immutable after Agent 11 | ✅ |
| Projections and bundles are pipeline-ephemeral | ✅ |
| Entity IDs assigned by ROS Projector only — no downstream assignment | ✅ |
| TST prefix used for test entries consistently | ✅ |
| No evaluation logic in any agent | ✅ |
| No recursive reasoning permitted | ✅ |

---

*Agent Pipeline Specification Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*
