# `stage_1_7_migration_plan.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis: Concrete Migration Governance Plan)**

---

## Preamble

This document governs the concrete transition from Stage 1.5 (ROS v1 Integrated Structured Output) to Stage 1.7 (Two-Stage Signal-Guided LLM Synthesis). It is a logical-layer migration governance document only. It does not generate code, SQL, Dockerfiles, docker-compose YAML, Alembic scripts, or Python classes. All implementation artifacts produced under this plan must comply with the governing specification documents listed below. In cases of conflict between any section of this document and `architecture_lock_v1.7.md`, `architecture_lock_v1.7.md` prevails without exception.

### Governing Documents

| Document | Role |
|---|---|
| `architecture_lock_v1.7.md` | Supreme constraint authority. Prevails over all other documents in conflict. |
| `system_overview_v1.7.md` | Architectural identity, pipeline flow, and system boundaries for Stage 1.7. |
| `agent_pipeline_spec_v1.7.md` | Complete logical pipeline definition. All agent responsibilities, inputs, outputs, and prohibited behaviors. |
| `signal_architecture_spec_v1.7.md` | Two-stage synthesis architecture. Signal schemas, validation rules, bundle structure, two-call invariants. |
| `canonical_projection_spec_v1.7.md` | Canonical projection field inclusion and exclusion rules. Parse artifact detection. Projection lifecycle. |
| `llm_synthesis_contract_v1.7.md` | Binding LLM behavioral contracts for both calls. Prohibited language list. Validation enforcement rules. |
| `canonical_model_philosophy_v1.7.md` | Canonical representation invariants. Complete v1.1 structural definition. |
| `ROS_v1.7.md` | Report Output Specification. Complete five-page schema. All projection rules and field mappings. |
| `database_schema_v1.7.md` | PostgreSQL schema definition. JSONB governance. Signal storage decision. |

---

## 1. Migration Purpose

### 1.1 What Stage 1.7 Introduces

Stage 1.7 replaces the single-call LLM synthesis model with a two-stage signal-guided architecture. All changes are logical-layer only. No infrastructure, schema, or deployment topology changes are introduced.

**Two-Stage Signal-Guided Synthesis.** The existing `synthesis_agent.py` (Agent 12) is retired. In its place, five new agents implement the full signal pipeline: deterministic signal detection, canonical projection construction, LLM Call 1 (signal interpretation), signal-evidence bundle construction, and LLM Call 2 (interview generation). The pipeline now makes exactly two bounded LLM calls per application instead of one.

**Deterministic Signal Detection (Agent 12).** A new agent (`signal_detector.py`) analyzes the assembled canonical representation using rule-based logic and derives a structured collection of deterministic signals — observable patterns in the canonical data that anchor LLM reasoning. No LLM is involved.

**Canonical Projection Construction (Agent 13).** A new agent (`projection_builder.py`) constructs a curated, cleaned view of the canonical representation for LLM Call 1. It applies null omission, parse artifact detection, and field inclusion rules per `canonical_projection_spec_v1.7.md`. It attaches the deterministic signal collection and entity ID map to produce the complete Call 1 projection.

**LLM Call 1 — Signal Interpretation (Agent 14).** A new agent (`signal_interpreter.py`) receives the Call 1 projection and makes exactly one LLM call. The LLM produces a structured collection of interpreted signals — higher-level behavioral inferences grounded in canonical evidence. This call performs analysis only. It does not produce interview questions or themes.

**Policy Guard — Call 1 Invocation.** The existing `policy/guard.py` is extended with a new `validate_signals()` function that validates the Call 1 output: schema conformance, signal ID format, entity ID references, deterministic signal ID references, and prohibited language. A new function is added alongside the existing validation logic — the existing function is not modified.

**Signal–Evidence Bundle Construction (Agent 15).** A new agent (`bundle_constructor.py`) receives the validated interpreted signal collection and pairs each signal with its supporting canonical evidence entries. The bundle is the sole input to LLM Call 2. It is constructed deterministically and contains no confidence scores, no internal UUIDs, and no content not referenced by validated signals.

**LLM Call 2 — Interview Generation (Agent 16).** A new agent (`interview_generator.py`) receives the signal-evidence bundle and makes exactly one LLM call. The LLM produces structured interview themes and question groups — the same output schema as the retired `synthesis_agent.py`. This call performs communication only. It does not re-analyze the applicant's profile.

**Policy Guard — Call 2 Invocation.** The existing `validate_themes()` function in `policy/guard.py` (previously the single invocation point) continues to handle Call 2 output validation. The prohibited language list is updated to the full 21-term list defined in `llm_synthesis_contract_v1.7.md` Section 5.

**`llm/client.py` Refactor.** The existing `generate_synthesis()` function is replaced with a generic `generate(messages)` function. Prompt construction moves to each calling agent. The client becomes a thin synchronous HTTP wrapper with no knowledge of call purpose or output schema.

**Signal Storage.** Interpreted signals are persisted alongside the ROS artifact. The `synthesis_output` JSONB column stores a `signal_data` key containing both the deterministic signal collection and the validated interpreted signal collection. No schema change is required. This decision enables debugging and auditability during Stage 1.7 production rollout and can be made ephemeral in a future stage.

**Orchestrator Rewiring (Agent 0).** `orchestrator.py` is updated to execute the full Stage 1.7 pipeline sequence. All new agents are wired in correct order. The retirement of `synthesis_agent.py` is reflected in the orchestration flow.

### 1.2 What Does NOT Change

The following elements are explicitly unchanged in Stage 1.7:

- Database schema: no new tables, no new columns, no new constraints, no new indexes, no Alembic migration
- Container topology: exactly two containers (API + PostgreSQL). No new containers
- Environment variables: the complete set of variables from `env_config_spec.md` is unchanged. No new variables
- `canonical/model.py`: Pydantic model definitions are unchanged. Canonical version remains `"1.1"`
- `canonical/version.py`: `CANONICAL_VERSION` constant remains `"1.1"`. No version bump
- `database.py`: connection binding, pool configuration, synchronous driver unchanged
- `auth/router.py` and `api/applications.py`: route handlers unchanged
- `projection/ros_projector.py`: deterministic ROS projection layer and entity ID assignment logic unchanged
- `ros/assembler.py`: ROS assembly step unchanged
- Agents 1–11: all responsibilities, input/output contracts, and prohibited behaviors are unchanged
- The synchronous, sequential, single-request-lifecycle execution model
- ROS v1 output schema: all five pages, all field names, `report_version: "ROS_v1"`
- Alembic revision history: no new revision is added

### 1.3 Why Changes Are Logical-Layer Only

Each change introduced by Stage 1.7 affects only the internal processing logic of the application module. The new agents are Python modules inside the existing `app/agents/` directory. The Policy Guard extension adds a function to an existing module. The `llm/client.py` refactor changes an internal function signature without changing the HTTP mechanism, endpoint, or configuration. The signal-evidence bundle is an in-memory Python object constructed and consumed within a single request lifecycle.

No change affects how the system is packaged, deployed, configured, or persisted at the infrastructure level. The addition of `signal_data` to `synthesis_output` is a JSONB content evolution — the column type, column name, and table structure are unchanged.

---

## 2. Pre-Migration State Confirmation

Before any implementation begins, confirm that the Stage 1.5 system is in a known good state. This section must be completed and all checks must pass before Phase A begins.

**2.1 End-to-End Pipeline Integrity**
- A complete pipeline run with a real PDF produces a `synthesis_records` row with `synthesis_output` containing all six top-level ROS v1 keys
- `report_metadata.report_version` equals `"ROS_v1"`
- `synthesis_records.policy_passed` is `true` for a valid application

**2.2 Schema State**
- `alembic current` shows the Stage 1 head revision unchanged
- Exactly four tables exist: `users`, `applications`, `canonical_records`, `synthesis_records`
- No column in any table differs from `database_schema_v1.7.md` Section 3

**2.3 Infrastructure State**
- `docker-compose up --build` completes without error
- Exactly two containers are running
- No third container of any kind is present

**2.4 Agent File State**
- `app/agents/synthesis_agent.py` exists and is importable
- No files named `signal_detector.py`, `projection_builder.py`, `signal_interpreter.py`, `bundle_constructor.py`, or `interview_generator.py` exist in `app/agents/`

**2.5 Policy Guard State**
- `policy/guard.py` contains the validation logic for Call 2 output (`themes[]`, `question_groups[]`)
- `policy/config.py` contains the prohibited terms list

If any check fails, the Stage 1.5 system must be restored to a passing state before Stage 1.7 migration begins.

---

## 3. `llm/client.py` Refactor Decision

**Decision:** The existing `generate_synthesis(canonical)` function is replaced with a generic `generate(messages)` function.

**Rationale:** The client is a thin HTTP wrapper. Prompt construction belongs in the calling agents, not in the client. Making the client generic removes all business logic from the transport layer and allows Agents 14 and 16 to construct their own prompts independently. The client does not need to know whether it is serving Call 1 or Call 2.

**New function signature:**

```python
def generate(messages: list[dict]) -> str:
    """
    Makes exactly one synchronous HTTP call to the configured LLM endpoint.
    Accepts a messages list in the format required by the endpoint.
    Returns the raw LLM response string.
    Does not parse, validate, or interpret the response.
    Does not retry on failure.
    Raises on HTTP error.
    """
```

**Migration steps:**

3.1. In `llm/client.py`, add the `generate(messages)` function. The HTTP call mechanism, endpoint URL, model name, and authentication pattern are identical to the existing implementation — only the input signature and the absence of prompt hardcoding differ.

3.2. Confirm `generate()` makes exactly one HTTP call per invocation. No retry logic. No fallback.

3.3. Keep `generate_synthesis()` in place until `synthesis_agent.py` is retired in Phase K. It must not be deleted before Phase K.

3.4. `generate()` must be importable and functional before Phase E begins.

**Validation:** `generate()` is importable. Given a valid messages list, it returns a string. It does not modify `generate_synthesis()`.

---

## 4. Implementation Phases

Phases must be executed in the order defined. Each phase has a validation checkpoint that must pass before the subsequent phase begins. No phase may be started until its prerequisite checkpoint passes. This ordering is not a suggestion — it enforces the antigraviton constraint: no component may depend on a step that has not yet been verified.

---

### Phase A — New Agent Stub Files

**Purpose:** Create importable stub files for all five new agents in `app/agents/`. No implementation logic. This confirms the file structure is clean and that naming is consistent before any logic is written.

**Modules Affected:**
- `agents/signal_detector.py` (new — Agent 12)
- `agents/projection_builder.py` (new — Agent 13)
- `agents/signal_interpreter.py` (new — Agent 14)
- `agents/bundle_constructor.py` (new — Agent 15)
- `agents/interview_generator.py` (new — Agent 16)

**Steps:**

A.1. Create `agents/signal_detector.py` with a stub function `detect_signals(canonical, entity_id_map)` that raises `NotImplementedError`.

A.2. Create `agents/projection_builder.py` with a stub function `build_projection(canonical, entity_id_map, deterministic_signals)` that raises `NotImplementedError`.

A.3. Create `agents/signal_interpreter.py` with a stub function `interpret_signals(projection)` that raises `NotImplementedError`.

A.4. Create `agents/bundle_constructor.py` with a stub function `construct_bundle(validated_signals, canonical, entity_id_map)` that raises `NotImplementedError`.

A.5. Create `agents/interview_generator.py` with a stub function `generate_interview(bundle, entity_id_map)` that raises `NotImplementedError`.

**Explicit Boundaries:**
- No logic is implemented in this phase
- No existing files are modified
- `synthesis_agent.py` is not touched

**Validation Checkpoint A:**
- All five files exist in `app/agents/`
- All five stub functions are importable without error
- `synthesis_agent.py` is unchanged and still importable
- No existing agent import is broken

---

### Phase B — `llm/client.py` Refactor

**Purpose:** Add the generic `generate(messages)` function to `llm/client.py` per Section 3. This must be complete before any LLM-calling agent (Phase E, Phase H) is implemented.

**Modules Affected:**
- `llm/client.py`

**Steps:**

B.1. In `llm/client.py`, implement `generate(messages: list[dict]) -> str` as a synchronous HTTP wrapper using the same endpoint, authentication, and model configuration as the existing `generate_synthesis()`. The function accepts a messages list and returns the raw response string. It does not parse JSON. It does not retry. It raises on HTTP error.

B.2. Confirm that `generate_synthesis()` is not modified. Both functions coexist in this file until Phase K.

B.3. Write a unit test confirming `generate()` makes exactly one HTTP call per invocation given a valid messages list.

**Explicit Boundaries:**
- `generate_synthesis()` is not modified or deleted
- No prompt construction logic is introduced in `llm/client.py`
- No retry, fallback, or chaining logic is introduced
- No async mechanism is introduced

**Validation Checkpoint B:**
- `generate()` is importable from `llm/client.py`
- `generate_synthesis()` is unchanged and still importable
- Unit test confirms exactly one HTTP call per invocation

---

### Phase C — Agent 12: Signal Detector

**Purpose:** Implement `signal_detector.py` in full. This is the first new pipeline component. It is entirely deterministic and does not call the LLM. It must be independently testable before any downstream agent is implemented.

**Modules Affected:**
- `agents/signal_detector.py`

**Steps:**

C.1. Replace the stub in `signal_detector.py` with a full implementation of `detect_signals(canonical, entity_id_map) -> list[dict]`.

C.2. Implement rule-based detection logic for all nine allowed signal types as defined in `agent_pipeline_spec_v1.7.md` Section 7:
- `"duration_pattern"` — activity entry with numeric duration value above a defined threshold
- `"domain_concentration"` — multiple entries in academic or activity collections concentrated in the same subject domain keyword
- `"leadership_presence"` — one or more entries with `activity_type: "leadership"` present
- `"academic_distribution"` — observable distribution pattern in scores across subjects or levels
- `"essay_characteristic"` — measurable characteristic of an essay entry (e.g. `short_response_flag: true`)
- `"cross_section_pattern"` — meaningful entity token appearing across multiple canonical sections
- `"activity_volume"` — total count of activity entries within or across activity types
- `"test_performance_pattern"` — pattern in test score or sectional breakdown data
- `"timeline_characteristic"` — pattern observable from academic year sequencing

C.3. Assign `signal_id` sequentially from `DET-001` for each signal produced.

C.4. For each signal, populate all required fields per `agent_pipeline_spec_v1.7.md` Section 7 and `signal_architecture_spec_v1.7.md` Section 6.4:
- `signal_id`: format `DET-###`
- `signal_type`: one of the nine allowed values
- `observation`: plain factual statement, no evaluative language
- `referenced_entity_ids`: valid entity IDs from the provided entity_id_map
- `source_collection`: the canonical collection from which the signal was derived

C.5. Implement validation within `detect_signals()`:
- All `referenced_entity_ids` must exist in the provided entity_id_map
- `signal_type` must be one of the nine allowed values
- `observation` must not contain any term from the 21-term prohibited list in `llm_synthesis_contract_v1.7.md` Section 5
- If any signal fails these checks, raise immediately — do not return a partial collection

C.6. Write unit tests using Ananya Kapoor's canonical (the dummy JSON provided) as a fixture. Confirm the output is a non-empty list of valid signals with all required fields populated.

**Explicit Boundaries:**
- No LLM call in this agent
- No evaluation, ranking, or inference
- `observation` field contains factual statements only — no evaluative language
- Entity IDs referenced must come from the entity_id_map — no new IDs invented
- No modification of canonical data

**Validation Checkpoint C:**
- Given Ananya's canonical, `detect_signals()` returns a non-empty list
- Every signal in the output has all five required fields
- Every `referenced_entity_id` in every signal exists in the provided entity_id_map
- All `signal_type` values are within the nine allowed values
- No evaluative language appears in any `observation` field
- Agent 12 makes no LLM call

---

### Phase D — Agent 13: Projection Builder

**Purpose:** Implement `projection_builder.py` in full. This agent constructs the Call 1 canonical projection per `canonical_projection_spec_v1.7.md`. It must be independently verified before Agent 14 is implemented.

**Prerequisite:** Phase C must be complete. Agent 13 receives the signal collection from Agent 12 as input.

**Modules Affected:**
- `agents/projection_builder.py`

**Steps:**

D.1. Replace the stub in `projection_builder.py` with a full implementation of `build_projection(canonical, entity_id_map, deterministic_signals) -> dict`.

D.2. Implement the `applicant_context` block:
- Include `full_name`, `preferred_major`
- Include `family_background` with `father` and `mother` sub-objects containing `name`, `education`, `field_of_employment`, `organization`, `designation` — only non-null fields
- Exclude `application_id`, `date_of_birth`
- If all parent fields are null, omit that parent object entirely

D.3. Implement the `academic_profile` block:
- One entry per `academic_entries[]` item
- Include: assigned entity ID (`ACA-###`), `academic_level`, `school_name`, `board_name`, `academic_year`, `grading_mode`, `score_raw`, subject entries (`subject_name` + `score_raw`)
- Include `predicted_score_raw` only if non-null
- Exclude: `entry_id`, `confidence_score`, `marking_scheme_raw`

D.4. Implement the `test_profile` block:
- One entry per `test_entries[]` item
- Include: assigned entity ID (`TST-###`), `test_name`, `total_score`, `sectional_scores` as `sections[]` (`label` + `score`)
- Include `percentile` and `rank` only if non-null
- Exclude: `entry_id`, `test_date`, `result_status`, `confidence_score`

D.5. Implement the `essay_profile` block:
- One entry per `essay_entries[]` item where `placeholder_flag` is `false` and `raw_text` is non-null
- Include: assigned entity ID (`ESS-###`), `essay_identifier` as `prompt`, `raw_text` as `text`
- Exclude: `entry_id`, `word_count`, `placeholder_flag`, `short_response_flag`, `confidence_score`

D.6. Implement the `activity_profile` block:
- One entry per `activity_entries[]` item
- Include: assigned entity ID (`ACT-###`), `activity_type`
- Include `activity_name`, `position_title`, `level`, `achievement` if non-null and passing artifact check
- Include `duration` as `duration_years` only if it is a numeric string (attempt float parse — include on success, exclude on failure)
- Apply text field artifact rules per `canonical_projection_spec_v1.7.md` Section 7.4:
  - Exclude `roles_and_responsibilities` and `activity_name` if the value contains a question mark, matches a known form label pattern, or is a single word from the blocklist: `["Organization", "Reference", "Position", "Role", "Title", "Name", "Duration", "Level"]`
  - Exclude `position_title` only if it matches a known form label pattern (the blocklist rule does not apply to `position_title`)
- Drop entry entirely if no substantive fields remain after null omission and artifact removal (must have at least one of: non-null `activity_name`, non-null `position_title`, non-null `achievement`)
- Exclude: `entry_id`, `description_raw`, `confidence_score`

D.7. Attach `entity_id_map` and `deterministic_signals` as top-level keys in the projection output.

D.8. Implement projection verification before returning:
- Every included entry has an entity ID
- Every entity ID in the projection body appears in `entity_id_map`
- No null fields are present anywhere in the projection
- No empty section arrays (omit the section key entirely if the array would be empty)
- `deterministic_signals` is present and non-empty
- No internal metadata fields present (`confidence_score`, `entry_id`, `placeholder_flag`, `short_response_flag`, `result_status`, `extraction_confidence`)
- If any check fails, raise immediately with the specific failing check identified

D.9. The following canonical sections must be excluded entirely from the projection:
- `schooling_history[]`
- `timeline_entries[]`
- `cross_references`
- `integrity_report`
- `extraction_confidence`

**Explicit Boundaries:**
- No LLM call in this agent
- Canonical representation is not modified
- No field values are summarized, paraphrased, or reordered
- No inference or quality judgment on entries
- Entity IDs are inherited from the entity_id_map — not reassigned

**Validation Checkpoint D:**
- Given Ananya's canonical and a valid entity_id_map and signal collection, `build_projection()` returns a projection with no null fields
- No `entry_id` UUID appears anywhere in the output
- No `confidence_score` appears anywhere in the output
- `schooling_history`, `timeline_entries`, `cross_references`, `integrity_report`, `extraction_confidence` are absent
- `deterministic_signals` key is present and non-empty
- `entity_id_map` key is present
- The parse artifact entry from Ananya's data (`duration: "Mobile Number"`) does not appear in `activity_profile`
- Canonical representation passed to the function is unchanged after the call

---

### Phase E — Agent 14: Signal Interpreter (LLM Call 1)

**Purpose:** Implement `signal_interpreter.py`. This agent constructs the LLM Call 1 prompt and makes exactly one LLM call. It does not validate its own output — that is the Policy Guard's responsibility.

**Prerequisite:** Phase D must be complete. Phase B must be complete (`generate()` function available).

**Modules Affected:**
- `agents/signal_interpreter.py`

**Steps:**

E.1. Replace the stub in `signal_interpreter.py` with a full implementation of `interpret_signals(projection: dict) -> str`.

E.2. Construct the LLM prompt from the projection. The prompt must:
- Include the complete `applicant_context`, `academic_profile`, `test_profile`, `essay_profile`, `activity_profile` sections from the projection
- Include the `entity_id_map` so the LLM can resolve entity IDs
- Include the `deterministic_signals` collection so the LLM can anchor interpretations to observations
- Instruct the LLM to produce strictly valid JSON matching the `interpreted_signals[]` schema:
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
- Instruct the LLM explicitly:
  - `referenced_entity_ids` must reference only entity IDs from the provided entity_id_map
  - `supporting_det_signal_ids` must reference only `signal_id` values from the provided deterministic_signals
  - No interview questions, themes, or narrative summaries
  - No evaluative language (reproduce the 21-term list from `llm_synthesis_contract_v1.7.md` Section 5 in the prompt)
  - No new facts not present in the projection

E.3. Call `llm/client.py` `generate(messages)` exactly once. Pass the constructed prompt as the messages list.

E.4. Return the raw LLM response string. Do not parse JSON. Do not validate. Do not retry.

**Explicit Boundaries:**
- Exactly one LLM call per invocation
- No retry on failure
- No validation of LLM output
- No modification of the projection input
- Prompt construction must not summarize or paraphrase canonical content

**Validation Checkpoint E:**
- `interpret_signals()` is callable and returns a string
- Exactly one call to `llm/client.py` `generate()` per invocation (confirmed via mock or log)
- No retry logic exists in the function
- Function does not raise on receiving a malformed LLM response string — it returns it as-is

---

### Phase F — Policy Guard: Call 1 Validation Function

**Purpose:** Extend `policy/guard.py` with `validate_signals()` — a new function for Call 1 output validation. The existing validation logic is not modified.

**Modules Affected:**
- `policy/guard.py`
- `policy/config.py`

**Steps:**

F.1. In `policy/config.py`, update the prohibited terms list to the full 21-term list defined in `llm_synthesis_contract_v1.7.md` Section 5:
`"Strength"`, `"Weakness"`, `"Outstanding"`, `"Exceptional"`, `"Deficiency"`, `"Below average"`, `"Underperformance"`, `"High potential"`, `"Top candidate"`, `"Risk factor"`, `"Admit"`, `"Reject"`, `"Likelihood"`, `"Impressive"`, `"Concerning"`, `"Excellent"`, `"Poor"`, `"Weak"`, `"Strong"`, `"Competitive"`, `"Uncompetitive"`.

If the existing list already contains some of these terms, extend it to include all 21. Do not remove any existing terms.

F.2. In `policy/guard.py`, add a new function `validate_signals(raw_output: str, entity_id_map: list, deterministic_signals: list) -> dict`. This function must perform the following validations in sequence:

F.2.1. **JSON structure.** Parse `raw_output` as JSON. Verify `interpreted_signals` key is present and is an array. If parsing fails or key is absent, reject with reason `"invalid_json_or_missing_key"`.

F.2.2. **Required fields.** Verify every signal in `interpreted_signals` contains all five required fields: `signal_id`, `title`, `description`, `referenced_entity_ids`, `supporting_det_signal_ids`. No field may be null or empty. Reject with reason `"missing_required_field"` if any field is absent or empty.

F.2.3. **Signal ID format.** Verify all `signal_id` values follow the `INT-###` format. Verify no duplicate `signal_id` values exist. Reject with reason `"invalid_signal_id_format"` or `"duplicate_signal_id"` as appropriate.

F.2.4. **Entity ID validation.** For every `referenced_entity_id` in every signal, verify it exists in the provided `entity_id_map`. Reject with reason `"invented_entity_id"` if any ID is not present.

F.2.5. **Deterministic signal ID validation.** For every `supporting_det_signal_ids` value in every signal, verify it exists in the provided `deterministic_signals` collection. Reject with reason `"invented_det_signal_id"` if any ID is not present.

F.2.6. **Language validation.** Scan all `title` and `description` fields against the 21-term prohibited list from `policy/config.py`. Matching is case-insensitive and partial-match aware. Reject with reason `"prohibited_language"` if any term is detected, identifying the specific term and field.

F.2.7. **Return structure.** On success, return `{"passed": True, "validated_signals": [parsed signal list]}`. On failure, return `{"passed": False, "reason": "...", "detail": "..."}`. Do not raise exceptions for validation failures — return the failure dict.

F.3. Confirm the existing Call 2 validation function (previously the only function in `guard.py`) is not modified. Name it explicitly `validate_themes(raw_output, entity_id_map)` if it does not already have a named function form.

**Explicit Boundaries:**
- `validate_signals()` does not call the LLM
- `validate_signals()` does not correct or modify LLM output
- No changes to the existing `validate_themes()` function behavior
- No changes to routing, persistence, or agent logic

**Validation Checkpoint F:**
- `validate_signals()` is importable from `policy/guard.py`
- Correctly rejects output with an invented entity ID not in the map
- Correctly rejects output with a signal referencing a non-existent deterministic signal ID
- Correctly rejects output missing a required field
- Correctly rejects output with a duplicate `signal_id`
- Correctly rejects output containing a prohibited term in `title` or `description`
- Correctly rejects structurally invalid (non-JSON) input
- On valid input, returns `{"passed": True, "validated_signals": [...]}` with the parsed collection
- `validate_themes()` is unchanged and passes its existing tests

---

### Phase G — Agent 15: Bundle Constructor

**Purpose:** Implement `bundle_constructor.py` in full. This agent receives validated interpreted signals and pairs each with its canonical evidence. It is deterministic.

**Prerequisite:** Phase F must be complete. Agent 15 receives validated signals from the Policy Guard.

**Modules Affected:**
- `agents/bundle_constructor.py`

**Steps:**

G.1. Replace the stub in `bundle_constructor.py` with a full implementation of `construct_bundle(validated_signals: list, canonical: dict, entity_id_map: list) -> dict`.

G.2. For each validated interpreted signal, extract the canonical entries corresponding to its `referenced_entity_ids`:
- Look up each entity ID in `entity_id_map` to identify the collection and entry
- Retrieve the corresponding entry from the canonical collection
- Apply the same field hygiene as the canonical projection: exclude `entry_id` UUIDs, exclude `confidence_score`, omit null fields, exclude parse artifact fields
- For essay entries, include full `raw_text`
- For academic entries, include level, scores, and subjects
- For test entries, include name, total score, and sectional breakdowns
- For activity entries, include type, name, position, level, duration (numeric only)

G.3. Construct the bundle per `signal_architecture_spec_v1.7.md` Section 10.3:
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

G.4. Enforce bundle rules:
- Must not include canonical entries not referenced by any validated signal
- Must not include the full canonical representation
- Must not include confidence scores or extraction metadata
- Must not introduce new entity IDs
- `application_id` sourced from `canonical.identifiers.application_id`

**Explicit Boundaries:**
- No LLM call in this agent
- Canonical representation is not modified
- Only entries referenced by validated signals are included
- Bundle does not include deterministic signal metadata beyond `supporting_det_signal_ids`

**Validation Checkpoint G:**
- Given validated signals and Ananya's canonical, `construct_bundle()` returns a valid bundle structure
- Bundle contains no `confidence_score` fields
- Bundle contains no `entry_id` UUID fields
- Bundle contains no null fields
- Only entity IDs referenced by validated signals appear in the bundle
- `application_id` is present and correct
- Canonical passed to the function is unchanged after the call

---

### Phase H — Agent 16: Interview Generator (LLM Call 2)

**Purpose:** Implement `interview_generator.py`. This agent constructs the LLM Call 2 prompt and makes exactly one LLM call. It does not validate its own output.

**Prerequisite:** Phase G must be complete. Phase B must be complete.

**Modules Affected:**
- `agents/interview_generator.py`

**Steps:**

H.1. Replace the stub in `interview_generator.py` with a full implementation of `generate_interview(bundle: dict, entity_id_map: list) -> str`.

H.2. Construct the LLM prompt from the signal-evidence bundle. The prompt must:
- Include all `signal_evidence_pairs` from the bundle
- Include the `entity_id_map` for reference validation context
- Include `application_id` for report context
- Instruct the LLM to produce strictly valid JSON matching the Call 2 output schema:
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
- Instruct the LLM explicitly:
  - `referenced_entity_ids` must reference only entity IDs from the provided entity_id_map
  - `question_groups[].theme_id` must reference only `theme_id` values defined in `themes[]`
  - No evaluative language (reproduce the 21-term prohibited list in the prompt)
  - No new facts not present in the signal-evidence bundle
  - Questions must be open-ended and exploratory

H.3. Call `llm/client.py` `generate(messages)` exactly once. Return the raw LLM response string. Do not parse. Do not validate. Do not retry.

**Explicit Boundaries:**
- Exactly one LLM call per invocation
- No retry on failure
- The LLM does not receive the full canonical representation
- The LLM does not receive the raw Call 1 output
- Prompt construction must not summarize or reinterpret signal content

**Validation Checkpoint H:**
- `generate_interview()` is callable and returns a string
- Exactly one call to `llm/client.py` `generate()` per invocation
- No retry logic exists in the function
- Function returns raw LLM response string without modification

---

### Phase I — Policy Guard: Call 2 Validation Confirmation

**Purpose:** Verify that the existing `validate_themes()` function meets Stage 1.7 requirements. Update the prohibited terms list if Phase F has not already done so. This phase confirms the existing guard handles Call 2 correctly — it is a verification and update phase, not a rewrite.

**Modules Affected:**
- `policy/guard.py` (verify only, update if needed)
- `policy/config.py` (confirm 21-term list from Phase F is present)

**Steps:**

I.1. Confirm `validate_themes(raw_output, entity_id_map)` performs all required validations per `agent_pipeline_spec_v1.7.md` Section 10.2:
- JSON structure: `themes` and `question_groups` keys present and are arrays
- All required fields present in each theme and question group
- `theme_id` uniqueness in `themes[]`
- All `question_groups[].theme_id` values reference a defined theme
- All `referenced_entity_ids` in themes exist in the entity_id_map
- No prohibited language in any theme title, description, group title, or question

I.2. If any of the above checks are missing from the existing implementation, add them. Do not remove or alter existing passing checks.

I.3. Confirm the prohibited terms list in `policy/config.py` is the full 21-term list (updated in Phase F). If Phase F is complete, this is a confirmation step only.

I.4. Confirm `validate_themes()` returns a consistent structure: `{"passed": True, "validated_output": {...}}` on success and `{"passed": False, "reason": "...", "detail": "..."}` on failure.

**Explicit Boundaries:**
- No changes to the calling signature or return structure if it already conforms
- No changes to `validate_signals()` introduced in Phase F

**Validation Checkpoint I:**
- `validate_themes()` correctly rejects output with an invented entity ID
- `validate_themes()` correctly rejects output with a broken `question_groups.theme_id` link
- `validate_themes()` correctly rejects output containing a prohibited term
- `validate_themes()` correctly rejects structurally invalid input
- On valid input, returns a passing result with the parsed output
- All 21 prohibited terms are present in `policy/config.py`

---

### Phase J — Orchestrator Rewiring (Agent 0)

**Purpose:** Update `orchestrator.py` to execute the full Stage 1.7 pipeline. This is the integration phase. All prior phases must be complete and their validation checkpoints must have passed before this phase begins.

**Prerequisite:** All of Phases A through I must be complete.

**Modules Affected:**
- `agents/orchestrator.py`

**Steps:**

J.1. Update the pipeline execution sequence in `agents/orchestrator.py` to implement the Stage 1.7 flow:

```
1.  Execute Agents 1–11 sequentially (unchanged)
2.  Invoke projection/ros_projector.py
      → Receive: Pages 1–3, entity_id_map
3.  Invoke agents/signal_detector.py (Agent 12)
      → Input: canonical, entity_id_map
      → Receive: deterministic_signals[]
4.  Invoke agents/projection_builder.py (Agent 13)
      → Input: canonical, entity_id_map, deterministic_signals
      → Receive: call_1_projection
5.  Invoke agents/signal_interpreter.py (Agent 14)
      → Input: call_1_projection
      → Receive: raw_call_1_output (string)
6.  Invoke policy/guard.py validate_signals()
      → Input: raw_call_1_output, entity_id_map, deterministic_signals
      → Receive: validation_result_1
7.  If validation_result_1["passed"] is False:
      → Log failure reason
      → Set applications.pipeline_status = "failed"
      → Set synthesis_records.policy_passed = False
      → Populate synthesis_records.policy_violations_log
      → Abort. Do not proceed to step 8.
8.  Invoke agents/bundle_constructor.py (Agent 15)
      → Input: validation_result_1["validated_signals"], canonical, entity_id_map
      → Receive: signal_evidence_bundle
9.  Invoke agents/interview_generator.py (Agent 16)
      → Input: signal_evidence_bundle, entity_id_map
      → Receive: raw_call_2_output (string)
10. Invoke policy/guard.py validate_themes()
      → Input: raw_call_2_output, entity_id_map
      → Receive: validation_result_2
11. If validation_result_2["passed"] is False:
      → Log failure reason
      → Set applications.pipeline_status = "failed"
      → Set synthesis_records.policy_passed = False
      → Populate synthesis_records.policy_violations_log
      → Abort. Do not proceed to step 12.
12. Invoke ros/assembler.py
      → Input: Pages 1–3, validation_result_2["validated_output"], report_metadata
      → Receive: full_ros_v1
13. Construct synthesis_output:
      {
        "report_metadata": ...,
        "page_1_background_profile": ...,
        "page_2_academic_and_engagement": ...,
        "page_3_essays": ...,
        "page_4_focus_themes": ...,
        "page_5_question_groups": ...,
        "signal_data": {
          "deterministic_signals": deterministic_signals,
          "interpreted_signals": validation_result_1["validated_signals"]
        }
      }
14. Persist canonical to canonical_records.canonical_data
15. Persist synthesis_output to synthesis_records.synthesis_output
16. Set applications.pipeline_status = "complete"
    Set synthesis_records.policy_passed = True
```

J.2. Confirm the orchestrator does not call `synthesis_agent.py`. It must not be invoked at any point in the Stage 1.7 flow. `synthesis_agent.py` still exists at this stage — it is not deleted until Phase K — but it must not appear in the new orchestration sequence.

J.3. Confirm Agent 0 contains no extraction logic and no LLM calls. It orchestrates only.

J.4. Confirm no async mechanism, deferred execution, background thread, or job queue is introduced.

J.5. Confirm that both Call 1 validation failure (step 7) and Call 2 validation failure (step 11) result in pipeline abort with no further LLM calls. Neither failure triggers a retry or fallback.

**Explicit Boundaries:**
- `synthesis_agent.py` is not invoked anywhere in the new sequence
- Exactly two LLM calls per successful pipeline run
- Zero LLM calls on pipeline failure after either validation step
- No async execution introduced
- `ros/assembler.py` is not modified

**Validation Checkpoint J:**
- A complete end-to-end pipeline run with a real PDF produces a `synthesis_records` row
- `synthesis_output` contains all seven keys: the six ROS keys plus `signal_data`
- `signal_data.deterministic_signals` is a non-empty array of valid signals
- `signal_data.interpreted_signals` is a non-empty array of validated signals
- `page_4_focus_themes` and `page_5_question_groups` contain valid themes and question groups
- `report_metadata.report_version` equals `"ROS_v1"`
- Log output shows exactly two LLM invocation events per completed run
- Call 1 validation failure aborts pipeline with no Call 2 invocation (confirmed via test with injected bad Call 1 output)
- Call 2 validation failure aborts pipeline with no ROS assembly (confirmed via test with injected bad Call 2 output)
- `synthesis_agent.py` is not imported or called anywhere in the codebase

---

### Phase K — Retirement of `synthesis_agent.py`

**Purpose:** Remove `synthesis_agent.py` from the codebase. This phase is irreversible. It must only be executed after Phase J validation checkpoint passes completely.

**Prerequisite:** Phase J validation checkpoint must pass. The end-to-end pipeline must be confirmed working via the new agents before the old agent is deleted.

**Modules Affected:**
- `agents/synthesis_agent.py` (deleted)
- `llm/client.py` (remove `generate_synthesis()`)

**Steps:**

K.1. Confirm that `synthesis_agent.py` is not imported by any module in the codebase. Search the entire `app/` directory for any import of `synthesis_agent`. If any import is found, it is a wiring error from Phase J — fix Phase J before proceeding.

K.2. Delete `agents/synthesis_agent.py`.

K.3. In `llm/client.py`, remove the `generate_synthesis()` function. The file now contains only the `generate(messages)` function introduced in Phase B.

K.4. Confirm the application starts without error after deletion. Run the full end-to-end pipeline once more.

**Explicit Boundaries:**
- No other file is deleted in this phase
- No logic from `synthesis_agent.py` is migrated into another file — the new agents already implement all required functionality independently

**Validation Checkpoint K:**
- `synthesis_agent.py` does not exist in `app/agents/`
- `generate_synthesis()` does not exist in `llm/client.py`
- No module in the codebase imports `synthesis_agent`
- End-to-end pipeline run completes successfully
- `alembic current` shows the Stage 1 head revision — unchanged

---

## 5. Agent Pipeline Summary

### 5.1 Agents That Change

**Agent 0 — Pipeline Orchestrator:** Rewired to execute the full Stage 1.7 two-stage signal pipeline per Phase J. No extraction logic added. No direct LLM calls.

### 5.2 New Agents

**Agent 12 — Signal Detector** (`signal_detector.py`): Deterministic. Produces `deterministic_signals[]` from canonical data using rule-based logic.

**Agent 13 — Projection Builder** (`projection_builder.py`): Deterministic. Constructs Call 1 canonical projection per `canonical_projection_spec_v1.7.md`.

**Agent 14 — Signal Interpreter** (`signal_interpreter.py`): LLM Call 1. Produces `interpreted_signals[]`. Analysis only.

**Agent 15 — Bundle Constructor** (`bundle_constructor.py`): Deterministic. Constructs signal-evidence bundle from validated signals and canonical evidence.

**Agent 16 — Interview Generator** (`interview_generator.py`): LLM Call 2. Produces `themes[]` and `question_groups[]`. Communication only.

### 5.3 Retired Agents

**Agent 12 (legacy) — Synthesis Agent** (`synthesis_agent.py`): Retired in Phase K. Its number is reused by the Signal Detector, which occupies the same pipeline position (first stage after canonical assembly).

### 5.4 Agents Unchanged

Agents 1–11 and all non-agent modules (`ros_projector.py`, `ros/assembler.py`) are unchanged. Their responsibilities, input/output contracts, and prohibited behaviors remain identical to Stage 1.5.

---

## 6. Policy Guard Module Summary

`policy/guard.py` now supports two named invocation functions:

| Function | Invoked After | Validates |
|---|---|---|
| `validate_signals(raw_output, entity_id_map, deterministic_signals)` | Agent 14 (LLM Call 1) | Schema, signal ID format, entity IDs, det signal IDs, prohibited language |
| `validate_themes(raw_output, entity_id_map)` | Agent 16 (LLM Call 2) | Schema, theme ID uniqueness, entity IDs, question group linkage, prohibited language |

Both functions share the same prohibited terms configuration from `policy/config.py`. Neither function calls the LLM. Neither function corrects or modifies LLM output. Both functions return a structured result dict — they do not raise on validation failure.

---

## 7. LLM Contact Surface

Stage 1.7 makes exactly two LLM calls per successfully completed application. Both calls use `llm/client.py` `generate(messages)`.

| Call | Agent | Input | Output |
|---|---|---|---|
| Call 1 | Agent 14 | Call 1 canonical projection + deterministic signals + entity ID map | Raw interpreted signals string |
| Call 2 | Agent 16 | Signal-evidence bundle + entity ID map | Raw themes and question groups string |

No other component invokes the LLM. No retry is attempted on failure of either call. No fallback synthesis path exists.

---

## 8. Signal Storage Decision

**Decision: Signals are persisted alongside the ROS artifact in Stage 1.7.**

`synthesis_records.synthesis_output` stores a `signal_data` key containing both the deterministic signal collection and the validated interpreted signal collection in addition to the six ROS pages. No schema change is required — the JSONB column absorbs this addition.

This decision applies uniformly to all applications processed under Stage 1.7. It is not configurable per-application.

**Rationale:** Stage 1.7 introduces new intermediate reasoning artifacts. Persisting signal data enables debugging and auditability during the first production rollout — verifying that deterministic signals are being correctly derived and that interpreted signals are meaningful and well-grounded. The storage overhead is negligible. The decision can be reversed in a future stage by removing the `signal_data` key from `synthesis_output` construction in the orchestrator, which requires no schema migration.

---

## 9. Schema and Infrastructure Confirmation

No schema or infrastructure changes are introduced in Stage 1.7.

- **Alembic:** No new revision. `alembic current` shows the Stage 1 head revision throughout.
- **Tables:** Exactly four tables. No new table. No new column. No new constraint. No new index.
- **`canonical_version`:** Remains `"1.1"`. No version bump.
- **Container topology:** Two containers. No new container.
- **Environment variables:** No new variable. The complete set from `env_config_spec.md` is unchanged.
- **`synthesis_output` column:** JSONB type, column name, and table name are unchanged. Only the internal JSON content evolves to include `signal_data`.

---

## 10. Completion Criteria

Stage 1.7 is considered complete when all of the following are confirmed:

### 10.1 End-to-End Pipeline

- A complete pipeline run with a real PDF produces a `synthesis_records` row
- `synthesis_output` contains all seven keys: `report_metadata`, `page_1_background_profile`, `page_2_academic_and_engagement`, `page_3_essays`, `page_4_focus_themes`, `page_5_question_groups`, `signal_data`
- `report_metadata.report_version` equals `"ROS_v1"`
- `signal_data.deterministic_signals` is a non-empty array with valid schemas
- `signal_data.interpreted_signals` is a non-empty array with valid schemas
- All `referenced_entity_ids` in themes and interpreted signals exist in the deterministic entity map for the application

### 10.2 Two-Call Confirmation

- Log output for every completed run contains exactly two LLM invocation events
- No retry event appears in any log
- No LLM call occurs after a Call 1 validation failure
- No LLM call occurs after a Call 2 validation failure

### 10.3 Policy Guard Correctness

- Call 1 validation correctly rejects signals with invented entity IDs
- Call 1 validation correctly rejects signals with invented deterministic signal IDs
- Call 1 validation correctly rejects signals with prohibited language
- Call 1 validation correctly rejects structurally invalid Call 1 output
- Call 2 validation correctly rejects themes with invented entity IDs
- Call 2 validation correctly rejects question groups with broken theme ID links
- Call 2 validation correctly rejects output with prohibited language
- On any validation failure, `synthesis_records.policy_passed` is `false` and `policy_violations_log` is populated
- On any validation failure, no ROS artifact is assembled and no partial artifact is persisted

### 10.4 Codebase Cleanliness

- `synthesis_agent.py` does not exist in `app/agents/`
- `generate_synthesis()` does not exist in `llm/client.py`
- No module imports `synthesis_agent` anywhere in the codebase
- No LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent framework import exists in any module

### 10.5 Schema and Infrastructure Freeze

- `alembic current` shows the Stage 1 head revision — no new revision applied
- Exactly four tables: `users`, `applications`, `canonical_records`, `synthesis_records`
- No new column in any table
- `synthesis_records.synthesis_output` is JSONB type, column name unchanged
- `canonical_records.canonical_version` value is `"1.1"` for all new records
- Exactly two containers running: API and PostgreSQL
- No third container of any kind
- `DATABASE_URL` continues to use the synchronous psycopg2 driver prefix
- No async driver, asyncio usage, background thread, or deferred execution mechanism in any module

### 10.6 API Behavior

- `POST /upload` triggers the full Stage 1.7 pipeline and returns the complete ROS v1 artifact
- `GET /applications/{id}` returns the stored `synthesis_output` without re-invoking the pipeline or LLM

---

## 11. Constraint Check

| Constraint | Status | Evidence |
|---|---|---|
| Deterministic-first preserved — Agents 1–11 use no LLM | ✅ | Phases A–D confirm new agents 12, 13, 15 are deterministic. Agents 1–11 are explicitly unchanged in Section 1.2. No LLM involvement before Agent 14. |
| Exactly two bounded LLM calls per application | ✅ | Phase E implements exactly one call in Agent 14. Phase H implements exactly one call in Agent 16. Phase J orchestrator wiring shows exactly two LLM invocations in the success path. Section 10.2 requires log-based two-call confirmation. |
| Call 2 receives only validated signal-evidence bundle | ✅ | Phase J step 9 passes only `signal_evidence_bundle` and `entity_id_map` to Agent 16. Agent 16 does not receive canonical projection, full canonical, or raw Call 1 output per Phase H boundaries. |
| Sequential execution — Call 1 validated before Call 2 invoked | ✅ | Phase J step 7 aborts pipeline on Call 1 validation failure before step 8–9 are reached. No parallel execution introduced anywhere. |
| No fallback and no retry on LLM failure | ✅ | Phase E and Phase H explicitly prohibit retry logic. Phase J steps 7 and 11 abort on failure with no further LLM invocations. Section 10.2 requires zero retry events in logs. |
| Signal validation is mandatory and non-bypassable | ✅ | Phase J step 6 invokes `validate_signals()` before bundle construction. Phase J step 7 aborts if validation fails. There is no code path from Agent 14 output to Agent 15 that does not pass through the Policy Guard. |
| Canonical–presentation separation enforced | ✅ | Phase D explicitly prohibits canonical modification. Phase J passes canonical to the projection layer read-only. `ros/assembler.py` is unchanged. No projection modifies canonical_records. |
| Canonical representation immutable after Agent 11 | ✅ | Phases C, D, G explicitly state canonical is not modified. Phase J validation checkpoint confirms canonical is unchanged after each new agent call. |
| Synchronous execution — no async or deferred stages | ✅ | Phase J step J.4 explicitly prohibits async mechanisms. Section 9 confirms no async driver. Section 10.5 requires confirmation that no asyncio usage exists. |
| Infrastructure freeze — no topology changes | ✅ | Section 1.2 confirms no new containers, variables, or infrastructure changes. Section 9 states infrastructure freeze explicitly. Section 10.5 requires exactly two containers at completion. |
| Database stability — no schema migrations | ✅ | Section 1.2 confirms no Alembic migration, no new tables, no new columns. Section 9 repeats this. Section 10.5 requires `alembic current` to show Stage 1 head unchanged. Phase K validation checkpoint confirms this at retirement. |
| No evaluation logic in any pipeline component | ✅ | Phase C prohibits evaluative language in signal observations. Phase F enforces 21-term prohibited list at both validation points. Section 10.3 requires prohibited language rejection at both calls. |
| No recursive reasoning — no LLM output fed back into LLM | ✅ | Phase J confirms Call 2 receives only the signal-evidence bundle — not raw Call 1 output. Phase H explicitly states the LLM does not receive raw Call 1 output. No code path feeds any LLM response back into any LLM call. |
| ROS v1 output schema unchanged | ✅ | `ros/assembler.py` is not modified. `report_version` remains `"ROS_v1"`. All five page keys and their schemas are unchanged. Section 10.1 requires `report_version` equals `"ROS_v1"`. |
| No additional LLM frameworks introduced | ✅ | Phase E and Phase H use `llm/client.py` `generate()` — a direct synchronous HTTP call. Section 10.4 requires confirmation that no LangChain, LangGraph, AutoGen, CrewAI, or Semantic Kernel import exists in any module. |

---

*End of `stage_1_7_migration_plan.md`.*

*Document Version: 1.0 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Architecture Version: `architecture_lock_v1.7.md`*