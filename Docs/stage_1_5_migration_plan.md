# `stage_1_5_migration_plan.md`

**(Stage 1.5 — ROS v1 Integrated Structured Output: Concrete Migration Governance Plan)**

---

## Preamble

This document governs the concrete transition from Stage 1 (Structured MVP) to Stage 1.5 (ROS v1 Integrated Structured Output). It is a logical-layer migration governance document only. It does not generate code, SQL, Dockerfiles, docker-compose YAML, Alembic scripts, or Python classes. All implementation artifacts produced under this plan must comply with the governing specification documents listed below. In cases of conflict between any section of this document and `architecture_lock.md`, `architecture_lock.md` prevails without exception.

### Governing Documents

| Document | Role |
|---|---|
| `architecture_lock.md` | Supreme constraint authority. Prevails over all other documents in conflict. |
| `system_overview_v1.5.md` | Architectural identity and invariants for Stage 1.5. |
| `agent_pipeline_spec_v1.5.md` | Logical pipeline definition with ROS v1 projection layer and Canonical v1.1 alignment. |
| `canonical_model_philosophy_v1.5.md` | Canonical representation invariants. Canonical version incremented to 1.1. |
| `llm_synthesis_contract_v1.5.md` | LLM synthesis behavioral contract. Structured output schema updated for ROS v1. |
| `ROSv1.md` | Report Output Specification. Authoritative definition of the five-page ROS v1 structure. |
| `database_schema_v1.md` | Formal PostgreSQL schema definition. Unchanged in Stage 1.5. |
| `database_schema_v1.5.md` | Stage 1.5 schema confirmation. No structural changes; `synthesis_output` JSONB content evolves only. |
| `env_config_spec.md` | Environment variable specification. Unchanged in Stage 1.5. |

---

## 1. Migration Purpose

### 1.1 What Stage 1.5 Introduces

Stage 1.5 is a logical-layer evolution of the Stage 1 system. It does not alter infrastructure, schema, or deployment topology. Every change introduced by Stage 1.5 is an evolution of the logical processing and output structure that executes entirely within the existing single-container application.

**Canonical Model Evolution (v1.0 → v1.1).** The canonical representation is incremented to version 1.1. Three additive structural changes are introduced: a structured `family_background` object nested under `identifiers`, a new `schooling_history[]` collection capturing institutional affiliation history, and an explicit `activity_type` classification field on each `activity_entries[]` item. These additions are additive-only, preserved within the existing `canonical_data` JSONB column, and require no Alembic migration. All collection discipline and non-evaluative invariants remain absolute.

**Deterministic ROS Projection Layer (Pages 1–3).** A deterministic projection function is introduced that consumes the Canonical v1.1 representation and produces the first three pages of the ROS v1 artifact: `page_1_background_profile`, `page_2_academic_and_engagement`, and `page_3_essays`. This layer assigns stable `entity_id` values to canonical entries, groups activities by `activity_type`, and computes deterministic highlight spans over essay text. It makes no LLM calls. It does not mutate canonical. It is not a separate service or container.

**Structured LLM Synthesis Output (Pages 4–5).** The LLM synthesis contract is updated. Agent 12 now receives the projection-cleaned Canonical v1.1 representation annotated with deterministic `entity_id` values. It is required to produce strictly structured JSON output conforming to the `themes[]` and `question_groups[]` schema defined in `llm_synthesis_contract_v1.5.md`. This corresponds to ROS Pages 4 and 5. The single-call invariant is preserved without modification.

**Entity ID Referencing.** Stable `entity_id` values are derived deterministically from canonical array order during ROS projection. These identifiers are used to anchor LLM theme references and highlight spans. `entity_id` values are projection-layer metadata only; they are not stored in canonical.

**Span-Based Essay Highlights.** Page 3 of the ROS includes deterministic highlight spans over essay full text. Spans are expressed as `start_char` and `end_char` character offsets, and may reference `entity_id` values from other canonical collections. Highlight generation is entirely deterministic. No LLM involvement is permitted in highlight generation.

**ROS Assembly Integration.** After Agent 13 validates LLM output, a deterministic assembly step merges Pages 1–3 (projection-derived) with Pages 4–5 (LLM-derived), attaches `report_metadata`, and produces the full ROS v1 JSON artifact. This is stored in `synthesis_records.synthesis_output` in place of the Stage 1 flat synthesis structure.

### 1.2 Explicit Statement: Infrastructure Remains Frozen

Stage 1.5 does not modify any aspect of the infrastructure established in Stage 1.

The Docker topology (two containers: API + PostgreSQL) is unchanged. No new containers are introduced. No additional environment variables are defined. No Alembic migration is applied. No Redis, Celery, background worker, job queue, or async execution model is introduced. The synchronous, single-request-lifecycle execution model is preserved without modification.

All changes in Stage 1.5 are code-layer and logic-layer only. They execute within the existing `app/` module structure of the single API container.

---

## 2. Migration Scope

### 2.1 What Changes

The following elements change in Stage 1.5. All changes are logical-layer only.

**`canonical/version.py`.** The `CANONICAL_VERSION` constant is updated from `"1.0"` to `"1.1"`.

**`canonical/model.py`.** Pydantic model definitions are updated to include: `FamilyMember` and `FamilyBackground` models for the `identifiers.family_background` structure; a `SchoolingHistoryEntry` model for the `schooling_history[]` collection; and an `activity_type` field on `ActivityEntry` with allowed values `"extracurricular"`, `"co_curricular"`, `"leadership"`, `"other"`.

**`agents/personal_extractor.py` (Agent 3).** Updated to extract structured `family_background` from the personal section and populate `identifiers.family_background` in the canonical output.

**`agents/academic_extractor.py` (Agent 4).** Updated to separately extract institutional affiliation data into `schooling_history[]`, distinct from academic performance records in `academic_entries[]`. No merging of the two collections is permitted.

**`agents/activity_extractor.py` (Agent 7).** Updated to assign explicit `activity_type` classification to each extracted activity entry using deterministic, rule-based logic. Classification must not be delegated to LLM inference.

**`agents/assembler.py` (Agent 11).** Updated to stamp `"canonical_version": "1.1"` and assemble the canonical representation including the new `schooling_history[]` collection and `identifiers.family_background` structure.

**`projection/ros_projector.py` (New Module).** A new deterministic projection module is introduced. This module accepts a Canonical v1.1 representation, assigns `entity_id` values per the deterministic assignment algorithm, and constructs ROS Pages 1–3 as defined in `ROSv1.md`. This module is not an agent. It does not call the LLM.

**`agents/synthesis_agent.py` (Agent 12).** Updated to receive the projection-cleaned canonical representation annotated with `entity_id` values, and to construct the LLM prompt conforming to `llm_synthesis_contract_v1.5.md`. The single LLM call is preserved. The output schema target is updated to require `themes[]` and `question_groups[]`.

**`agents/validation_filter.py` (Agent 13).** Updated to validate the structured LLM output schema: JSON structure conformance, `theme_id` uniqueness, `referenced_entity_ids` existence against the deterministic entity map, `question_groups.theme_id` linkage validity, absence of prohibited language, and absence of invented entity IDs.

**`agents/orchestrator.py` (Agent 0).** Updated to invoke the deterministic ROS projection layer after Agent 11 canonical assembly, pass the annotated canonical to Agent 12, pass the LLM output to Agent 13, and invoke the ROS assembly step after successful validation.

**`ros/assembler.py` (New Module).** A new deterministic assembly module is introduced to merge validated Pages 1–3 with validated LLM Pages 4–5, attach `report_metadata`, and produce the full ROS v1 JSON artifact for persistence.

**`synthesis_records.synthesis_output` (JSONB content only).** The content of the `synthesis_output` JSONB column evolves from the Stage 1 flat structure to the full five-page ROS v1 structure defined in `ROSv1.md`. The column name, column type, table name, and all constraints remain unchanged. No Alembic migration is required.

**`policy/guard.py` and `policy/config.py`.** Updated to enforce prohibited language detection against the terms defined in `llm_synthesis_contract_v1.5.md` Section 6, and to validate `referenced_entity_ids` and `theme_id` linkage as defined in `llm_synthesis_contract_v1.5.md` Section 7.

### 2.2 What Does NOT Change

The following elements are explicitly unchanged in Stage 1.5:

- Database schema: no new tables, no new columns, no new constraints, no new indexes, no Alembic migration.
- Container topology: exactly two containers (API + PostgreSQL). No new containers.
- Environment variables: no new variables introduced. All twelve variables defined in `env_config_spec.md` remain the complete set.
- `llm/client.py`: the `generate_synthesis` function contract and synchronous HTTP invocation mechanism are unchanged.
- `database.py`: connection binding, pool configuration, and synchronous driver (psycopg2) are unchanged.
- `auth/router.py` and `api/applications.py`: route handlers are unchanged.
- Logging configuration: `LOG_LEVEL` and pipeline lifecycle log events are unchanged.
- Docker Compose topology, volumes, and health check behavior.
- Alembic revision history: no new revision is added.
- The four-table relational structure: `users`, `applications`, `canonical_records`, `synthesis_records`.
- The single-LLM-call-per-application invariant.
- The synchronous, sequential, single-request-lifecycle execution model.
- All agent modules not listed in Section 2.1 (Agents 1, 2, 5, 6, 8, 9, 10).

### 2.3 Why Changes Are Logical-Layer Only

Each change described in Section 2.1 affects only the internal processing logic of the application module. No change affects:

- How the system is packaged or deployed.
- What infrastructure the system depends on.
- How configuration is supplied.
- What database tables or columns exist.
- How database connections are established.

The deterministic projection layer is a Python function, not a service. Entity ID generation is a pure computation on canonical arrays. ROS assembly is a dictionary composition step. The LLM output schema update changes the prompt structure and the validation rules; it does not change the HTTP client, the LLM endpoint, or the call mechanism. In every case, the infrastructure, deployment, and schema layers from Stage 1 remain structurally and behaviorally identical to Stage 1.

---

## 3. Implementation Phases

This section defines the step-by-step execution phases for Stage 1.5 implementation. Phases must be executed in the order defined. Each phase includes the exact modules affected, the exact responsibilities assigned, explicit boundaries, and the validation checkpoint that must pass before the subsequent phase may begin.

---

### Phase A — Canonical Model Updates

**Purpose:** Update the Pydantic canonical model to Canonical v1.1. Introduce new structural types. Increment the version constant.

**Modules Affected:**
- `canonical/version.py`
- `canonical/model.py`

**Steps:**

A.1. In `canonical/version.py`, update the `CANONICAL_VERSION` constant from `"1.0"` to `"1.1"`. No other changes to this file.

A.2. In `canonical/model.py`, introduce the following new Pydantic model classes in this order:
   - `FamilyMember`: fields `name` (str or None), `education` (str or None), `occupation` (str or None), `organization` (str or None).
   - `FamilyBackground`: fields `father` (FamilyMember), `mother` (FamilyMember).
   - `SchoolingHistoryEntry`: fields `entry_id` (UUID), `level` (str), `school_name` (str or None), `board_name` (str or None), `location` (str or None), `confidence_score` (float).

A.3. In `canonical/model.py`, update the existing `ActivityEntry` model to add `activity_type` as a required field. Permitted values: `"extracurricular"`, `"co_curricular"`, `"leadership"`, `"other"`.

A.4. In `canonical/model.py`, update the `Identifiers` model to include `family_background` as an optional field of type `FamilyBackground` (nullable).

A.5. In `canonical/model.py`, update the top-level canonical model to include `schooling_history` as a required field of type `List[SchoolingHistoryEntry]`, defaulting to an empty list.

**Explicit Boundaries:**
- No existing field names, types, or semantics are altered.
- No evaluation-related fields are introduced.
- No page-grouping, theme-grouping, or UI-ordering fields are introduced in canonical.
- `entity_id` is not added to canonical. `entry_id` remains unchanged.
- No changes outside `canonical/version.py` and `canonical/model.py`.

**Validation Checkpoint A:**
- `CANONICAL_VERSION` equals `"1.1"`.
- `FamilyBackground`, `FamilyMember`, `SchoolingHistoryEntry` classes are importable from `canonical/model.py`.
- `ActivityEntry` has `activity_type` field.
- `Identifiers` has optional `family_background` field.
- Top-level canonical model has `schooling_history: List[SchoolingHistoryEntry]`.
- No evaluative fields exist in any canonical model class.
- All existing canonical model fields from v1.0 are preserved with identical names, types, and semantics.

---

### Phase B — Agent Pipeline Updates

**Purpose:** Update Agents 3, 4, 7, and 11 to produce Canonical v1.1 output. No changes to Agents 1, 2, 5, 6, 8, 9, or 10.

**Modules Affected:**
- `agents/personal_extractor.py` (Agent 3)
- `agents/academic_extractor.py` (Agent 4)
- `agents/activity_extractor.py` (Agent 7)
- `agents/assembler.py` (Agent 11)

**Steps:**

B.1. In `agents/personal_extractor.py` (Agent 3):
   - Add extraction logic to identify and extract `father` and `mother` family member data from the personal section of the PDF, if present.
   - Populate `identifiers.family_background` with a `FamilyBackground` object. If a family member's data is absent, the corresponding `FamilyMember` fields must be `null`. Do not infer missing values.
   - Do not normalize, enrich, or evaluate family background data. Preserve raw extracted values only.

B.2. In `agents/academic_extractor.py` (Agent 4):
   - Add extraction logic to identify institutional affiliation data (school name, board, level, location) from academic sections.
   - Populate `schooling_history[]` as a separate collection. Each entry receives a new UUID `entry_id`.
   - `academic_entries[]` and `schooling_history[]` must remain distinct. Institutional data must not be merged into academic performance records. Academic performance records must not be duplicated in schooling history.
   - No GPA conversion. No normalization. No cross-entry merging.

B.3. In `agents/activity_extractor.py` (Agent 7):
   - Add deterministic, rule-based classification logic to assign `activity_type` to each extracted activity entry.
   - Classification must be based solely on extracted content using defined rules. It must not call the LLM. It must not use heuristics that introduce evaluation.
   - Permitted `activity_type` values are exactly: `"extracurricular"`, `"co_curricular"`, `"leadership"`, `"other"`.
   - Default classification for unclassified activities is `"other"`.

B.4. In `agents/assembler.py` (Agent 11):
   - Update the canonical assembly step to stamp `"canonical_version": "1.1"`.
   - Ensure `schooling_history[]` from Agent 4 output is included in the assembled canonical representation.
   - Ensure `identifiers.family_background` from Agent 3 output is included in the assembled canonical representation.
   - Ensure `activity_type` is present on all `activity_entries[]` items.
   - Preserve all existing assembly behavior: array insertion order must be maintained, all existing collections remain required.
   - Agent 11 must not produce ROS output. Canonical must remain presentation-agnostic.

**Explicit Boundaries:**
- Agents 1, 2, 5, 6, 8, 9, and 10 are not modified in this phase.
- No agent in this phase calls the LLM.
- No agent in this phase applies scoring, ranking, normalization, or evaluation.
- No `entity_id` assignment occurs in this phase. `entity_id` assignment is exclusively the responsibility of the projection layer (Phase D).
- No agent in this phase is aware of ROS page structure.

**Validation Checkpoint B:**
- Agent 3 output includes `identifiers.family_background` with valid structure. Null fields are preserved as null, not omitted.
- Agent 4 output includes both `academic_entries[]` and `schooling_history[]` as distinct collections.
- Agent 7 output includes `activity_type` on every activity entry. All values are within the permitted set.
- Agent 11 output includes `"canonical_version": "1.1"` and all required collections: `identifiers`, `academic_entries[]`, `schooling_history[]`, `test_entries[]`, `essay_entries[]`, `activity_entries[]`, `timeline_entries[]`, `cross_references`, `integrity_report`, `extraction_confidence`.
- No evaluative field appears in any agent output.
- No `entity_id` field appears in canonical output.

---

### Phase C — LLM Synthesis Contract Integration

**Purpose:** Update Agent 12 (Synthesis Agent) to comply with `llm_synthesis_contract_v1.5.md`. Update the LLM input to include the projection-annotated canonical representation with `entity_id` values. Update the expected output schema to require `themes[]` and `question_groups[]`.

**Modules Affected:**
- `agents/synthesis_agent.py` (Agent 12)

**Prerequisite:** Phase D (ROS Projection Layer) must be complete, because Agent 12 receives the `entity_id`-annotated canonical prepared by the projection layer.

**Steps:**

C.1. In `agents/synthesis_agent.py`, update the input signature to accept the projection-annotated canonical representation. This includes the canonical collections with `entity_id` values assigned, ready for LLM consumption.

C.2. In `agents/synthesis_agent.py`, update the LLM prompt construction to include the following canonical collections in canonical array order, without sorting, collapsing, or normalization:
   - `academic_entries[]`
   - `schooling_history[]`
   - `test_entries[]`
   - `essay_entries[]`
   - `activity_entries[]` (including `activity_type`)
   - `identifiers.family_background`

   The LLM must not receive: confidence scores, integrity severity levels, internal extraction metadata, raw layout blocks, or raw PDF text.

C.3. In `agents/synthesis_agent.py`, update the LLM prompt to instruct the model to produce strictly valid JSON matching the following structure as defined in `llm_synthesis_contract_v1.5.md` Section 4:
   ```
   {
     "themes": [
       { "theme_id": "THEME-###", "title": "string", "description": "string", "referenced_entity_ids": ["string"] }
     ],
     "question_groups": [
       { "theme_id": "THEME-###", "group_title": "string", "questions": ["string"] }
     ]
   }
   ```

C.4. In `agents/synthesis_agent.py`, enforce in the prompt that:
   - The LLM must reference only `entity_id` values that were provided in the input.
   - The LLM must not invent new entity IDs.
   - `theme_id` values must follow the format `THEME-###`.
   - No prohibited language terms (as defined in `llm_synthesis_contract_v1.5.md` Section 6) may appear.

C.5. In `agents/synthesis_agent.py`, confirm that:
   - Exactly one LLM call is made per application. No retry logic is added. No fallback model is introduced. No secondary LLM pass is introduced.
   - The `llm/client.py` `generate_synthesis` function is used without modification. The LLM client is not wrapped in a retry decorator.

**Explicit Boundaries:**
- `llm/client.py` is not modified.
- No additional LLM call is introduced anywhere in the system.
- The LLM does not receive, generate, or modify Pages 1–3 of the ROS.
- The LLM does not modify canonical content.
- No async execution is introduced.

**Validation Checkpoint C:**
- Agent 12 prompt includes `schooling_history[]` (resolves audit mismatch identified in `llm_synthesis_contract_v1.5.md`).
- Agent 12 prompt includes `activity_type` values for all activity entries.
- Agent 12 prompt includes the complete `entity_id`-annotated canonical input.
- Agent 12 invokes `llm/client.py` exactly once per application.
- The expected output schema is `themes[]` + `question_groups[]` as defined in the contract.
- No additional LLM client invocation exists anywhere in the codebase.

---

### Phase D — Deterministic ROS Projection Layer Implementation

**Purpose:** Implement the deterministic projection module that consumes Canonical v1.1 and produces ROS Pages 1–3 with `entity_id` assignment. This module does not call the LLM.

**Modules Affected:**
- `projection/ros_projector.py` (New Module)

**Steps:**

D.1. Create `projection/ros_projector.py`. This module is not an agent. It is a pure deterministic projection function.

D.2. Implement deterministic `entity_id` assignment per the algorithm defined in `agent_pipeline_spec_v1.5.md` Section 4A:
   - For each canonical collection, independently index entries from 1 to `len(collection)` using canonical array order.
   - Apply prefix mapping:
     - `academic_entries[]` → prefix `ACA`
     - `test_entries[]` → prefix `TEST`
     - `essay_entries[]` → prefix `ESS`
     - `activity_entries[]` → prefix `ACT`
     - `schooling_history[]` → prefix `SCH`
   - Format: `{PREFIX}-{zero_padded_index_3_digits}` (e.g., `ACA-001`, `TEST-002`, `ESS-001`).
   - `entity_id` values must be stable across identical canonical input: given the same canonical representation with the same array order, the same `entity_id` values must always be produced.
   - `entity_id` values must not be stored in the canonical representation. They exist in the projection output only.
   - Projection must not sort canonical collections before assignment.

D.3. Implement Page 1 projection (`page_1_background_profile`) by mapping canonical fields as follows per `ROSv1.md`:
   - `identity` ← `identifiers` fields (application_number, full_name, date_of_birth, age_at_application, gender, nationality, city, state, country).
   - `family_background` ← `identifiers.family_background`.
   - `schooling_history` ← `schooling_history[]` with `entity_id` values assigned (`SCH-###`).
   - `academic_orientation` ← `identifiers` or extracted academic metadata.
   - If any canonical field is null or absent, the corresponding ROS field must preserve null. No heuristic reconstruction is permitted.

D.4. Implement Page 2 projection (`page_2_academic_and_engagement`) by mapping canonical fields as follows per `ROSv1.md`:
   - `academic_records` ← `academic_entries[]` with `entity_id` values assigned (`ACA-###`).
   - `standardized_tests` ← `test_entries[]` with `entity_id` values assigned (`TEST-###`), preserving percentiles and breakdowns.
   - `additional_tests` ← any additional test entries with `entity_id` values assigned (`TEST-ADD-###`).
   - `extracurricular_activities` ← `activity_entries[]` where `activity_type == "extracurricular"` or `activity_type == "other"`, with `entity_id` values assigned (`ACT-###`).
   - `co_curricular_activities` ← `activity_entries[]` where `activity_type == "co_curricular"`, with `entity_id` values assigned (`ACT-###`).
   - `leadership_roles` ← `activity_entries[]` where `activity_type == "leadership"`, with `entity_id` values assigned (`LEAD-###`).
   - Activity grouping must be based strictly on canonical `activity_type`. Projection must not reclassify activities.

D.5. Implement Page 3 projection (`page_3_essays`) by mapping canonical fields as follows per `ROSv1.md`:
   - `essays` ← `essay_entries[]` with `entity_id` values assigned (`ESS-###`), including `prompt`, `full_text`, and `word_count`.
   - For each essay, compute deterministic highlight spans by scanning `full_text` for tokens that correspond to canonical entities from other collections (academic entries, activity entries, test entries, schooling history). Express highlights as `start_char`/`end_char` character offsets over the essay `full_text`. Populate `referenced_entity_ids` within each highlight span with the corresponding `entity_id` values.
   - Highlight generation is strictly deterministic. No LLM involvement is permitted. No inference or interpretation is permitted.

D.6. The projection module must return:
   - The three constructed page objects (Pages 1–3).
   - The complete deterministic `entity_id` map (mapping canonical collection entries to their assigned `entity_id` values), for use by Agent 12 prompt construction and Agent 13 validation.

**Explicit Boundaries:**
- `projection/ros_projector.py` does not call the LLM.
- `projection/ros_projector.py` does not mutate the canonical representation.
- `projection/ros_projector.py` does not collapse canonical collections.
- `projection/ros_projector.py` does not introduce evaluation or scoring logic.
- `projection/ros_projector.py` does not rewrite essay content.
- `entity_id` values are not written back to `canonical_records`.

**Validation Checkpoint D:**
- Given identical canonical v1.1 input, `entity_id` assignment produces identical output on repeated calls (determinism).
- `SCH-001` through `SCH-N` map to the first through Nth `schooling_history[]` entries in canonical array order.
- `ACA-001` through `ACA-N` map to the first through Nth `academic_entries[]` entries in canonical array order.
- `TEST-001` through `TEST-N` map to the first through Nth `test_entries[]` entries in canonical array order.
- `ESS-001` through `ESS-N` map to the first through Nth `essay_entries[]` entries in canonical array order.
- `ACT-001` through `ACT-N` map to the first through Nth `activity_entries[]` entries in canonical array order.
- Page 1 contains no null-reconstructed values: null canonical fields appear as null in Page 1.
- Activity grouping in Page 2 matches canonical `activity_type` exclusively.
- Essay highlights in Page 3 contain only valid `entity_id` values present in the deterministic entity map.
- Canonical representation passed to projection is unchanged after projection completes.

---

### Phase E — ROS Assembly Integration

**Purpose:** Implement the ROS assembly module and update Agent 0 (Orchestrator) to execute the full Stage 1.5 pipeline flow including projection, LLM synthesis, validation, and final ROS assembly.

**Modules Affected:**
- `ros/assembler.py` (New Module)
- `agents/orchestrator.py` (Agent 0)

**Steps:**

E.1. Create `ros/assembler.py`. This module is a deterministic assembly function. It accepts:
   - Validated Pages 1–3 (from the projection layer).
   - Validated LLM output (Pages 4–5, from Agent 13).
   - `report_metadata` inputs: `application_number`, `generated_at` (current ISO-8601 timestamp), `canonical_version` (from canonical), `report_version` (constant `"ROS_v1"`).

   It returns the full ROS v1 JSON document matching the structure defined in `ROSv1.md`:
   ```
   {
     "report_metadata": { ... },
     "page_1_background_profile": { ... },
     "page_2_academic_and_engagement": { ... },
     "page_3_essays": { ... },
     "page_4_focus_themes": { ... },
     "page_5_question_groups": { ... }
   }
   ```

E.2. In `agents/orchestrator.py` (Agent 0), update the pipeline execution sequence to implement the Stage 1.5 flow as defined in `system_overview_v1.5.md` Section 2.2:
   1. Execute Agents 1–11 sequentially (unchanged).
   2. Invoke `projection/ros_projector.py` with the assembled canonical representation. Receive Pages 1–3 and the deterministic entity map.
   3. Invoke Agent 12 (Synthesis Agent) with the entity-map-annotated canonical. Receive LLM output (`themes[]`, `question_groups[]`).
   4. Invoke Agent 13 (Validation Filter) with the LLM output and the deterministic entity map. Receive validated thematic output.
   5. If Agent 13 validation fails: log the error, mark the application as failed, do not invoke `ros/assembler.py`, do not invoke a second LLM call.
   6. If Agent 13 validation passes: invoke `ros/assembler.py` to merge Pages 1–3, validated Pages 4–5, and `report_metadata` into the full ROS v1 document.
   7. Persist canonical to `canonical_records.canonical_data`. Persist full ROS v1 to `synthesis_records.synthesis_output`.

E.3. Confirm that Agent 0 passes the canonical representation to the projection layer before passing it to Agent 12. Agent 12 must receive the `entity_id`-annotated view, not the raw canonical.

E.4. Confirm that Agent 0 does not introduce any async mechanism, deferred execution, background thread, or job queue.

**Explicit Boundaries:**
- `ros/assembler.py` does not call the LLM.
- `ros/assembler.py` does not modify canonical content.
- Agent 0 does not perform extraction logic.
- Agent 0 does not invoke the LLM directly.
- No second LLM call is introduced anywhere in the orchestration sequence.

**Validation Checkpoint E:**
- A complete pipeline run with a real PDF produces a `synthesis_records` row where `synthesis_output` contains all six top-level ROS keys: `report_metadata`, `page_1_background_profile`, `page_2_academic_and_engagement`, `page_3_essays`, `page_4_focus_themes`, `page_5_question_groups`.
- `report_metadata.report_version` equals `"ROS_v1"`.
- `report_metadata.canonical_version` matches the associated `canonical_records.canonical_version`.
- The LLM was called exactly once during the pipeline run (confirmed via log output).
- If Agent 13 validation fails, no ROS artifact is persisted and no second LLM call is made.

---

### Phase F — Validation and Policy Guard Updates

**Purpose:** Update Agent 13 (Validation Filter) and `policy/guard.py` to enforce the structured output contract defined in `llm_synthesis_contract_v1.5.md`.

**Modules Affected:**
- `agents/validation_filter.py` (Agent 13)
- `policy/guard.py`
- `policy/config.py`

**Steps:**

F.1. In `agents/validation_filter.py` (Agent 13), implement the following validation steps in sequence, as required by `llm_synthesis_contract_v1.5.md` Section 7:

   F.1.1. **JSON structure conformance.** Verify that the LLM response parses as valid JSON and contains both `themes` (array) and `question_groups` (array) at the top level.

   F.1.2. **`theme_id` uniqueness.** Verify that all `theme_id` values within the `themes[]` array are unique. Reject if any duplicate is found.

   F.1.3. **`referenced_entity_ids` existence.** For every `referenced_entity_id` in every theme, verify that the ID exists in the deterministic entity map produced by the projection layer. Reject if any `referenced_entity_id` is not present in the entity map.

   F.1.4. **`question_groups.theme_id` linkage.** For every `theme_id` in `question_groups[]`, verify that it exists in the `themes[]` array. Reject if any `question_groups` entry references a non-existent `theme_id`.

   F.1.5. **No invented entity IDs.** Verify no `referenced_entity_id` appears that was not in the provided entity map. This duplicates the check in F.1.3 as an explicit named validation step.

   F.1.6. **Prohibited language detection.** Pass the full LLM response text through `policy/guard.py`. Reject if any prohibited term defined in `llm_synthesis_contract_v1.5.md` Section 6 is detected.

   F.1.7. **Rejection behavior.** If any of the above validations fail: log the failure reason, mark the application as failed in `applications.pipeline_status`, set `synthesis_records.policy_passed` to `false`, populate `synthesis_records.policy_violations_log` with the structured rejection reason. Do not trigger a second LLM call.

F.2. In `policy/guard.py`, update the prohibited language term list to include the full set defined in `llm_synthesis_contract_v1.5.md` Section 6:
   `"Strength"`, `"Weakness"`, `"Outstanding"`, `"Deficiency"`, `"Below average"`, `"Underperformance"`, `"High potential"`, `"Top candidate"`, `"Risk factor"`, `"Admit"`, `"Reject"`, `"Likelihood"`.

F.3. In `policy/config.py`, confirm that prohibited language rules are externalized in the policy configuration structure and not hardcoded inline in guard logic.

**Explicit Boundaries:**
- No second LLM call is triggered by validation failure. Failure is terminal per application.
- Agent 13 does not correct LLM output. It only validates or rejects.
- `policy/guard.py` does not make network calls or LLM calls.
- No changes are made to authentication, routing, or persistence logic.

**Validation Checkpoint F:**
- Agent 13 rejects an LLM response with an invented `entity_id` not in the entity map.
- Agent 13 rejects an LLM response where a `question_groups` entry references a non-existent `theme_id`.
- Agent 13 rejects an LLM response containing any prohibited language term.
- Agent 13 rejects a structurally invalid (non-JSON or schema-nonconforming) LLM response.
- On rejection, `synthesis_records.policy_passed` is `false` and `policy_violations_log` is populated.
- On rejection, no second LLM call is made.
- On passing validation, `synthesis_records.policy_passed` is `true`.

---

## 4. Agent Pipeline Modifications

This section documents all agent-level changes derived from `agent_pipeline_spec_v1.5.md`.

### 4.1 Agents That Change

**Agent 3 — Personal Information Extractor:** Updated to extract and populate `identifiers.family_background` per `agent_pipeline_spec_v1.5.md` Section 3 (Agent 3). Must not infer missing family members. Must not normalize beyond explicit yes/no flags.

**Agent 4 — Academic Records Extractor:** Updated to separately populate `schooling_history[]` per `agent_pipeline_spec_v1.5.md` Section 3 (Agent 4). Must keep `academic_entries[]` and `schooling_history[]` distinct. No GPA conversion. No normalization. No merging.

**Agent 7 — Activity Extractor:** Updated to assign explicit `activity_type` classification per `agent_pipeline_spec_v1.5.md` Section 3 (Agent 7). Classification is deterministic and rule-based. Must not delegate to LLM.

**Agent 11 — Canonical Structure Assembler:** Updated to stamp `"canonical_version": "1.1"` and assemble the canonical model including all new v1.1 fields per `agent_pipeline_spec_v1.5.md` Section 3 (Agent 11). Must not produce ROS. Canonical remains presentation-agnostic.

**Agent 12 — Synthesis Agent:** Updated to receive entity-map-annotated canonical and produce structured `themes[]` and `question_groups[]` output per `agent_pipeline_spec_v1.5.md` Section 5. Exactly one LLM call. No additional calls.

**Agent 13 — Output Validation Filter:** Updated to validate structured ROS Page 4–5 output per `agent_pipeline_spec_v1.5.md` Section 6. Validates JSON structure, `theme_id` uniqueness, `referenced_entity_ids` existence, `question_groups.theme_id` linkage, prohibited language. No corrective LLM call on failure.

**Agent 0 — Pipeline Orchestrator:** Updated to incorporate the deterministic ROS projection step between Agent 11 and Agent 12, and the ROS assembly step after Agent 13 per `agent_pipeline_spec_v1.5.md` Section 3 (Agent 0). No extraction logic inside Agent 0.

### 4.2 Logic Added

- Deterministic `entity_id` assignment (projection layer, not an agent).
- Page 1–3 deterministic construction (projection layer).
- Span-based essay highlight computation (projection layer, Page 3).
- Structured LLM prompt requiring `themes[]` and `question_groups[]` output.
- `entity_id` reference validation in Agent 13.
- `theme_id` linkage validation in Agent 13.
- ROS assembly step merging Pages 1–3 and Pages 4–5.

### 4.3 Logic That Remains Unchanged

- Agents 1, 2, 5, 6, 8, 9, and 10: all responsibilities, input/output contracts, confidence discipline, and prohibited behaviors remain identical.
- The synchronous, sequential execution model of Agents 1–11.
- The single-call LLM invocation mechanism in `llm/client.py`.
- All policy guard rule categories not listed in Phase F.
- All confidence metadata propagation from extraction agents.

---

## 5. Canonical Model Updates

This section documents all canonical model changes derived from `canonical_model_philosophy_v1.5.md`.

### 5.1 Version Increment

Canonical version increments from `"1.0"` to `"1.1"`. This is reflected in the `CANONICAL_VERSION` constant and stamped by Agent 11 on all new canonical records. Existing stored records with `canonical_version: "1.0"` are not retroactively modified. The `canonical_version` check constraint defined in `database_schema_v1.md` must continue to accept both `"1.0"` and `"1.1"` format strings, as both match the `major.minor` pattern.

### 5.2 Additive Fields

The following fields are added to the canonical structure per `canonical_model_philosophy_v1.5.md` Sections 10.1, 10.2, and 10.3:

**`identifiers.family_background`:** A structured object with `father` and `mother` sub-objects, each containing `name`, `education`, `occupation`, `organization`. All sub-fields are nullable. Populated by Agent 3 from extracted document content. Non-evaluative. No inference of missing values.

**`schooling_history[]`:** A new collection of institutional affiliation records. Each entry includes `entry_id` (UUID), `level`, `school_name`, `board_name`, `location`, `confidence_score`. Populated by Agent 4 and assembled by Agent 11. Distinct from `academic_entries[]`. Collection-based. Deterministically ordered.

**`activity_type` on `activity_entries[]`:** An explicit classification field on each activity entry. Allowed values: `"extracurricular"`, `"co_curricular"`, `"leadership"`, `"other"`. Populated by Agent 7. Deterministic and rule-based. Non-evaluative.

### 5.3 Storage Guarantees

All Canonical v1.1 additions are stored within the existing `canonical_records.canonical_data` JSONB column. Because the column is JSONB, structural evolution is accommodated without schema migration per `canonical_model_philosophy_v1.5.md` Section 7. No new column, no new table, and no Alembic migration is required.

### 5.4 Preserved Invariants

As confirmed by `canonical_model_philosophy_v1.5.md` Section 13:

- Collection-based structure is preserved. No collection may be collapsed into fixed keys.
- No fixed academic keys (`class_10`, `class_12`, `grade_11`, etc.) are introduced.
- Canonical remains independent from ROS. No page grouping, theme grouping, or UI ordering logic is embedded in canonical.
- No evaluation logic is introduced. No scoring, ranking, normalization, strength/weakness flags, or predictive fields.
- No schema migration is required.
- Canonical v1.1 is additive only. No existing field semantics are altered.

---

## 6. LLM Synthesis Contract Updates

This section documents all LLM contract changes derived from `llm_synthesis_contract_v1.5.md`.

### 6.1 Updated Input Structure

The LLM receives a projection-cleaned canonical representation (v1.1) with `entity_id` values assigned. Input collections passed to the LLM per `llm_synthesis_contract_v1.5.md` Section 3:

- `academic_entries[]`
- `schooling_history[]` (added in v1.5; resolves prior audit mismatch)
- `test_entries[]`
- `essay_entries[]`
- `activity_entries[]` (including `activity_type`)
- `identifiers.family_background`

Collections are passed in canonical array order, without sorting, collapsing, or normalization. The LLM does not receive confidence scores, integrity metadata, raw layout blocks, or raw PDF text.

### 6.2 Required Output Schema

The LLM must return strictly valid JSON matching the schema defined in `llm_synthesis_contract_v1.5.md` Section 4:

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

This output corresponds to ROS Page 4 (`page_4_focus_themes`) and ROS Page 5 (`page_5_question_groups`).

### 6.3 Entity Reference Rules

- The LLM must reference only `entity_id` values provided in the input.
- Each `referenced_entity_id` must exist in the deterministic entity map.
- The LLM must not invent new entity IDs.
- Theme-level `referenced_entity_ids` must correspond to real extracted canonical entities.

### 6.4 Validation Constraints

Per `llm_synthesis_contract_v1.5.md` Section 7, Agent 13 enforces:
1. JSON structure matches the output contract.
2. All `theme_id` values are unique.
3. All `referenced_entity_ids` exist in the deterministic entity map.
4. All `question_groups.theme_id` values exist in the `themes[]` array.
5. No invented entity IDs.
6. No prohibited language (full term list in `llm_synthesis_contract_v1.5.md` Section 6).

Validation failure is terminal: the application is marked failed. No corrective LLM call is triggered.

### 6.5 Single-Call Invariant Enforcement

Exactly one LLM call per application. Stage 1.5 introduces no multi-step reasoning, theme refinement pass, question refinement pass, or secondary model usage. This invariant is absolute per `llm_synthesis_contract_v1.5.md` Section 10 and `architecture_lock.md` Section 2.2.

---

## 7. ROS Projection Layer

This section documents the deterministic projection layer derived from `ROSv1.md`, `system_overview_v1.5.md`, and `agent_pipeline_spec_v1.5.md`.

### 7.1 Overview

The ROS projection layer is a deterministic, LLM-free module that consumes Canonical v1.1 and produces ROS Pages 1–3. It is introduced in `projection/ros_projector.py`. It is not a microservice, not an agent, and not an async worker. It executes synchronously within the request lifecycle.

### 7.2 Deterministic Page 1–3 Construction

Page construction follows the canonical source mapping defined in `ROSv1.md` and confirmed in `system_overview_v1.5.md` Section 4.2:

| ROS Page | Source | Determinism |
|---|---|---|
| Page 1 — Background Profile | `identifiers`, `identifiers.family_background`, `schooling_history[]` | Fully deterministic |
| Page 2 — Academic + Engagement | `academic_entries[]`, `test_entries[]`, `activity_entries[]` grouped by `activity_type` | Fully deterministic |
| Page 3 — Essays + Highlights | `essay_entries[]` with deterministic span highlight computation | Fully deterministic |

### 7.3 Entity Anchoring

Entity IDs are assigned per the algorithm in `agent_pipeline_spec_v1.5.md` Section 4A:

- Each canonical collection is independently indexed using canonical array order.
- Prefix-based `entity_id` values are generated: `ACA-###`, `TEST-###`, `ESS-###`, `ACT-###`, `SCH-###`.
- `LEAD-###` is used for leadership entries in the Page 2 leadership_roles group.
- `TEST-ADD-###` is used for additional test entries in the Page 2 additional_tests group.
- Assignment is stable across identical canonical input.
- `entity_id` values are projection-layer metadata. They are not stored in canonical.

### 7.4 Highlight Spans

Essay highlights in Page 3 are computed deterministically per `ROSv1.md` Page 3 specification:

- For each essay in `essay_entries[]`, scan the `full_text` for tokens matching canonical entity content from `academic_entries[]`, `activity_entries[]`, `test_entries[]`, and `schooling_history[]`.
- Express each matched span as `{ "start_char": N, "end_char": M, "referenced_entity_ids": ["entity_id"] }`.
- Span offsets are character positions in the `full_text` string.
- `referenced_entity_ids` within highlights must be valid `entity_id` values present in the entity map.
- No LLM involvement in highlight generation. No inference. No evaluation.

### 7.5 Merge with LLM Output

After Agent 13 validates the LLM output, `ros/assembler.py` merges:

- Pages 1–3 from the projection layer.
- Pages 4–5 (`themes[]` and `question_groups[]`) from the validated LLM output.
- `report_metadata` containing `application_number`, `generated_at`, `canonical_version`, and `report_version: "ROS_v1"`.

The merged document is the full ROS v1 artifact, stored in `synthesis_records.synthesis_output`.

### 7.6 LLM-Free Guarantee

The projection layer (`projection/ros_projector.py`) and ROS assembler (`ros/assembler.py`) are LLM-free. Their operation must be verifiable without any LLM endpoint connection. No network call is made by either module.

---

## 8. Schema Verification

This section confirms the database schema position for Stage 1.5, derived from `database_schema_v1.md` and `database_schema_v1.5.md`.

### 8.1 No New Tables

Stage 1.5 introduces no new database tables. The four-table structure from Stage 1 is preserved: `users`, `applications`, `canonical_records`, `synthesis_records`. Per `database_schema_v1.5.md` Section 2: "No new tables are added in Stage 1.5."

### 8.2 No New Columns

Stage 1.5 introduces no new columns on any table. Per `database_schema_v1.5.md`:
- `users`: unchanged from Stage 1.
- `applications`: unchanged from Stage 1.
- `canonical_records`: unchanged from Stage 1.
- `synthesis_records`: unchanged from Stage 1. No new columns added. No new constraints added.

### 8.3 JSONB Structure Change Only

The sole database-layer evolution in Stage 1.5 is the internal JSON structure of `synthesis_records.synthesis_output` (JSONB column). Per `database_schema_v1.5.md` Section 7:

The Stage 1 structure:
```json
{ "snapshot": "string", "discussion_focus_areas": "...", "suggested_questions": "...", "canonical_version_ref": "string" }
```
Is replaced by the full ROS v1 structure:
```json
{ "report_metadata": {...}, "page_1_background_profile": {...}, "page_2_academic_and_engagement": {...}, "page_3_essays": {...}, "page_4_focus_themes": {...}, "page_5_question_groups": {...} }
```

The JSONB column type, column name (`synthesis_output`), table name (`synthesis_records`), and all table-level constraints remain unchanged.

### 8.4 Alembic Migration NOT Required

Because `synthesis_output` is JSONB and the change is to the internal JSON document structure only (not to the column type, column name, or table structure), no Alembic migration script is required or permitted for Stage 1.5. Per `database_schema_v1.5.md` Section 7: "No migration required." Per `architecture_lock.md` Section 2.6: "No schema migrations introduced." The Alembic revision history established in Stage 1 remains unchanged.

---

## 9. Infrastructure Freeze Verification

This section confirms that all Stage 1 infrastructure invariants are preserved in Stage 1.5, derived from `architecture_lock.md` and `env_config_spec.md`.

### 9.1 Container Topology Unchanged

Per `architecture_lock.md` Section 2.5: "Docker topology unchanged. Services unchanged. No additional containers." The Stage 1 topology of exactly two containers (one FastAPI API container and one PostgreSQL container) is preserved in Stage 1.5 without modification. No new container is introduced for projection, assembly, caching, or any other purpose.

### 9.2 No New Environment Variables

Per `architecture_lock.md` Section 2.5: "No new environment variables introduced for Stage 1.5." The complete set of environment variables remains as defined in `env_config_spec.md`. No new variable is introduced to configure projection behavior, ROS output format, or LLM schema validation. All twelve environment variables defined in Stage 1 remain the complete and exclusive configuration set.

### 9.3 No Async Drivers

Per `architecture_lock.md` Section 2.4: "The system remains fully synchronous." The psycopg2 synchronous database driver is unchanged. The synchronous `httpx` LLM client is unchanged. No async driver, coroutine, asyncio event loop, or async framework is introduced.

### 9.4 No Redis

Per `architecture_lock.md` Section 2.4: Redis is not introduced. No Redis container, no Redis client library, and no Redis configuration variable is added in Stage 1.5.

### 9.5 No Job Queues

Per `architecture_lock.md` Section 2.4: No background workers, Celery, RQ, Kafka, or task scheduler is introduced. The synchronous single-request-lifecycle execution model is preserved.

### 9.6 No Additional Frameworks

No LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent orchestration framework is introduced. The LLM integration remains a direct synchronous HTTP call via `llm/client.py` as established in Stage 1.

---

## 10. Test Plan

This section defines the validation test plan for Stage 1.5. All tests are derived from the contract documents. Tests must pass before Stage 1.5 is declared complete.

### 10.1 Entity ID Determinism Tests

- Given a canonical v1.1 document with N `academic_entries[]`, verify that the projection layer assigns `ACA-001` through `ACA-{N}` in canonical array order.
- Given a canonical v1.1 document with M `schooling_history[]` entries, verify that the projection layer assigns `SCH-001` through `SCH-{M}` in canonical array order.
- Given identical canonical input passed to the projection layer twice, verify that the complete `entity_id` maps are identical between the two invocations.
- Verify that inserting a new entry at the beginning of `academic_entries[]` shifts all subsequent `ACA-###` assignments by one (reflecting canonical order dependency).
- Verify that `entity_id` values are not present in the canonical representation returned from Agent 11. Canonical must not contain `entity_id` fields.
- Verify that `entry_id` values (UUID) on canonical entries are unaffected by projection.

### 10.2 Span Correctness Tests

- Given an essay with known `full_text` content and a canonical entity whose label text appears within it, verify that the projection layer produces a highlight span with correct `start_char` and `end_char` character offsets.
- Verify that highlight `referenced_entity_ids` within Page 3 essays contain only `entity_id` values present in the deterministic entity map.
- Verify that essays with no cross-referencing canonical entity tokens produce an empty `highlights` array (not null, not absent).
- Verify that highlight computation does not modify `full_text` content.

### 10.3 Reference Integrity Tests

- Verify that all `referenced_entity_ids` in Page 4 `themes[]` exist in the deterministic entity map produced by the projection layer.
- Verify that all `theme_id` values referenced in Page 5 `question_groups[]` exist in the `themes[]` array.
- Verify that Agent 13 rejects an LLM response containing a `referenced_entity_id` not present in the entity map, sets `policy_passed` to `false`, and does not produce a second LLM call.
- Verify that Agent 13 rejects an LLM response where a `question_groups` item references a non-existent `theme_id`, sets `policy_passed` to `false`, and does not produce a second LLM call.

### 10.4 LLM Output Schema Validity Tests

- Verify that a well-formed LLM response containing `themes[]` and `question_groups[]` passes Agent 13 JSON structure validation.
- Verify that a response missing the `themes` key is rejected by Agent 13.
- Verify that a response missing the `question_groups` key is rejected by Agent 13.
- Verify that a response where `themes` is not an array is rejected by Agent 13.
- Verify that a response containing duplicate `theme_id` values is rejected by Agent 13.
- Verify that a response containing any prohibited language term (as listed in `llm_synthesis_contract_v1.5.md` Section 6) is rejected by Agent 13.

### 10.5 Single LLM Call Invariant Tests

- Confirm via application log output that exactly one LLM invocation start event and exactly one LLM invocation completion event appear per pipeline run.
- Confirm that no LLM call is made by the projection layer (`projection/ros_projector.py`).
- Confirm that no LLM call is made by the ROS assembler (`ros/assembler.py`).
- Confirm that Agent 13 validation failure produces no second LLM call.
- Confirm that no LLM framework import (LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel) is present in any Python module.

### 10.6 Canonical Preservation Tests

- A complete pipeline run produces a `canonical_records` row with `canonical_version = "1.1"`.
- The `canonical_data` JSONB document contains all required top-level collections: `identifiers`, `academic_entries`, `schooling_history`, `test_entries`, `essay_entries`, `activity_entries`, `timeline_entries`, `cross_references`, `integrity_report`, `extraction_confidence`.
- No fixed academic-level key (`class_10`, `class_12`, `grade_11`, etc.) appears in the canonical JSONB document.
- All `activity_entries[]` items contain `activity_type` with a value in the permitted set.
- `identifiers.family_background` is present in the JSONB document and its sub-fields are null-safe.
- `schooling_history[]` is present as an array in the JSONB document. It may be empty but must not be absent.
- No evaluative field (scoring, ranking, strength/weakness flags) is present in the canonical JSONB document.
- `entity_id` does not appear as a field in any canonical entry. Only `entry_id` (UUID) is present on canonical entries.
- After a projection run, a re-read of the `canonical_records.canonical_data` JSONB document is identical to its pre-projection state (projection does not mutate canonical).

### 10.7 ROS JSON Structure Correctness Tests

- `synthesis_records.synthesis_output` contains exactly the six required top-level keys: `report_metadata`, `page_1_background_profile`, `page_2_academic_and_engagement`, `page_3_essays`, `page_4_focus_themes`, `page_5_question_groups`.
- `report_metadata.report_version` equals `"ROS_v1"`.
- `report_metadata.canonical_version` matches the associated `canonical_records.canonical_version`.
- `page_1_background_profile.schooling_history` entries contain `entity_id` values in `SCH-###` format.
- `page_2_academic_and_engagement.academic_records` entries contain `entity_id` values in `ACA-###` format.
- `page_2_academic_and_engagement` activity groups are populated in accordance with canonical `activity_type`.
- `page_3_essays` entries contain `entity_id` values in `ESS-###` format and a `highlights` array.
- `page_4_focus_themes.themes` is a non-empty array with valid `theme_id` values in `THEME-###` format.
- `page_5_question_groups.question_groups` is a non-empty array where every entry references a valid `theme_id` from `page_4_focus_themes`.
- GET `/applications/{id}` returns the stored `synthesis_output` (ROS v1) without re-invoking the pipeline or LLM.

### 10.8 Schema and Infrastructure Confirmation Tests

- `alembic current` shows the same head revision as Stage 1. No new migration has been applied.
- Exactly four tables exist in the PostgreSQL database: `users`, `applications`, `canonical_records`, `synthesis_records`.
- No new column exists on any table beyond those defined in `database_schema_v1.md`.
- `docker-compose up --build` completes without error.
- Exactly two containers are running after startup.
- No third container is present.
- No Redis, Celery, RQ, Kafka, MinIO, NGINX, or cloud provider integration is present in any configuration, container definition, or Python module.

---

## 11. Stage 1.5 Completion Criteria

Stage 1.5 is declared complete only when all of the following acceptance conditions are satisfied.

### 11.1 Canonical v1.1 Correctness Checks

- All new pipeline runs produce `canonical_records` rows with `canonical_version = "1.1"`.
- `canonical_data` JSONB contains `identifiers.family_background` with the correct structure as defined in `canonical_model_philosophy_v1.5.md` Section 10.1.
- `canonical_data` JSONB contains `schooling_history[]` as a distinct collection with entry structure as defined in `canonical_model_philosophy_v1.5.md` Section 10.2.
- All `activity_entries[]` items in `canonical_data` contain `activity_type` with a value from the permitted set as defined in `canonical_model_philosophy_v1.5.md` Section 10.3.
- No evaluative field is present in any `canonical_data` JSONB document.
- No fixed academic-level key is present as a top-level or nested key in any `canonical_data` JSONB document.
- `entity_id` is absent from all `canonical_data` JSONB documents.
- Canonical array insertion order is preserved as produced by Agent 11.

### 11.2 ROS v1 Output Correctness Checks

- A complete pipeline run with a real PDF produces a `synthesis_records` row with `synthesis_output` containing all six top-level ROS v1 keys.
- `report_metadata.report_version` equals `"ROS_v1"` in every stored ROS artifact.
- `report_metadata.canonical_version` matches the associated `canonical_records.canonical_version` in every stored ROS artifact.
- All `entity_id` values in Page 1, Page 2, and Page 3 conform to the prefix format defined in `agent_pipeline_spec_v1.5.md` Section 4A.
- Activity grouping in Page 2 strictly reflects canonical `activity_type` values. No activity appears in a group inconsistent with its canonical classification.
- All `highlighted` span offsets in Page 3 are valid character positions within the corresponding essay `full_text` strings.
- All `referenced_entity_ids` in Page 3 highlights, Page 4 themes, and Page 5 question groups exist in the deterministic entity map for their respective application.
- All `question_groups` entries in Page 5 reference valid `theme_id` values present in Page 4.
- No prohibited language term appears in any stored ROS artifact.
- GET `/applications/{id}` returns the complete stored ROS v1 artifact without re-invoking the pipeline.

### 11.3 Single LLM Call Confirmation

- Log output for every completed pipeline run contains exactly one LLM invocation start event and exactly one LLM invocation completion event, with no retry and no secondary invocation.
- No LLM call is made during projection layer execution.
- No LLM call is made during ROS assembly execution.
- No LLM call is made during Agent 13 validation failure handling.
- No LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent framework import exists in any module.

### 11.4 Validation and Policy Guard Checks

- Agent 13 correctly rejects all LLM responses with invented `entity_id` values.
- Agent 13 correctly rejects all LLM responses with broken `theme_id` linkage in `question_groups`.
- Agent 13 correctly rejects all LLM responses containing prohibited language.
- Agent 13 correctly rejects all structurally non-conforming LLM responses.
- On every rejection, `synthesis_records.policy_passed` is `false` and `policy_violations_log` is populated with a structured reason.
- On every rejection, no second LLM call is triggered.

### 11.5 Schema Stability Checks

- `alembic current` shows the Stage 1 head revision. No new Alembic revision has been applied.
- Exactly four tables exist: `users`, `applications`, `canonical_records`, `synthesis_records`.
- All columns on all tables match the definitions in `database_schema_v1.md`. No new column exists.
- `synthesis_records.synthesis_output` is JSONB type. Column name and type are unchanged.
- `canonical_records.canonical_data` is JSONB type. Column name and type are unchanged.
- All check constraints, foreign key constraints, and indexes from Stage 1 remain active and unmodified.

### 11.6 Infrastructure Freeze Confirmation

- `docker-compose up --build` completes without error.
- Exactly two containers are running: API container and PostgreSQL container.
- No third container of any kind is present.
- The complete environment variable set is the twelve variables defined in `env_config_spec.md`. No new variable has been added.
- No async driver, asyncio usage, background thread, job queue, or deferred execution mechanism exists in any Python module.
- No Redis, Celery, RQ, Kafka, MinIO, NGINX, Kubernetes, or cloud provider integration exists in any configuration, container definition, or Python module.
- `DATABASE_URL` continues to use the synchronous psycopg2 driver prefix.

---

## Constraint Check

The following table confirms that this migration plan fully complies with all architectural invariants from `architecture_lock.md`. Each confirmation is based on explicit evidence within the document sections above.

| Constraint | Status | Evidence |
|---|---|---|
| **Deterministic-first preserved** | ✅ | Section 2.2 explicitly confirms Agents 1, 2, 5, 6, 8, 9, 10 are unchanged. Phase B updates to Agents 3, 4, 7, 11 are extraction-only with no LLM involvement. Phase D defines the projection layer as LLM-free. No section introduces LLM involvement before canonical assembly. |
| **Single LLM call preserved** | ✅ | Phase C explicitly states exactly one LLM call per application, no retry, no fallback, no secondary pass. Validation Checkpoint C requires confirmation of exactly one invocation. Section 11.3 requires log-based confirmation of single invocation. Phase F states rejection failure is terminal with no corrective LLM call. |
| **Canonical–presentation separation enforced** | ✅ | Phase D explicitly prohibits projection from mutating canonical. Phase B explicitly states Agent 11 must not produce ROS. Section 5.4 confirms all canonical invariants are preserved. Section 7 confirms projection derives from canonical without reshaping it. Validation Checkpoint D requires post-projection canonical identity check. |
| **No evaluation logic introduced** | ✅ | No section introduces scoring, ranking, normalization, strength/weakness labeling, admissions commentary, or predictive fields. Phase B prohibits evaluative classification in activity_type assignment. Phase F enforces prohibited language detection. Section 11.2 requires absence of prohibited language in stored ROS artifacts. |
| **Collection-based canonical preserved** | ✅ | Section 5.4 confirms all collection discipline rules from `canonical_model_philosophy_v1.5.md` Section 13. Section 10.6 requires all canonical collection fields to be arrays. Phase A adds `schooling_history[]` as a new collection, not a fixed key. No section collapses any collection into fixed-key alternatives. |
| **No rigid key paths introduced** | ✅ | Phase A explicitly prohibits introduction of fixed academic-level keys. Section 10.6 requires validation that no fixed academic-level key appears in canonical JSONB. Section 11.1 repeats this requirement as a completion criterion. |
| **No async introduced** | ✅ | Section 9.3 confirms psycopg2 synchronous driver is unchanged. Section 9.4–9.5 confirm no Redis and no job queues. Phase E explicitly states Agent 0 must not introduce async mechanisms. Section 11.6 requires confirmation that no async driver, asyncio usage, or deferred execution mechanism exists. |
| **Infrastructure freeze preserved** | ✅ | Section 9.1 confirms two-container topology unchanged. Section 9.2 confirms no new environment variables. Sections 9.3–9.6 confirm no async drivers, no Redis, no job queues, no additional frameworks. Section 11.6 requires confirmation that exactly two containers are running and no third container is present. |
| **No schema migration introduced** | ✅ | Section 8.4 explicitly states no Alembic migration is required or permitted. Section 8.2 confirms no new columns. Section 8.1 confirms no new tables. Section 11.5 requires `alembic current` to show the Stage 1 head revision unchanged. |
| **No additional LLM frameworks introduced** | ✅ | Phase C confirms `llm/client.py` is used without modification. Section 10.5 requires confirmation that no LangChain, LangGraph, AutoGen, CrewAI, or Semantic Kernel import is present in any module. Section 11.3 repeats this as a completion criterion. |

---

*End of `stage_1_5_migration_plan.md`.*

*Document Version: 1.0 | Stage: 1.5 — ROS v1 Integrated Structured Output | Governing Architecture Version: architecture_lock.md*
