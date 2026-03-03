# `database_schema_v1.md`

**(Stage 1 — Structured MVP: Formal PostgreSQL Schema Definition)**

---

## 1. Schema Version Declaration

### Schema Version

| Property | Value |
|---|---|
| schema_version | `1.0` |
| canonical_version compatibility | `1.0` |
| stage | Stage 1 — Structured MVP |
| status | Formal definition |

### Compatibility Statement

This schema is designed to store and serve canonical representations produced under `canonical_version: "1.0"` as defined in `canonical/version.py` and governed by `canonical_model_philosophy.md`. The `canonical_records.canonical_version` column must match the constant defined in that module at assembly time. Any future increment to `canonical_version` requires a corresponding schema migration review but does not automatically invalidate this schema, as canonical data is stored as JSONB and the version field acts as a discriminator, not a structural binding.

---

## 2. Database Engine Specification

### PostgreSQL Version Assumption

PostgreSQL 15 or later is assumed. No PostgreSQL 15-specific features are required; however, PostgreSQL 15 is selected as the minimum baseline to ensure stable JSONB indexing behavior, UUID support, and constraint enforcement semantics. Earlier versions are not supported under Stage 1.

### Required Extensions

| Extension | Purpose | Justification |
|---|---|---|
| `uuid-ossp` | UUID generation via `gen_random_uuid()` or `uuid_generate_v4()` | All primary keys are UUID type. UUID generation must occur at the database level as a default value to ensure consistency regardless of application-layer assignment. |

Note: PostgreSQL 13 and later expose `gen_random_uuid()` natively via the `pgcrypto` module. Either `uuid-ossp` or `pgcrypto` is acceptable depending on the PostgreSQL version in use. The implementation must confirm which function is available and use it consistently across all tables. Both options are compliant with this specification.

### JSONB Usage Rationale

JSONB is used in two columns: `canonical_records.canonical_data` and `synthesis_records.synthesis_output`.

JSONB is selected over TEXT or JSON for the following reasons:

- JSONB is stored in a decomposed binary format, enabling indexing and querying at the key level if required in later stages without schema migration.
- JSONB validates JSON structure at write time, preventing malformed documents from being persisted.
- JSONB supports GIN indexing, which enables efficient key-existence queries against the canonical structure when needed.
- JSONB does not impose a relational schema onto collection-based canonical data, preserving the architectural requirement that canonical structure remains extensible and not storage-bound.

Relational decomposition of canonical data into separate tables is intentionally not performed. This decision is governed by `canonical_model_philosophy.md`, which explicitly states that the canonical representation is a transport-level construct that must not be tightly coupled to database storage structure.

### Encoding Assumptions

| Property | Value |
|---|---|
| Database encoding | UTF-8 |
| Collation | `en_US.UTF-8` (or locale-equivalent) |
| Character type | UTF-8 |

UTF-8 encoding is required because application documents may contain non-ASCII characters including academic subject names, personal names, and institutional identifiers from diverse linguistic contexts.

---

## 3. Table Definitions

### 3.1 Table: `users`

**Purpose:** Stores authenticated user accounts. Users are institutional actors (admins or interviewers) who interact with the system.

#### Column Definitions

| Column Name | PostgreSQL Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `email` | `VARCHAR(320)` | NOT NULL | — | RFC 5321 maximum email length |
| `password_hash` | `VARCHAR(255)` | NOT NULL | — | bcrypt hash output |
| `role` | `VARCHAR(50)` | NOT NULL | — | Constrained by check constraint |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

- `id`

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_users_email` | `email` |

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_users_role` | `role IN ('admin', 'interviewer')` |

The role constraint is intentionally minimal. Role expansion must not be introduced in Stage 1.

#### Not-Null Constraints

All columns are NOT NULL. No nullable columns exist in this table.

#### Foreign Keys

None.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_users` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_users_email` | `email` | B-tree (implicit via unique constraint) | Login and registration lookups |

#### Cascade Behavior

No cascade rules apply at this table level. Users are not deleted in Stage 1.

#### Relationship Cardinality

- One user may be associated with zero or many application records (one-to-many via `applications.uploaded_by`).

---

### 3.2 Table: `applications`

**Purpose:** Stores application submission records. Each record corresponds to a single uploaded PDF and tracks the pipeline execution status and aggregate confidence for that document.

#### Column Definitions

| Column Name | PostgreSQL Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `uploaded_by` | `UUID` | NOT NULL | — | Foreign key to `users.id` |
| `file_path` | `VARCHAR(512)` | NOT NULL | — | Absolute local path to stored PDF |
| `pipeline_status` | `VARCHAR(50)` | NOT NULL | `'processing'` | Pipeline execution state |
| `pipeline_confidence` | `NUMERIC(5,4)` | NULL | — | Aggregate confidence 0.0000–1.0000; null until pipeline completes |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

- `id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_applications_uploaded_by` | `uploaded_by` | `users(id)` | RESTRICT | CASCADE |

Deletion of a user is restricted if associated application records exist. This prevents orphaned application records without implementing cascade deletion, which would silently destroy pipeline outputs.

#### Unique Constraints

None beyond the primary key. A single user may upload multiple applications.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_applications_pipeline_status` | `pipeline_status IN ('processing', 'complete', 'failed')` |
| `chk_applications_pipeline_confidence` | `pipeline_confidence IS NULL OR (pipeline_confidence >= 0.0000 AND pipeline_confidence <= 1.0000)` |

#### Not-Null Constraints

`id`, `uploaded_by`, `file_path`, `pipeline_status`, `created_at` are NOT NULL. `pipeline_confidence` is nullable.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_applications` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `idx_applications_uploaded_by` | `uploaded_by` | B-tree | Foreign key join performance; retrieval of all applications by user |

#### Cascade Behavior

- Delete on `users` is RESTRICT: no cascade. Application records must be explicitly managed before user deletion.

#### Relationship Cardinality

- Many applications belong to one user (many-to-one with `users`).
- One application has exactly one canonical record (one-to-one with `canonical_records`).
- One application has exactly one synthesis record (one-to-one with `synthesis_records`).

---

### 3.3 Table: `canonical_records`

**Purpose:** Stores the versioned canonical representation produced by the deterministic agent pipeline. This is the sole structured input to LLM synthesis and the authoritative extracted form of the application.

#### Column Definitions

| Column Name | PostgreSQL Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `application_id` | `UUID` | NOT NULL | — | Foreign key to `applications.id`; unique (one-to-one) |
| `canonical_version` | `VARCHAR(20)` | NOT NULL | — | Must match `CANONICAL_VERSION` constant at assembly time |
| `canonical_data` | `JSONB` | NOT NULL | — | Full collection-based canonical representation |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

- `id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_canonical_records_application_id` | `application_id` | `applications(id)` | CASCADE | CASCADE |

Deletion of an application cascades to its canonical record. An application without a canonical record is a meaningless shell. Cascade deletion is appropriate and intentional here.

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_canonical_records_application_id` | `application_id` |

This enforces the one-to-one relationship between applications and canonical records at the database level.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_canonical_records_version_format` | `canonical_version ~ '^\d+\.\d+$'` |

The version format check enforces the `"major.minor"` string pattern (e.g., `"1.0"`, `"1.1"`). This prevents unversioned or malformed version strings from being persisted.

#### Not-Null Constraints

All columns are NOT NULL.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_canonical_records` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_canonical_records_application_id` | `application_id` | B-tree (implicit via unique constraint) | One-to-one join; foreign key enforcement |
| `idx_canonical_records_version` | `canonical_version` | B-tree | Supports future version-scoped queries and migration tooling |

Optional JSONB indexing on `canonical_data` is not mandated in Stage 1. If specific key-level query patterns emerge, a GIN index on `canonical_data` may be added in Stage 2 or later without schema restructuring.

#### Cascade Behavior

- Cascade delete from `applications`: if an application is deleted, its canonical record is deleted.
- Cascade update from `applications`: if `applications.id` changes (which should not occur in normal operation), the foreign key follows.

#### Relationship Cardinality

- One canonical record belongs to exactly one application (one-to-one).

---

### 3.4 Table: `synthesis_records`

**Purpose:** Stores the LLM-generated synthesis output after policy validation. This table holds the final interviewer preparation report and the associated policy validation result.

#### Column Definitions

| Column Name | PostgreSQL Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | `gen_random_uuid()` | Primary key |
| `application_id` | `UUID` | NOT NULL | — | Foreign key to `applications.id`; unique (one-to-one) |
| `synthesis_output` | `JSONB` | NOT NULL | — | Structured synthesis result: snapshot, focus areas, questions |
| `policy_passed` | `BOOLEAN` | NOT NULL | — | True if output passed all policy rules without sanitization |
| `policy_violations_log` | `JSONB` | NULL | — | Structured violation metadata if sanitization occurred; null if policy_passed is true |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `NOW()` | UTC-aware timestamp |

#### Primary Key

- `id`

#### Foreign Keys

| Constraint Name | Column | References | On Delete | On Update |
|---|---|---|---|---|
| `fk_synthesis_records_application_id` | `application_id` | `applications(id)` | CASCADE | CASCADE |

Cascade delete is consistent with `canonical_records`. An application's synthesis record has no meaning without the application.

#### Unique Constraints

| Constraint Name | Column(s) |
|---|---|
| `uq_synthesis_records_application_id` | `application_id` |

Enforces one-to-one relationship at the database level.

#### Check Constraints

| Constraint Name | Definition |
|---|---|
| `chk_synthesis_records_violations_consistency` | `policy_passed = TRUE AND policy_violations_log IS NULL OR policy_passed = FALSE` |

When `policy_passed` is `TRUE`, `policy_violations_log` must be NULL. A passed output carries no violations log. When `policy_passed` is `FALSE`, `policy_violations_log` may or may not be populated depending on sanitization outcome.

Note: This check constraint enforces only the `TRUE → NULL log` direction. The `FALSE` case is intentionally permissive to allow for edge cases where violation detection occurs but log assembly fails in a recoverable way.

#### Not-Null Constraints

`id`, `application_id`, `synthesis_output`, `policy_passed`, `created_at` are NOT NULL. `policy_violations_log` is nullable.

#### Indexes

| Index Name | Column(s) | Type | Rationale |
|---|---|---|---|
| `pk_synthesis_records` | `id` | B-tree (implicit via PK) | Primary key lookup |
| `uq_synthesis_records_application_id` | `application_id` | B-tree (implicit via unique constraint) | One-to-one join; foreign key enforcement |
| `idx_synthesis_records_policy_passed` | `policy_passed` | B-tree | Supports operational queries filtering by policy compliance status |

---

## 4. Relationship Graph

### One-to-Many Relationships

| Parent Table | Child Table | Join Column | Cardinality Description |
|---|---|---|---|
| `users` | `applications` | `applications.uploaded_by → users.id` | One user may upload many applications |

### One-to-One Relationships

| Table A | Table B | Join Column | Enforcement |
|---|---|---|---|
| `applications` | `canonical_records` | `canonical_records.application_id → applications.id` | Unique constraint on `canonical_records.application_id` |
| `applications` | `synthesis_records` | `synthesis_records.application_id → applications.id` | Unique constraint on `synthesis_records.application_id` |

### Foreign Key Enforcement Rules

All foreign keys are enforced at the database level using explicit constraint declarations. No application-layer-only enforcement is acceptable. The database must reject inserts that violate referential integrity regardless of application behavior.

### Deletion Behavior Discipline

| Relationship | On Delete Behavior | Rationale |
|---|---|---|
| `users` → `applications` | RESTRICT | Prevents accidental deletion of a user that owns application records. Requires explicit application handling before user removal. |
| `applications` → `canonical_records` | CASCADE | Canonical record is meaningless without its application context. Deletion of an application removes its canonical output atomically. |
| `applications` → `synthesis_records` | CASCADE | Synthesis record is meaningless without its application context. Same rationale as canonical cascade. |

RESTRICT is used where data loss would be non-recoverable and ambiguous. CASCADE is used only where the child record's existence is entirely dependent on the parent and independent persistence would be a semantic error.

No `SET NULL` or `SET DEFAULT` behaviors are used. These would create orphaned records with undefined pipeline state.

---

## 5. JSONB Governance

### `canonical_records.canonical_data` — Structure Expectations

The `canonical_data` column stores the full canonical representation as defined in the Stage 0 Finalization Document, Section 3. The top-level structure expected within this column is:

| Top-Level Key | Value Type | Required |
|---|---|---|
| `canonical_version` | string | Yes |
| `identifiers` | object | Yes |
| `profile_meta` | object | Yes |
| `academic_entries` | array | Yes |
| `test_entries` | array | Yes |
| `essay_entries` | array | Yes |
| `activity_entries` | array | Yes |
| `timeline_entries` | array | Yes |
| `cross_references` | object | Yes |
| `integrity_report` | object | Yes |
| `extraction_confidence` | object | Yes |

All array fields represent collections. None may be collapsed into a singular object or replaced with fixed-key maps. This is a non-negotiable constraint inherited from `canonical_model_philosophy.md`.

The schema does not enforce internal JSONB structure via database-level constraints in Stage 1. Structural validation is the responsibility of Pydantic models in the application layer (`canonical/model.py`). The database is a durable store, not a schema enforcer for the canonical document.

### `synthesis_records.synthesis_output` — Structure Expectations

The `synthesis_output` column stores the LLM-generated synthesis result as defined in the Stage 0 Finalization Document, Section 3. The expected top-level structure is:

| Top-Level Key | Value Type | Required |
|---|---|---|
| `snapshot` | string | Yes |
| `discussion_focus_areas` | array of strings | Yes |
| `suggested_questions` | array of strings | Yes |
| `canonical_version_ref` | string | Yes |

The `canonical_version_ref` must match the `canonical_version` of the associated `canonical_records` row. This is a logical consistency requirement enforced at the application layer, not via a database cross-column constraint in Stage 1.

### `synthesis_records.policy_violations_log` — Structure Expectations

When populated, this column stores structured violation metadata. The expected structure per violation entry is:

| Field | Value Type |
|---|---|
| `rule_id` | string |
| `rule_set_name` | string |
| `field_reference` | string (target output field name) |
| `action_taken` | string (`"reject"` or `"sanitize"`) |
| `severity` | string |

Raw prohibited text is not stored. Only structured metadata describing what was detected and what action was taken is persisted.

### Justification for JSONB Over Relational Decomposition

Relational decomposition of canonical data would require:

- A separate table for each collection type (academic entries, test entries, essay entries, activity entries, timeline entries).
- Additional join tables for nested structures such as subject entries within academic entries and sectional scores within test entries.
- Schema migrations every time a new field is added to any canonical entry type.
- Fixed column definitions that would embed assumptions about academic systems, test formats, and essay structures into the database schema — which is explicitly prohibited by `canonical_model_philosophy.md`.

JSONB eliminates all of these problems while preserving database-level storage, ACID guarantees, and queryability. The canonical model is extensible by design; JSONB is the storage mechanism that preserves this extensibility at the persistence layer.

### Query Strategy Assumptions

In Stage 1, `canonical_data` is retrieved as a complete document per application. No sub-document queries are required in Stage 1. The application layer deserializes the JSONB document into Pydantic models for all processing. If sub-document queries become necessary in later stages, GIN indexing on `canonical_data` can be introduced without schema restructuring.

### Confirmation: Collection-Based Canonical Philosophy Preserved

The `canonical_data` column stores the canonical representation as a JSONB document with array-typed collection fields for all repeating data structures. No canonical collection is collapsed. No fixed academic-level keys exist at the column level or within the expected JSONB structure. The collection-based canonical philosophy defined in `canonical_model_philosophy.md` is fully preserved.

---

## 6. Indexing Strategy

### Mandatory Indexes

| Index Name | Table | Column(s) | Index Type | Rationale |
|---|---|---|---|---|
| `pk_users` | `users` | `id` | B-tree (PK) | Primary key lookup; all user-related joins |
| `uq_users_email` | `users` | `email` | B-tree (unique) | Login and registration lookup by email |
| `pk_applications` | `applications` | `id` | B-tree (PK) | Primary key lookup; all application-related joins |
| `idx_applications_uploaded_by` | `applications` | `uploaded_by` | B-tree | Foreign key join; retrieve all applications by user |
| `pk_canonical_records` | `canonical_records` | `id` | B-tree (PK) | Primary key lookup |
| `uq_canonical_records_application_id` | `canonical_records` | `application_id` | B-tree (unique) | One-to-one join enforcement; foreign key |
| `idx_canonical_records_version` | `canonical_records` | `canonical_version` | B-tree | Version-scoped migration queries; canonical version filtering |
| `pk_synthesis_records` | `synthesis_records` | `id` | B-tree (PK) | Primary key lookup |
| `uq_synthesis_records_application_id` | `synthesis_records` | `application_id` | B-tree (unique) | One-to-one join enforcement; foreign key |
| `idx_synthesis_records_policy_passed` | `synthesis_records` | `policy_passed` | B-tree | Policy compliance filtering |

### Optional JSONB Indexing Discipline

No GIN index on `canonical_data` or `synthesis_output` is mandated in Stage 1. The access pattern in Stage 1 is full-document retrieval by `application_id`. No sub-document querying is performed. GIN indexes on JSONB columns are appropriate only when key-level or containment queries are performed at volume. Introduction of JSONB indexes before such patterns exist is premature optimization and violates Stage 1 scope discipline.

If GIN indexes become necessary, they may be introduced in Stage 2 or later via a dedicated Alembic migration without requiring any schema restructuring.

### Performance Rationale

All indexed columns serve one of three purposes: primary key resolution, foreign key join performance, or frequent equality-filter access patterns. No speculative indexes are introduced. No composite indexes are introduced in Stage 1. Index surface area is kept minimal to reduce write overhead during pipeline execution, which includes multiple insert operations per processed application.

---

## 7. Constraint Governance

### Naming Convention for Constraints

| Constraint Type | Naming Pattern | Example |
|---|---|---|
| Primary Key | `pk_{table_name}` | `pk_users`, `pk_applications` |
| Unique Constraint | `uq_{table_name}_{column_name}` | `uq_users_email`, `uq_canonical_records_application_id` |
| Foreign Key | `fk_{table_name}_{column_name}` | `fk_applications_uploaded_by`, `fk_canonical_records_application_id` |
| Check Constraint | `chk_{table_name}_{descriptor}` | `chk_users_role`, `chk_applications_pipeline_status` |

### Naming Convention for Indexes

| Index Type | Naming Pattern | Example |
|---|---|---|
| Primary Key Index (implicit) | `pk_{table_name}` | `pk_users` |
| Unique Index (implicit via unique constraint) | `uq_{table_name}_{column_name}` | `uq_users_email` |
| Explicit Non-Unique Index | `idx_{table_name}_{column_name}` | `idx_applications_uploaded_by` |

Indexes created implicitly by primary key or unique constraint declarations inherit the constraint name. Explicit non-unique indexes use the `idx_` prefix. This naming scheme allows constraint and index management to be unambiguous in migration tooling.

### Schema Evolution Discipline

- All schema changes must be expressed as versioned Alembic migration scripts.
- No ad-hoc schema modification is permitted in any environment.
- Each migration script must be named with a sequential revision identifier and a descriptive label.
- Migration scripts must be reviewed against `architecture_lock.md` and `stage_1_scope_lock.md` before application.
- Destructive migrations (column drops, table drops) must not be executed without confirmed data redundancy or explicit architectural approval.
- The `canonical_version` column in `canonical_records` acts as a discriminator for canonical structure evolution. New `canonical_version` values do not require schema migration of the `canonical_data` column; they require application-layer version handling only.
- No schema migration may introduce columns that embed evaluation logic, ranking fields, scoring values, normalization results, or audit trail structures.

### Migration Governance Statement

Alembic is the exclusively permitted migration tool. Manual schema modifications executed directly against the database are prohibited in all environments where Alembic is in use. Migration history must be preserved and committed to version control alongside application code.

---

## 8. What Is Explicitly Not Included

The following are confirmed absent from this schema. Their absence is intentional and required by the governing specification documents.

| Category | Specific Exclusion | Governing Document |
|---|---|---|
| Job tables | No job queue table, no task status table, no polling table | `stage_1_scope_lock.md`, `stage_0_scope_lock.md` |
| Audit logs | No audit_log table, no event_log table, no change_history table | `stage_1_scope_lock.md` |
| Tenant tables | No tenant table, no institution table, no organization table | `stage_1_scope_lock.md` |
| Async tracking | No job_id column, no worker_id column, no queue_reference column | `stage_1_scope_lock.md` |
| Object storage references | No S3 key column, no MinIO bucket reference, no external storage path beyond local file_path | `stage_1_scope_lock.md` |
| Refresh token storage | No refresh_token column, no token_store table | `architecture_lock.md` |
| Ranking fields | No rank column, no percentile_rank column, no comparative_score column | `architecture_lock.md`, `llm_synthesis_contract.md` |
| Scoring columns | No applicant_score column, no aggregate_score column, no component_score column | `architecture_lock.md`, `llm_synthesis_contract.md` |
| Evaluation flags | No strength_flag column, no concern_flag column, no weakness_indicator column | `architecture_lock.md`, `llm_synthesis_contract.md` |
| Normalization columns | No normalized_gpa column, no percentage_equivalent column, no converted_grade column | `canonical_model_philosophy.md` |
| Prediction fields | No admissions_probability column, no outcome_prediction column | `system_overview.md` |
| Multi-tenant columns | No tenant_id column, no institution_id column in any table | `stage_1_scope_lock.md` |
| Service boundary markers | No service_id column, no routing_key column | `architecture_lock.md` |

---

## 9. Stage 1 Completion Criteria (Schema-Level)

The schema is considered Stage 1 compliant when all of the following are true:

### Structural Completeness

- Exactly four tables exist: `users`, `applications`, `canonical_records`, `synthesis_records`.
- No additional tables have been introduced.
- All columns defined in Section 3 are present with the specified types, constraints, and defaults.

### Constraint Enforcement

- All primary keys are UUID type with database-level default generation.
- All foreign keys are declared explicitly with correct reference targets and deletion behavior.
- All unique constraints are declared and enforced at the database level.
- All check constraints on `pipeline_status`, `role`, `pipeline_confidence`, and `canonical_version` format are active.
- The `policy_violations_log` consistency check constraint is active.

### JSONB Storage

- `canonical_records.canonical_data` is JSONB type, not TEXT or JSON.
- `synthesis_records.synthesis_output` is JSONB type, not TEXT or JSON.
- `synthesis_records.policy_violations_log` is JSONB type or NULL, not TEXT.
- No relational decomposition of canonical or synthesis data has occurred.
- Collection-based structure of canonical data is preserved within the JSONB document.

### Index Coverage

- All foreign key columns have explicit B-tree indexes.
- `users.email` has a unique index.
- `canonical_records.canonical_version` has a B-tree index.
- `synthesis_records.policy_passed` has a B-tree index.
- No speculative or premature JSONB indexes have been introduced.

### Naming Compliance

- All constraints and indexes follow the naming conventions defined in Section 7.
- No unnamed constraints exist (all are explicitly named).

### Migration Governance

- All tables were created via Alembic migration scripts.
- No manual DDL was applied to any environment.
- Migration history is committed to version control.
- Migration scripts contain no evaluation logic, no scoring fields, and no prohibited columns.

### Canonical Version Alignment

- `canonical_records.canonical_version` value `"1.0"` has been successfully written for at least one processed application.
- The `canonical_version_ref` field in `synthesis_records.synthesis_output` matches the associated canonical record's `canonical_version` for all stored records.

### Architectural Invariance Confirmation

- No column in any table performs or stores applicant evaluation.
- No column encodes academic-level-specific assumptions.
- No column references external async infrastructure.
- No column stores raw PDF content.
- No column stores LLM intermediate reasoning.

---

## Constraint Check

| Constraint | Status | Evidence |
|---|---|---|
| **Deterministic-first preserved** | ✅ | No schema column stores LLM-extracted content. `canonical_data` stores only the output of deterministic agents assembled by Agent 11. LLM output is stored separately in `synthesis_records`. No schema structure implies or requires LLM involvement in extraction. |
| **Single LLM call preserved** | ✅ | No job table, no retry table, no secondary synthesis column exists. The schema supports exactly one `synthesis_records` row per application (enforced by unique constraint on `application_id`). No schema mechanism enables multiple LLM calls. |
| **No evaluation logic introduced** | ✅ | No scoring column, ranking column, evaluation flag, concern indicator, strength label, weakness marker, or normalization field appears in any table definition. All prohibited evaluation constructs are explicitly listed as absent in Section 8. |
| **Collection-based canonical preserved** | ✅ | `canonical_data` is JSONB with expected array-typed fields for all repeating structures. No relational decomposition occurs. No fixed academic-level column exists. Section 5 explicitly confirms collection-based philosophy is preserved. |
| **No rigid key paths introduced** | ✅ | No column of the form `class_12_score`, `sat_total`, or `career_essay_text` exists anywhere. All canonical content lives within the extensible JSONB document. |
| **No async schema introduced** | ✅ | No job table, task table, worker_id column, queue reference, or polling endpoint schema exists. Confirmed absent in Section 8. |
| **No infrastructure creep beyond Stage 1** | ✅ | No tenant tables, no audit tables, no object storage reference columns, no distributed tracing schema, no monitoring tables. Schema contains exactly the four tables permitted by Stage 0 Finalization Document and Stage 1 scope. |
| **No service separation introduced** | ✅ | No service_id, routing_key, or inter-service reference column exists. All tables represent a single-service schema. No schema structure implies microservice decomposition. |
| **No additional LLM frameworks introduced** | ✅ | No schema column stores LangChain state, agent memory, tool-call chain data, or multi-step reasoning output. The schema supports exactly one LLM invocation per application with no structural provision for anything beyond that. |

---

*End of `database_schema_v1.md`.*

*Schema Version: 1.0 | Stage: 1 — Structured MVP | Governing Architecture Version: architecture_lock.md*
