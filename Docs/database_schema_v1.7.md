# `database_schema_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. Schema Version Declaration

| Property | Value |
|---|---|
| Schema version | `1.7` |
| Canonical version compatibility | `1.1` |
| Stage | Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis |
| Status | Frozen — no structural changes introduced in Stage 1.7 |

### Stability Statement

Stage 1.7 introduces no database schema changes. No new tables, no new columns, no new constraints, no new indexes, and no Alembic migrations are required. The four-table schema defined in this document is the complete and current schema. All Stage 1.7 additions to the pipeline are logical-layer only and do not touch the persistence layer structure.

The `synthesis_output` JSONB column in `synthesis_records` absorbs the Stage 1.7 output change — the internal JSON structure now stores the ROS v1 five-page artifact, and may optionally include signal data — without any column or table modification. This is by design: JSONB storage decouples persistence structure from application output evolution.

The signal storage decision — whether interpreted signals are embedded in `synthesis_output` alongside the ROS artifact — must be made explicitly before Stage 1.7 goes to production. It is defined in Section 8 of this document.

---

## 2. Database Engine Specification

### PostgreSQL Version

PostgreSQL 15 or later is required. No PostgreSQL 15-specific features are used; however, PostgreSQL 15 is the minimum baseline to ensure stable JSONB indexing behavior, UUID support, and constraint enforcement semantics. Earlier versions are not supported.

### Required Extensions

| Extension | Purpose |
|---|---|
| `uuid-ossp` or `pgcrypto` | UUID generation via `gen_random_uuid()` or `uuid_generate_v4()` |

All primary keys are UUID type with database-level default generation. UUID generation must occur at the database level, not the application layer, to ensure consistency. PostgreSQL 13 and later expose `gen_random_uuid()` natively via `pgcrypto`. Either extension is acceptable. The implementation must confirm which function is available and use it consistently across all tables.

### JSONB Usage Rationale

JSONB is used in three columns: `canonical_records.canonical_data`, `synthesis_records.synthesis_output`, and `synthesis_records.policy_violations_log`.

JSONB is selected over TEXT or JSON for the following reasons:

- JSONB is stored in a decomposed binary format, enabling key-level indexing and querying if required in later stages without schema migration
- JSONB validates JSON structure at write time, preventing malformed documents from being persisted
- JSONB supports GIN indexing for efficient key-existence queries when needed
- JSONB does not impose a relational schema onto collection-based canonical data, preserving the architectural requirement that canonical structure remains extensible and not storage-bound

Relational decomposition of canonical data into separate tables is intentionally not performed. This decision is governed by `canonical_model_philosophy_v1.7.md`, which explicitly states that canonical structure must be collection-based and not tightly coupled to database storage structure. Decomposition would require separate tables for each collection type, additional join tables for nested structures, and schema migrations for every new field — all of which are incompatible with the extensibility model.

### Encoding

| Property | Value |
|---|---|
| Database encoding | UTF-8 |
| Collation | `en_US.UTF-8` or locale-equivalent |
| Character type | UTF-8 |

UTF-8 is required because application documents contain non-ASCII characters including personal names, academic subject names, school names, and institutional identifiers from diverse linguistic contexts.

---

## 3. Table Definitions

### 3.1 Table: `users`

**Purpose:** Stores authenticated user accounts. Users are institutional actors — admins or interviewers — who interact with the system.

#### Column Definitions

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `email` | `VARCHAR(320)` | NOT NULL | — | RFC 5321 maximum email length |
| `password_hash` | `VARCHAR(255)` | NOT NULL | — | bcrypt hash output |
| `role` | `VARCHAR(50)` | NOT NULL | — | Constrained by check constraint |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

`id`

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_users_email` | `email` |

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_users_role` | `role IN ('admin', 'interviewer')` |

Role expansion beyond `admin` and `interviewer` must not be introduced in Stage 1.7.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_users` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_users_email` | `email` | B-tree (implicit via unique constraint) | Login and registration lookups |

#### Cascade Behavior

No cascade rules apply at this table. Users are not deleted in Stage 1.7.

#### Relationship Cardinality

One user may be associated with zero or many application records via `applications.uploaded_by`.

---

### 3.2 Table: `applications`

**Purpose:** Stores application submission records. Each record corresponds to a single uploaded PDF and tracks pipeline execution status and aggregate confidence.

#### Column Definitions

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `uploaded_by` | `UUID` | NOT NULL | — | Foreign key to `users.id` |
| `file_path` | `VARCHAR(512)` | NOT NULL | — | Absolute local path to stored PDF |
| `pipeline_status` | `VARCHAR(50)` | NOT NULL | `'processing'` | Pipeline execution state |
| `pipeline_confidence` | `NUMERIC(5,4)` | NULL | — | Aggregate confidence 0.0000–1.0000; null until pipeline completes |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

`id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_applications_uploaded_by` | `uploaded_by` | `users(id)` | RESTRICT | CASCADE |

Deletion of a user is restricted if associated application records exist. This prevents orphaned application records without cascade deletion silently destroying pipeline outputs.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_applications_pipeline_status` | `pipeline_status IN ('processing', 'complete', 'failed')` |
| `chk_applications_pipeline_confidence` | `pipeline_confidence IS NULL OR (pipeline_confidence >= 0.0000 AND pipeline_confidence <= 1.0000)` |

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_applications` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `idx_applications_uploaded_by` | `uploaded_by` | B-tree | Foreign key join; retrieval of all applications by user |

#### Relationship Cardinality

- Many applications belong to one user (many-to-one with `users`)
- One application has exactly one canonical record (one-to-one with `canonical_records`)
- One application has exactly one synthesis record (one-to-one with `synthesis_records`)

---

### 3.3 Table: `canonical_records`

**Purpose:** Stores the versioned canonical representation produced by the deterministic extraction pipeline (Agents 1–11). This is the authoritative extracted form of the application and the source for all downstream processing.

#### Column Definitions

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `application_id` | `UUID` | NOT NULL | — | Foreign key to `applications.id`; unique (one-to-one) |
| `canonical_version` | `VARCHAR(20)` | NOT NULL | — | Must match `CANONICAL_VERSION` constant at assembly time |
| `canonical_data` | `JSONB` | NOT NULL | — | Full collection-based canonical representation v1.1 |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

`id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_canonical_records_application_id` | `application_id` | `applications(id)` | CASCADE | CASCADE |

Deletion of an application cascades to its canonical record. A canonical record without an application is a semantic error.

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_canonical_records_application_id` | `application_id` |

Enforces the one-to-one relationship between applications and canonical records at the database level.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_canonical_records_version_format` | `canonical_version ~ '^\d+\.\d+$'` |

Enforces the `major.minor` version string format (e.g. `"1.1"`). Prevents unversioned or malformed version strings from being persisted.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_canonical_records` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_canonical_records_application_id` | `application_id` | B-tree (implicit via unique constraint) | One-to-one join; foreign key enforcement |
| `idx_canonical_records_version` | `canonical_version` | B-tree | Version-scoped queries and migration tooling |

GIN indexing on `canonical_data` is not mandated in Stage 1.7. Access pattern is full-document retrieval by `application_id`. If key-level sub-document queries emerge in later stages, a GIN index may be added without schema restructuring.

#### Relationship Cardinality

One canonical record belongs to exactly one application.

---

### 3.4 Table: `synthesis_records`

**Purpose:** Stores the final ROS v1 artifact produced by the pipeline after both LLM calls and both Policy Guard validations complete successfully. Also stores the policy validation result and any violation metadata.

#### Column Definitions

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `application_id` | `UUID` | NOT NULL | — | Foreign key to `applications.id`; unique (one-to-one) |
| `synthesis_output` | `JSONB` | NOT NULL | — | Full ROS v1 artifact; optionally includes signal data (see Section 8) |
| `policy_passed` | `BOOLEAN` | NOT NULL | — | True if output passed all policy validation rules |
| `policy_violations_log` | `JSONB` | NULL | — | Structured violation metadata if validation failed; null if policy_passed is true |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

`id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_synthesis_records_application_id` | `application_id` | `applications(id)` | CASCADE | CASCADE |

Cascade delete is consistent with `canonical_records`. A synthesis record without an application is a semantic error.

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_synthesis_records_application_id` | `application_id` |

Enforces the one-to-one relationship at the database level.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_synthesis_records_violations_consistency` | `policy_passed = TRUE AND policy_violations_log IS NULL OR policy_passed = FALSE` |

When `policy_passed` is `TRUE`, `policy_violations_log` must be `NULL`. A passed output carries no violations log. The `FALSE` case is intentionally permissive to allow for edge cases where violation detection occurs but log assembly fails in a recoverable way.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_synthesis_records` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_synthesis_records_application_id` | `application_id` | B-tree (implicit via unique constraint) | One-to-one join; foreign key enforcement |
| `idx_synthesis_records_policy_passed` | `policy_passed` | B-tree | Operational queries filtering by policy compliance |

#### Relationship Cardinality

One synthesis record belongs to exactly one application.

---

## 4. Relationship Graph

### One-to-Many Relationships

| Parent Table | Child Table | Join Column | Cardinality |
|---|---|---|---|
| `users` | `applications` | `applications.uploaded_by → users.id` | One user may upload many applications |

### One-to-One Relationships

| Table A | Table B | Join Column | Enforcement Mechanism |
|---|---|---|---|
| `applications` | `canonical_records` | `canonical_records.application_id → applications.id` | Unique constraint on `canonical_records.application_id` |
| `applications` | `synthesis_records` | `synthesis_records.application_id → applications.id` | Unique constraint on `synthesis_records.application_id` |

### Deletion Behavior

| Relationship | On Delete | Rationale |
|---|---|---|
| `users` → `applications` | RESTRICT | Prevents accidental deletion of a user that owns application records. Requires explicit application handling before user removal. |
| `applications` → `canonical_records` | CASCADE | Canonical record is meaningless without its application context. Deletion of an application removes its canonical output atomically. |
| `applications` → `synthesis_records` | CASCADE | Synthesis record is meaningless without its application context. Same rationale as canonical cascade. |

`SET NULL` and `SET DEFAULT` deletion behaviors are not used. These would create orphaned records with undefined pipeline state.

---

## 5. JSONB Governance

### 5.1 `canonical_records.canonical_data`

Stores the full canonical representation v1.1 assembled by Agent 11. The complete top-level structure expected within this column:

| Top-Level Key | Value Type | Required |
|---|---|---|
| `canonical_version` | string | Yes |
| `identifiers` | object | Yes |
| `academic_entries` | array | Yes |
| `schooling_history` | array | Yes |
| `test_entries` | array | Yes |
| `essay_entries` | array | Yes |
| `activity_entries` | array | Yes |
| `timeline_entries` | array | Yes |
| `cross_references` | object | Yes |
| `integrity_report` | object | Yes |
| `extraction_confidence` | object | Yes |

All array fields represent collections. None may be collapsed into a singular object or replaced with fixed-key maps. Structural validation of the JSONB document is the responsibility of the Pydantic models in `canonical/model.py`. The database stores the document without enforcing internal structure via database-level constraints. The `canonical_version` column acts as a discriminator for application-layer version handling.

### 5.2 `synthesis_records.synthesis_output`

Stores the complete ROS v1 artifact assembled by the ROS Assembly Step. The top-level structure:

| Top-Level Key | Value Type | Required |
|---|---|---|
| `report_metadata` | object | Yes |
| `page_1_background_profile` | object | Yes |
| `page_2_academic_and_engagement` | object | Yes |
| `page_3_essays` | object | Yes |
| `page_4_focus_themes` | object | Yes |
| `page_5_question_groups` | object | Yes |
| `signal_data` | object | No — see Section 8 |

The second-level structure of each page key is as follows:

**`report_metadata`**: `application_id` (string), `generated_at` (ISO-8601 timestamp), `canonical_version` (string), `report_version` (string, always `"ROS_v1"`)

**`page_1_background_profile`**: `identity` object (application_id, full_name, date_of_birth, preferred_major), `family_background` object (father and mother sub-objects with name, education, field_of_employment, organization, designation), `schooling_history` array (entity_id, level, school_name, board_name, location)

**`page_2_academic_and_engagement`**: `academic_records` array (entity_id, level, school_name, board, year, grading_mode, overall_score, subjects array), `standardized_tests` array (entity_id, name, overall_score, percentile, rank, sections array), `extracurricular_activities` array (entity_id, name, position, level, duration_years), `co_curricular_activities` array (same structure), `leadership_roles` array (entity_id, position, level, duration_years)

**`page_3_essays`**: `essays` array (entity_id, prompt, full_text, word_count, highlights array with start_char, end_char, referenced_entity_ids)

**`page_4_focus_themes`**: `themes` array (theme_id, title, description, referenced_entity_ids)

**`page_5_question_groups`**: `question_groups` array (theme_id, group_title, questions array of strings)

Full field-level schemas for all pages are defined in `ROS_v1.7.md`.

Pages 1–3 are produced by the deterministic ROS projection layer. Pages 4–5 are produced by LLM Call 2 (Agent 16) and validated by the Policy Guard before inclusion. The full ROS v1 page schemas are defined in `ROS_v1.7.md`.

The `signal_data` key is conditionally present based on the signal storage decision defined in Section 8. If present, its structure is:

```json
{
  "signal_data": {
    "deterministic_signals": [...],
    "interpreted_signals": [...]
  }
}
```

If absent, the `synthesis_output` document contains only the six ROS keys listed above.

### 5.3 `synthesis_records.policy_violations_log`

When populated, stores structured violation metadata from Policy Guard validation. Raw prohibited text is not stored — only structured metadata describing what was detected and what action was taken.

Expected structure per violation entry:

| Field | Type | Description |
|---|---|---|
| `rule_id` | string | Identifier for the violated rule |
| `rule_set_name` | string | Name of the rule set (e.g. `"prohibited_language"`, `"entity_id_validation"`) |
| `field_reference` | string | The output field in which the violation was detected |
| `action_taken` | string | `"reject"` — the only permitted action in Stage 1.7 |
| `severity` | string | Severity classification of the violation |

In Stage 1.7, all Policy Guard validation failures result in pipeline abort and full output rejection. The `action_taken` value is always `"reject"`. No sanitization path exists.

---

## 6. Indexing Strategy

### Mandatory Indexes

| Index Name | Table | Column(s) | Type | Rationale |
|---|---|---|---|---|
| `pk_users` | `users` | `id` | B-tree (PK) | Primary key lookup |
| `uq_users_email` | `users` | `email` | B-tree (unique) | Login and registration lookup |
| `pk_applications` | `applications` | `id` | B-tree (PK) | Primary key lookup |
| `idx_applications_uploaded_by` | `applications` | `uploaded_by` | B-tree | Foreign key join; user's application list |
| `pk_canonical_records` | `canonical_records` | `id` | B-tree (PK) | Primary key lookup |
| `uq_canonical_records_application_id` | `canonical_records` | `application_id` | B-tree (unique) | One-to-one join; foreign key enforcement |
| `idx_canonical_records_version` | `canonical_records` | `canonical_version` | B-tree | Version-scoped queries; migration tooling |
| `pk_synthesis_records` | `synthesis_records` | `id` | B-tree (PK) | Primary key lookup |
| `uq_synthesis_records_application_id` | `synthesis_records` | `application_id` | B-tree (unique) | One-to-one join; foreign key enforcement |
| `idx_synthesis_records_policy_passed` | `synthesis_records` | `policy_passed` | B-tree | Policy compliance filtering |

### Optional JSONB Indexing

No GIN index on `canonical_data` or `synthesis_output` is mandated in Stage 1.7. The access pattern is full-document retrieval by `application_id`. No sub-document querying is performed. GIN indexes on JSONB columns are appropriate only when key-level or containment queries are performed at volume. Introduction of JSONB indexes before such patterns exist is premature optimization. If GIN indexes become necessary, they may be introduced in a later stage via a dedicated Alembic migration without schema restructuring.

### Performance Rationale

All indexed columns serve one of three purposes: primary key resolution, foreign key join performance, or frequent equality-filter access patterns. No speculative or composite indexes are introduced. Index surface area is kept minimal to reduce write overhead during pipeline execution, which performs multiple inserts per processed application.

---

## 7. Constraint Governance

### Naming Conventions

| Constraint Type | Pattern | Example |
|---|---|---|
| Primary Key | `pk_{table_name}` | `pk_users`, `pk_applications` |
| Unique Constraint | `uq_{table_name}_{column_name}` | `uq_users_email`, `uq_canonical_records_application_id` |
| Foreign Key | `fk_{table_name}_{column_name}` | `fk_applications_uploaded_by`, `fk_canonical_records_application_id` |
| Check Constraint | `chk_{table_name}_{descriptor}` | `chk_users_role`, `chk_applications_pipeline_status` |
| Explicit Non-Unique Index | `idx_{table_name}_{column_name}` | `idx_applications_uploaded_by` |

Indexes created implicitly by primary key or unique constraint declarations inherit the constraint name. All constraints must be explicitly named. No unnamed constraints are permitted.

### Schema Evolution Discipline

- All schema changes must be expressed as versioned Alembic migration scripts
- No ad-hoc schema modification is permitted in any environment after Alembic initialization
- Each migration script must carry a sequential revision identifier and a descriptive label
- Destructive migrations (column drops, table drops) must not be executed without confirmed data redundancy or explicit architectural approval
- The `canonical_version` column acts as a discriminator for canonical structure evolution — new canonical version values do not require schema migration of the `canonical_data` column
- No schema migration may introduce columns that embed evaluation logic, ranking fields, scoring values, normalization results, or audit trail structures

### Alembic Governance

Alembic is the exclusively permitted schema migration tool. Manual DDL applied directly to the database is prohibited in all environments where Alembic is in use. Migration history must be preserved and committed to version control alongside application code.

---

## 8. Signal Storage Decision

### Decision Required Before Production

Stage 1.7 introduces interpreted signals as pipeline-ephemeral artifacts by default. They are not stored in a dedicated table or column. However, if signal data is required for auditability, debugging, or future analytical use, it may be embedded as a structured key within `synthesis_records.synthesis_output` alongside the ROS artifact.

This decision must be made explicitly before Stage 1.7 goes to production. It must not be left ambiguous. The two options are:

**Option A — Signals ephemeral (default):**
`synthesis_output` contains only the six ROS v1 keys. No signal data is stored. Signal artifacts are discarded after each pipeline run completes.

**Option B — Signals persisted:**
`synthesis_output` contains the six ROS v1 keys plus a `signal_data` key containing the deterministic signal collection and the validated interpreted signal collection. No schema change is required — the JSONB column absorbs this addition.

### Constraints on This Decision

- The decision is binary — either all signal data for an application is stored, or none is
- Partial signal storage (e.g. storing deterministic signals but not interpreted signals) is not permitted — it creates ambiguous audit state
- This decision applies uniformly to all applications processed under Stage 1.7 — it cannot be made per-application
- Reversing the decision after production deployment requires a data migration to backfill or strip signal data from existing `synthesis_output` documents — this should be factored into the decision
- A dedicated `signal_records` table must not be introduced — if signals are persisted, they live in `synthesis_output` only

---

## 9. What Is Explicitly Not Included

The following are confirmed absent from this schema. Their absence is intentional and governed by the architectural invariants defined in `architecture_lock_v1.7.md`.

| Category | Specific Exclusion |
|---|---|
| Job tables | No job queue table, no task status table, no polling table |
| Audit logs | No audit_log table, no event_log table, no change_history table |
| Tenant tables | No tenant table, no institution table, no organization table |
| Async tracking | No job_id column, no worker_id column, no queue_reference column |
| Object storage references | No S3 key column, no MinIO bucket reference — only local `file_path` |
| Refresh token storage | No refresh_token column, no token_store table |
| Ranking fields | No rank column, no percentile_rank column, no comparative_score column |
| Scoring columns | No applicant_score column, no aggregate_score column, no component_score column |
| Evaluation flags | No strength_flag column, no concern_flag column, no weakness_indicator column |
| Normalization columns | No normalized_gpa column, no percentage_equivalent column, no converted_grade column |
| Prediction fields | No admissions_probability column, no outcome_prediction column |
| Multi-tenant columns | No tenant_id column, no institution_id column in any table |
| Signal-specific tables | No signal_records table, no deterministic_signals table, no interpreted_signals table — signals embed in `synthesis_output` if persisted |
| Dedicated projection storage | No projection_records table — projections are pipeline-ephemeral and never stored |

---

## 10. Invariant Check

| Invariant | Status |
|---|---|
| Exactly four tables — no new tables in Stage 1.7 | ✅ |
| No new columns in any table | ✅ |
| No new constraints introduced | ✅ |
| No Alembic migrations required for Stage 1.7 | ✅ |
| `canonical_data` is JSONB — no relational decomposition | ✅ |
| `synthesis_output` is JSONB — ROS v1 structure stored without schema change | ✅ |
| No evaluation logic in any column | ✅ |
| No async tracking columns or tables | ✅ |
| No signal-specific dedicated table | ✅ |
| No projection storage table | ✅ |
| Signal storage decision must be made explicitly before production | ✅ |
| All constraints and indexes follow naming conventions | ✅ |
| Alembic is the exclusively permitted migration tool | ✅ |

---

*Database Schema Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*