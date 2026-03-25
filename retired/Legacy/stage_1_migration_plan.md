# `stage_1_migration_plan.md`

**(Stage 1 — Structured MVP: Concrete Migration Governance Plan)**

---

## Preamble

This document governs the concrete transition from Stage 0 (Local Core Engine) to Stage 1 (Structured MVP). It is a structural migration governance document only. It does not generate code, SQL, Dockerfiles, docker-compose YAML, Alembic scripts, or Python classes. All implementation artifacts produced under this plan must comply with the governing specification documents listed below. In cases of conflict between any section of this document and `architecture_lock.md`, `architecture_lock.md` prevails without exception.

### Governing Documents

| Document | Role |
|---|---|
| `architecture_lock.md` | Supreme constraint authority. Prevails over all other documents in conflict. |
| `system_overview.md` | Architectural identity and invariants. |
| `agent_pipeline_spec.md` | Logical pipeline definition. Unchanged by Stage 1. |
| `canonical_model_philosophy.md` | Canonical representation invariants. Unchanged by Stage 1. |
| `llm_synthesis_contract.md` | LLM synthesis behavioral contract. Unchanged by Stage 1. |
| `stage_1_scope_lock.md` | Stage 1 boundary enforcement. |
| `database_schema_v1.md` | Formal PostgreSQL schema definition for Stage 1. |
| `env_config_spec.md` | Environment variable specification for Stage 1. |

---

## 1. Stage 1 Objectives

### 1.1 Infrastructure Formalization Goals

Stage 1 exists to formalize the infrastructure layer beneath the logical core established in Stage 0. The goals are bounded, explicit, and infrastructure-only:

**Database Formalization.** Replace any SQLite usage from Stage 0 with a formally defined PostgreSQL 15+ instance. Introduce Alembic as the exclusively permitted schema migration tool. Apply the schema defined in `database_schema_v1.md` via versioned migration scripts. Enforce all constraints, indexes, and foreign key relationships at the database level.

**Containerization.** Introduce a minimal Docker-based deployment topology consisting of exactly two containers: one for the FastAPI application and one for PostgreSQL. No additional containers are permitted. The containerized system must exhibit behavior identical to the non-containerized Stage 0 system.

**Authentication Hardening.** Confirm that bcrypt password hashing and JWT-based authentication are correctly implemented. Confirm role-based access control for `admin` and `interviewer` roles is functioning. No third-party authentication providers are introduced.

**Configuration Formalization.** Externalize all configuration through environment variables as defined in `env_config_spec.md`. Remove any hardcoded values that may have existed in Stage 0. Enforce startup-time validation across all required variables.

**Basic Structured Logging.** Introduce minimal application-level logging covering defined pipeline lifecycle events. Logging emits to stdout only. No observability stack, monitoring integration, or distributed tracing is introduced.

### 1.2 Explicit Statement: Logical Pipeline Remains Unchanged

The logical agent pipeline defined in `agent_pipeline_spec.md` is not modified by Stage 1 in any respect. All fourteen agents (Agents 0 through 13) retain their defined responsibilities, prohibitions, execution order, and input/output contracts without alteration.

The canonical representation philosophy defined in `canonical_model_philosophy.md` is not modified. The canonical model remains collection-based, versioned, non-evaluative, PII-separated, and transport-level. No field is added, removed, or restructured.

The LLM synthesis contract defined in `llm_synthesis_contract.md` is not modified. The system continues to make exactly one LLM call per processed application. The prompt design, input boundary, output scope, and policy validation behavior remain identical to Stage 0.

Stage 1 changes only how the system is packaged, persisted, configured, and deployed. It does not change what the system does.

---

## 2. Stage 0 → Stage 1 Transition Overview

### 2.1 What Remains Identical

The following elements are carried forward from Stage 0 without modification:

- All agent module implementations (`agents/` directory: `orchestrator.py`, `layout_extractor.py`, `section_detector.py`, `personal_extractor.py`, `academic_extractor.py`, `test_extractor.py`, `essay_extractor.py`, `activity_extractor.py`, `cross_section_detector.py`, `timeline_builder.py`, `integrity_analyzer.py`, `assembler.py`, `synthesis_agent.py`, `validation_filter.py`)
- All Pydantic models in `canonical/model.py` and the `CANONICAL_VERSION` constant in `canonical/version.py`
- The `llm/client.py` implementation and its `generate_synthesis` function contract
- The `policy/guard.py` and `policy/config.py` structure and rule definitions
- The API route handlers in `api/applications.py` and `auth/router.py`
- The pipeline execution model: synchronous, sequential, single-request-lifecycle
- The canonical JSON field naming conventions defined in the Stage 0 Finalization Document, Section 3
- The four-table database logical structure: `users`, `applications`, `canonical_records`, `synthesis_records`
- The `synthesis_output` structure: `snapshot`, `discussion_focus_areas`, `suggested_questions`, `canonical_version_ref`

### 2.2 What Changes

The following elements change in Stage 1:

**Database engine.** If Stage 0 used SQLite for initial development, the database engine transitions to PostgreSQL 15+. If Stage 0 was already implemented against PostgreSQL, the transition involves formalizing the schema via Alembic and applying all constraints defined in `database_schema_v1.md`. In either case, the schema enforcement, constraint naming, index structure, JSONB column types, check constraints, and foreign key behaviors defined in `database_schema_v1.md` are formally applied.

**Schema migration tooling.** Alembic is formally initialized and becomes the exclusively permitted mechanism for schema changes. All table definitions are expressed as versioned Alembic migration scripts. No manual DDL is applied in any environment after Alembic initialization.

**Containerization.** The application and database are containerized via Docker. A `Dockerfile` defines the API container. A `docker-compose.yml` defines the two-container topology and their network, volume, and startup dependency relationships. The container topology is the authoritative deployment model for Stage 1.

**Environment variable handling.** The `config.py` module implements full startup-time validation of all required environment variables as defined in `env_config_spec.md`. A `.env.example` file is introduced to the repository. All hardcoded configuration values are removed.

**Logging.** Minimal structured logging is introduced covering the pipeline lifecycle events defined in `env_config_spec.md`, Section 5. Logging is configured at startup from the `LOG_LEVEL` environment variable.

**SQLAlchemy connection binding.** The `database.py` module is updated to target PostgreSQL via the `psycopg2` driver. JSONB column types are confirmed in ORM model definitions. Connection pool parameters are bound to `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` environment variables.

### 2.3 Why Changes Are Infrastructure-Only

Each change described in Section 2.2 affects only the infrastructure layer surrounding the logical core:

The database engine change affects where and how data is stored, not what data is processed or how the pipeline operates. The canonical representation stored in `canonical_records.canonical_data` is identical in content regardless of storage engine.

Alembic formalizes schema management. It does not alter agent logic, canonical structure, LLM behavior, or policy validation. It is a disciplined tooling change.

Containerization changes how the application is packaged and started. The application code inside the container is identical to the Stage 0 application code.

Environment variable formalization changes how configuration values are supplied. It does not alter what those values govern or how they are consumed by application logic.

Logging introduces observability into infrastructure events. It does not alter the behavior of any agent, the content of any canonical field, or the behavior of the LLM synthesis call.

In every case, the logical pipeline from PDF ingestion through deterministic extraction, canonical assembly, single LLM synthesis, policy validation, and final report generation remains structurally and behaviorally identical to Stage 0.

---

## 3. Database Migration Plan

This section references `database_schema_v1.md` as the authoritative schema definition. All schema decisions are governed by that document and by `canonical_model_philosophy.md`.

### 3.1 Migration Strategy: SQLite to PostgreSQL (If Applicable)

If Stage 0 was implemented using SQLite as a development database, the following strategy governs the transition:

**No data migration from SQLite to PostgreSQL is required or permitted.** Stage 0 is an architectural proof stage. Its data is not production data. The PostgreSQL database in Stage 1 begins empty. No migration tooling for transferring SQLite records to PostgreSQL is introduced. The transition is a clean schema initialization, not a data migration.

If Stage 0 was already implemented against a PostgreSQL instance without formal Alembic management, the strategy is: capture the existing schema state as the Alembic baseline, confirm alignment with `database_schema_v1.md`, apply any gap-filling migrations as versioned scripts, and proceed from a known, Alembic-managed state.

In either case, the target state is identical: a PostgreSQL 15+ database with the four-table schema defined in `database_schema_v1.md`, fully managed by Alembic.

### 3.2 UUID Extension Enablement Sequencing

The `uuid-ossp` extension or confirmation of `gen_random_uuid()` availability via `pgcrypto` must be handled before any table creation migration is applied.

Extension enablement must occur as the first migration in the Alembic history. This migration has no downgrade equivalent that would be safe to apply in a live system. The sequencing is:

1. Confirm PostgreSQL version is 15 or later.
2. Confirm which UUID generation function is available (`gen_random_uuid()` via pgcrypto or `uuid_generate_v4()` via uuid-ossp).
3. Apply extension enablement as Alembic revision `0001`.
4. Confirm UUID function is callable before proceeding to table creation migrations.

No table creation migration may be applied before extension availability is confirmed and the extension migration is committed.

### 3.3 Alembic Initialization Order

Alembic initialization follows this sequence:

1. Alembic is initialized in the repository, creating the `alembic/` directory and `alembic.ini` configuration file.
2. `alembic.ini` is configured to read `DATABASE_URL` from the environment, not from a hardcoded value in the file. The database URL must never be hardcoded in `alembic.ini` or in any Alembic `env.py` configuration file.
3. The Alembic `env.py` is configured to import SQLAlchemy models from the application's `models/` directory, enabling model-aware migration generation. However, autogenerate-without-review is prohibited (see Section 4).
4. An initial baseline migration (Alembic revision `0001`) is created to enable UUID support as described in Section 3.2.
5. Subsequent migrations create each table in the order defined by dependency: `users` first (no foreign key dependencies), then `applications` (depends on `users`), then `canonical_records` and `synthesis_records` (both depend on `applications`). These may be expressed as a single revision or as individual revisions; single-revision table creation is acceptable for initial schema establishment.
6. All migrations are committed to version control before any are applied to any environment.

### 3.4 Schema Creation Discipline

Schema creation must strictly implement the table definitions in `database_schema_v1.md`. The following discipline governs the creation process:

**Column types must match exactly.** UUID primary keys with database-level defaults, VARCHAR with defined length limits, TIMESTAMP WITH TIME ZONE (not TIMESTAMP WITHOUT TIME ZONE), NUMERIC(5,4) for `pipeline_confidence`, JSONB for canonical and synthesis data, BOOLEAN for `policy_passed`.

**All columns defined as NOT NULL in `database_schema_v1.md` must be declared NOT NULL.** No column may be silently made nullable to ease implementation.

**JSONB columns must be JSONB.** Neither TEXT nor JSON is an acceptable substitute. This is non-negotiable per `database_schema_v1.md` Section 2 and the rationale documented therein.

**Default values must be database-level defaults.** UUID generation defaults and timestamp defaults must be expressed as column-level default expressions, not application-layer assignments. Application-layer assignment is not sufficient; database defaults must exist so that records are valid regardless of application behavior.

**`pipeline_status` must default to `'processing'` at the database level**, not only at the application layer.

### 3.5 Data Migration Handling

As stated in Section 3.1, no data migration from Stage 0 to Stage 1 is required or implemented. Stage 0 is a proof stage. Stage 1 begins with an empty database. Any Stage 0 test records are discarded. No migration tooling for record transfer is introduced.

If, in exceptional circumstances, a decision is made to preserve specific Stage 0 records, this requires explicit architectural approval as defined in `architecture_lock.md` Section 12. Silent data migration is not permitted.

### 3.6 Constraint Enforcement Order

Constraints must be applied in the following logical order to avoid referential and logical dependency conflicts:

1. Primary key constraints on all tables (applied as part of table creation).
2. Unique constraints on all tables (applied as part of table creation or as named constraints immediately following).
3. Check constraints on all tables (`chk_users_role`, `chk_applications_pipeline_status`, `chk_applications_pipeline_confidence`, `chk_canonical_records_version_format`, `chk_synthesis_records_violations_consistency`) — applied as part of table creation.
4. Foreign key constraints in dependency order:
   - `fk_applications_uploaded_by` (requires `users` table to exist).
   - `fk_canonical_records_application_id` (requires `applications` table to exist).
   - `fk_synthesis_records_application_id` (requires `applications` table to exist).
5. All constraints must be explicitly named following the naming conventions in `database_schema_v1.md` Section 7. Unnamed constraints are not permitted.

Constraints must not be applied before their referenced tables and columns exist. The dependency order described above must be respected in migration script sequencing.

### 3.7 Index Creation Order

Indexes are created immediately after their associated table and constraint definitions are applied. The index creation order follows the table dependency order:

1. Indexes on `users` table: `pk_users` (implicit via PK), `uq_users_email` (implicit via unique constraint).
2. Indexes on `applications` table: `pk_applications` (implicit via PK), `idx_applications_uploaded_by` (explicit B-tree).
3. Indexes on `canonical_records` table: `pk_canonical_records` (implicit via PK), `uq_canonical_records_application_id` (implicit via unique constraint), `idx_canonical_records_version` (explicit B-tree).
4. Indexes on `synthesis_records` table: `pk_synthesis_records` (implicit via PK), `uq_synthesis_records_application_id` (implicit via unique constraint), `idx_synthesis_records_policy_passed` (explicit B-tree).

No GIN indexes on JSONB columns are introduced in Stage 1. Their introduction is deferred to Stage 2 or later, contingent on emerging query patterns.

### 3.8 Validation Queries (Described)

After schema application, the following validation queries must be confirmed to produce expected results before Stage 1 is declared schema-complete:

**Table existence validation.** A query confirming that exactly four tables exist in the target schema: `users`, `applications`, `canonical_records`, `synthesis_records`. No additional tables may be present.

**Column presence validation.** For each table, a query confirming that all defined columns exist with the expected names, types, nullability, and default values.

**Constraint presence validation.** A query confirming that all named constraints exist: primary keys, unique constraints, check constraints, and foreign key constraints. All constraint names must match the naming conventions defined in `database_schema_v1.md` Section 7.

**Index presence validation.** A query confirming that all defined indexes exist by name and target the correct columns.

**JSONB type validation.** A query confirming that `canonical_records.canonical_data`, `synthesis_records.synthesis_output`, and `synthesis_records.policy_violations_log` are of type `jsonb`, not `json` or `text`.

**UUID default validation.** A test insert into `users` without supplying an `id` value, confirming that the database assigns a valid UUID automatically.

**Check constraint validation.** Test inserts that violate each check constraint, confirming that the database rejects them. Specifically: inserting an invalid `role` value, inserting an invalid `pipeline_status` value, inserting a `pipeline_confidence` value outside 0.0–1.0, inserting a `canonical_version` that does not match the regex pattern, and inserting a `synthesis_records` row with `policy_passed = TRUE` and a non-null `policy_violations_log`.

**Foreign key constraint validation.** A test insert into `applications` referencing a non-existent `users.id`, confirming rejection. A test insert into `canonical_records` referencing a non-existent `applications.id`, confirming rejection.

**Cascade delete validation.** A test confirming that deletion of an `applications` row cascades to its associated `canonical_records` and `synthesis_records` rows. A test confirming that attempted deletion of a `users` row with associated `applications` rows is rejected (RESTRICT).

All validation queries must be executed against the target PostgreSQL instance after migrations are applied and before any application traffic is processed.

---

## 4. Alembic Governance Plan

### 4.1 Migration File Naming Convention

All Alembic migration files must follow the naming convention:

`{revision_id}_{descriptive_label}.py`

Where:
- `revision_id` is the Alembic-generated hexadecimal identifier (typically 12 characters), preserved as generated.
- `descriptive_label` is a lowercase, underscore-separated description of what the migration does. The label must be meaningful and unambiguous. Generic labels such as `initial`, `changes`, `update`, or `fix` are not acceptable.

Examples of acceptable labels:
- `enable_uuid_extension`
- `create_users_table`
- `create_applications_table`
- `create_canonical_records_table`
- `create_synthesis_records_table`
- `add_idx_applications_uploaded_by`
- `add_chk_canonical_records_version_format`

Examples of unacceptable labels:
- `initial`
- `migration_1`
- `changes`
- `update_schema`

Every migration file must include a docstring at the top identifying its purpose, the schema elements it creates or modifies, and a reference to the governing specification document that authorizes the change.

### 4.2 Revision Discipline

Each migration revision must be atomic in scope: it must address a single, well-defined schema concern. A single revision may create multiple related tables if they form an inseparable dependency unit (for example, creating all four tables in the initial schema establishment). However, mixing structural changes with data migration logic, policy logic, or any application-layer concern in a single revision is prohibited.

Every revision must:
- Have a clearly defined `upgrade()` function.
- Have a `downgrade()` function that reverses the upgrade cleanly (subject to the constraints defined in Section 4.3).
- Be committed to version control before being applied to any environment.
- Pass review against `database_schema_v1.md` before application.

Revision identifiers must not be manually altered after creation. The Alembic-generated identifier is the authoritative reference for that migration.

### 4.3 Downgrade Policy

Downgrade support must be implemented for all migrations that can be safely reversed. However, the following downgrade constraints apply:

**UUID extension downgrade is not safely reversible if data exists.** The downgrade function for the extension-enablement migration must be defined but must produce a warning and refuse to execute if any UUID-keyed table contains rows. Dropping the UUID extension when data exists would break foreign key relationships. This is a non-destructive guard, not a silent no-op.

**Table drop downgrades must not be executed in any environment where real data exists.** Downgrade functions for table-creation migrations must be defined but must be protected by a pre-execution check that confirms the table is empty before proceeding with the drop. If data exists, the downgrade must be aborted with a descriptive error.

**Downgrade to Stage 0 state is addressed in Section 9 (Rollback Strategy).**

Downgrade functions must never be executed without explicit operator action and confirmation. No automated or trigger-based downgrade is permitted.

### 4.4 Environment Configuration Binding

Alembic must not contain hardcoded database connection strings. The `DATABASE_URL` environment variable defined in `env_config_spec.md` must be the sole source of the connection string used by Alembic during migration operations.

The Alembic `env.py` file must read `DATABASE_URL` from the environment at runtime. If `DATABASE_URL` is absent when Alembic is invoked, Alembic must refuse to proceed and emit a descriptive error.

The `alembic.ini` `sqlalchemy.url` key must not contain a real database URL. It must be overridden at runtime by the `env.py` logic that reads the environment variable.

Migration operations must not be run against a database that the application is actively serving. In Stage 1, migration is a startup-time or explicit operator-initiated action, not an in-process action triggered by application requests.

### 4.5 No Autogenerate-Without-Review Rule

Alembic's `--autogenerate` flag may be used as a development aid to detect differences between ORM models and the current database schema. However, autogenerated migration scripts must never be applied to any environment without human review and explicit confirmation that the generated script complies with `database_schema_v1.md`.

Autogenerate frequently produces spurious or incomplete output. It is a suggestion tool, not an authoritative source. The authoritative schema definition is `database_schema_v1.md`. Every migration script must be manually reviewed against that document before it is committed to version control or applied to any environment.

Autogenerated scripts that would introduce columns, tables, indexes, or constraints not defined in `database_schema_v1.md` must be rejected and discarded.

### 4.6 Schema Drift Prevention Discipline

Schema drift — the divergence between the Alembic migration history and the actual state of the database — is prohibited. The following practices enforce this:

**All schema changes must originate from Alembic migrations.** No manual DDL operations (`ALTER TABLE`, `CREATE INDEX`, `DROP COLUMN`, etc.) may be applied directly to any PostgreSQL instance managed by Alembic. This applies to all environments including local development.

**The Alembic `alembic_version` table must be present and accurate in all environments.** Any environment where the `alembic_version` table is absent or shows a different revision than the committed migration history is in a drift state and must be remediated before proceeding.

**Migration scripts must be committed to version control before application.** The sequence is: write migration, review, commit, then apply. Applying uncommitted migrations is prohibited.

**The `alembic current` command must be used to confirm migration state before and after any migration operation.** The output must match expectations based on the committed migration history.

**No column or table not defined in `database_schema_v1.md` may exist in the database.** Presence of undeclared schema elements is drift and must be resolved via an explicit migration that removes them, subject to the data-existence checks described in Section 4.3.

---

## 5. Dockerization Plan

### 5.1 Container Topology

Stage 1 defines exactly two containers. No additional containers are permitted under any circumstances.

**API Container.** Runs the FastAPI application using Uvicorn. Built from a `Dockerfile` in the repository root. Contains all application code, including all agent modules, canonical models, LLM client, policy guard, and API route handlers. This is the same codebase as Stage 0, containerized without modification to logic.

**PostgreSQL Container.** Runs PostgreSQL 15 or later. Uses the official PostgreSQL Docker image. Persists data to a named Docker volume. No custom extensions are baked into the image; extension enabling is handled via Alembic migration on first startup.

These two containers communicate over a Docker-defined internal network. No external network exposure is required for the PostgreSQL container. The API container is the only container that exposes a port to the host for development access.

No Redis container. No worker container. No NGINX container. No MinIO container. No monitoring container. No sidecar container. The topology is exhaustively: API + PostgreSQL.

### 5.2 Volume Persistence Discipline

Two named Docker volumes are defined:

**Database volume.** Mounted into the PostgreSQL container at the standard PostgreSQL data directory. This volume persists database state across container restarts. Named volumes are used rather than bind mounts to avoid host filesystem permission issues. The database volume must not be shared with or accessible by the API container.

**Uploads volume.** Mounted into the API container at the path defined by the `UPLOAD_DIRECTORY` environment variable. This volume persists uploaded PDF files across container restarts. The `UPLOAD_DIRECTORY` path inside the container must exactly match the mount point of this volume.

No other volumes are defined. No temporary volumes. No anonymous volumes for production use. Volume names must be explicitly declared in the `docker-compose.yml` to ensure they are persistent and named, not ephemeral.

Volume lifecycle is operator-managed. Volumes are not destroyed on container restart or `docker-compose down` without the explicit `-v` flag. The default behavior must be volume preservation.

### 5.3 Environment Variable Injection Method

Environment variables are supplied to both containers via one of two mechanisms, both of which are acceptable in Stage 1:

**`.env` file reference.** The `docker-compose.yml` references a `.env` file via the `env_file` directive. The `.env` file is not committed to version control. Its existence and location must be documented in the project README. The `.env.example` file provides the template.

**Inline `environment` block.** Environment variables may be defined in the `docker-compose.yml` `environment` block using variable substitution syntax that reads from the shell environment or a `.env` file. This is functionally equivalent to the `env_file` method.

In either case:
- No secret value may be hardcoded in `docker-compose.yml` or any committed file.
- The `DATABASE_URL` supplied to the API container must reference the PostgreSQL container by its Docker Compose service name (e.g., `db`), not by `localhost` or a host IP.
- The API container's `DATABASE_URL` must use the `postgresql://` or `postgresql+psycopg2://` DSN prefix. The async prefix is prohibited.

### 5.4 Startup Dependency Sequencing

The API container must not attempt to establish a database connection or run application initialization logic before the PostgreSQL container is ready to accept connections.

Docker Compose's `depends_on` directive with a `condition: service_healthy` option must be used to enforce this. The PostgreSQL container must define a health check that confirms PostgreSQL is accepting connections before the API container is allowed to start.

The health check for the PostgreSQL container must verify actual connection acceptance, not merely process existence. A `pg_isready`-based health check is the appropriate mechanism.

The startup dependency sequencing is therefore:

1. PostgreSQL container starts.
2. PostgreSQL health check begins polling.
3. Once PostgreSQL reports healthy, the API container is permitted to start.
4. The API container runs startup validation (environment variables, filesystem checks).
5. The API container connects to PostgreSQL.
6. If Alembic migration is part of the startup sequence, it runs at this point before the application begins accepting requests (see Section 5.5 for the migration execution decision).
7. The FastAPI application begins accepting requests on the configured port.

### 5.5 Database Readiness Gating Discipline

The API container must implement connection retry logic with bounded retry count and sleep interval during startup. This guards against the PostgreSQL container passing its health check before the database engine is fully initialized. The retry must not be indefinite; it must have a maximum retry count after which the API container exits with a non-zero code and a descriptive error.

Alembic migration execution at container startup is acceptable in Stage 1 as a developer-facing convenience (running `alembic upgrade head` as part of the container entrypoint). However, if this approach is used, the following constraints apply:

- Migration must complete successfully before the Uvicorn process starts.
- If migration fails, the entrypoint must exit with a non-zero code without starting the API.
- Migration must not be run concurrently across multiple API container instances. In Stage 1, there is exactly one API container, so this constraint is automatically satisfied.

In production-equivalent environments, migration may alternatively be executed as a separate manual step before the API container is started. Both approaches are acceptable at Stage 1.

### 5.6 Local Development vs Container Parity Rules

The application's behavior must be identical whether it is run as a bare Python process against a local PostgreSQL instance (development mode) or as a containerized process against the Docker Compose PostgreSQL container (container mode).

The following parity rules enforce this:

**No code path may branch on whether the application is running inside Docker.** The `APP_ENV` variable distinguishes `development` from `production`, but it must not be used to infer container vs. non-container execution. No container-detection logic is permitted.

**The `DATABASE_URL` is the only difference between local development and container operation.** In local development, `DATABASE_URL` points to a locally running PostgreSQL instance. In the container, it points to the Compose service name. All other behavior is identical.

**The `UPLOAD_DIRECTORY` path must be configured consistently.** In local development, it is a local directory path. In the container, it is the path at which the uploads volume is mounted. The application code is identical in both cases; only the configured path differs.

**Agent pipeline behavior, canonical output, LLM synthesis, and policy validation must produce identical results regardless of deployment mode.** A PDF processed in local development must produce the same canonical representation and synthesis output as the same PDF processed in the container.

---

## 6. Environment Integration Plan

This section references `env_config_spec.md` as the authoritative definition of all environment variables.

### 6.1 Configuration Loading Order

Environment configuration is loaded once at application startup in the following order:

1. `python-dotenv` reads the `.env` file from the working directory (if present) and loads values into the process environment. This step is a convenience for local development. In containerized deployment, environment variables are pre-populated by Docker Compose before the Python process starts; `python-dotenv` loading is a no-op if variables are already present in the environment.
2. `config.py` reads all environment variables from `os.environ` and subjects them to the validation rules defined in `env_config_spec.md` Section 3.
3. Validated configuration values are stored in a settings object that is imported by modules requiring configuration. No module may call `os.environ` directly outside of `config.py`. All configuration access must go through the settings object.
4. The settings object is initialized once. It is not re-created or re-validated at request time.

### 6.2 Startup Validation Enforcement

Validation must be executed as a blocking step during application initialization, before:

- The SQLAlchemy engine is created.
- The Alembic migration check runs (if applicable).
- FastAPI routes are registered.
- The Uvicorn server begins accepting connections.

The validation sequence within `config.py` must:

1. Confirm all required variables are present in the environment.
2. Apply type enforcement rules as defined in `env_config_spec.md` Section 3.
3. Apply semantic validation where defined (URL prefix checks, length checks, accepted value checks, range checks).
4. Attempt to confirm `UPLOAD_DIRECTORY` writability. If the directory does not exist, attempt to create it. If creation fails, treat as a startup failure.
5. Log the successful configuration summary at `INFO` level, suppressing all secret values (replacing them with a redacted indicator such as `[REDACTED]`).
6. If any validation step fails, emit a descriptive error to stderr and halt the process.

### 6.3 Failure Behavior on Missing Config

If any required environment variable is absent or fails validation:

- The application must emit a message to stderr identifying the variable name, the failure reason, and the expected format or acceptable values.
- The application must not proceed to any subsequent initialization step.
- The process must exit with a non-zero exit code.
- No partial initialization is acceptable. The application must not enter a degraded state or skip validation for variables not yet reached in the sequence.

This behavior is absolute. There is no grace period, delayed validation, or request-time retry of missing configuration.

### 6.4 No Silent Fallback Discipline

No environment variable may have a silent, undocumented fallback. The only variables that may receive default values are the two explicitly optional variables defined in `env_config_spec.md`: `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`. These defaults are documented, logged at startup, and applied only when the variable is absent.

All other variables are required. Their absence is a hard failure.

No variable may derive its value from another variable at runtime. No variable may be conditionally defaulted based on the value of `APP_ENV` or any other variable. No variable may be conditionally omitted from validation based on runtime conditions. The configuration surface is static and fully defined by `env_config_spec.md`.

No secrets may be defaulted under any condition. `JWT_SECRET`, `LLM_API_KEY`, and `DATABASE_URL` must be explicitly provided. Any implementation that defaults a secret variable to a placeholder or development value in a manner that could reach a production environment constitutes a critical compliance violation.

---

## 7. Logging Integration Plan

### 7.1 Logging Initialization Stage

Logging is initialized as the first action in the application startup sequence, before environment variable validation. This ensures that the validation failure messages described in Section 6.3 are captured by the logging system and emitted in a consistent format.

The logging system is configured using the Python standard library `logging` module. The root logger is configured once, at startup, with the level derived from the `LOG_LEVEL` environment variable. If `LOG_LEVEL` is not yet validated when logging is initialized, a temporary default of `INFO` is used for the initialization period only. Once `LOG_LEVEL` is validated, the root logger level is updated to the confirmed value.

All application modules must use loggers derived from the root logger via `logging.getLogger(__name__)`. No module may configure its own handler or level outside of the root configuration established at startup.

### 7.2 What Events Must Be Logged

The following events must be logged at the levels defined in `env_config_spec.md` Section 5. This list is binding:

| Event | Level |
|---|---|
| Application startup with configuration summary (secrets suppressed, shown as `[REDACTED]`) | `INFO` |
| Application startup validation failure (variable name and failure reason) | `ERROR` |
| Application upload received (application_id, file size in bytes) | `INFO` |
| Pipeline execution started (application_id) | `INFO` |
| Each agent invocation (agent_id, agent_name) | `DEBUG` |
| Each agent completion with confidence score (agent_id, agent_name, confidence) | `DEBUG` |
| Canonical assembly completed (canonical_version, application_id) | `INFO` |
| LLM invocation started (application_id, model_name — no prompt content, no canonical data) | `INFO` |
| LLM invocation completed (application_id, confirmation of response received — no response content) | `INFO` |
| LLM invocation timeout or failure (application_id, error type — no API key in message) | `ERROR` |
| Policy validation started (application_id) | `DEBUG` |
| Policy validation result (application_id, policy_passed, count of violations if any) | `INFO` |
| Pipeline completion (application_id, final status: complete or failed) | `INFO` |
| Pipeline failure (application_id, failure reason — no sensitive content) | `ERROR` |

The events listed above represent the minimum required logging. Additional DEBUG-level events within agent logic are acceptable provided they do not log sensitive content.

### 7.3 Log Format Discipline

Each log line must include at minimum:
- Timestamp (ISO 8601 format, UTC-aware)
- Log level (normalized to uppercase: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- Module name (derived from `__name__`)
- Log message

Example format: `2026-03-02T10:15:30Z INFO app.agents.orchestrator Pipeline execution started. application_id=abc123`

Plain text logging to stdout is the defined approach for Stage 1. Structured JSON logging is permitted as an alternative if the team chooses it, provided the same secret suppression rules apply and no external logging agent is introduced.

Log output must go to stdout and/or stderr only. No file-based logging. No log rotation configuration. No external log aggregation target. Container-level log capture is handled by the Docker runtime, not by the application.

### 7.4 No Observability Stack Introduction

Stage 1 does not introduce any of the following:

- Prometheus metrics endpoint
- Grafana dashboard configuration
- Datadog agent or API integration
- New Relic integration
- OpenTelemetry SDK or exporter
- Jaeger or Zipkin trace collection
- Any health check endpoint beyond what FastAPI provides natively (e.g., a simple `/health` route returning HTTP 200 is acceptable; a full observability integration is not)
- Log aggregation services (ELK stack, Loki, Splunk, etc.)
- Distributed trace ID propagation across agents

Logging in Stage 1 is strictly: Python standard library `logging` module, stdout/stderr output, no external target.

---

## 8. Antigravity Implementation Phases

"Antigravity" refers to the implementation team or automated implementation agent responsible for executing the Stage 1 transition. Each phase defines scope, constraints, and validation gates.

---

### Phase 1 — Docker Introduction

**What Antigravity modifies:**
- Introduces a `Dockerfile` in the repository root defining the API container build: base image selection, dependency installation from `requirements.txt`, working directory configuration, and entrypoint definition.
- Introduces a `docker-compose.yml` defining the two-container topology (API + PostgreSQL), the internal network, the two named volumes (database and uploads), the environment variable injection method, the health check for the PostgreSQL container, and the startup dependency relationship.
- Introduces a `.env.example` file listing all variables defined in `env_config_spec.md` with placeholder values.
- Introduces or updates `.gitignore` to ensure `.env` is excluded from version control.

**What Antigravity must not modify:**
- Any file in `app/agents/`
- Any file in `app/canonical/`
- Any file in `app/llm/`
- Any file in `app/policy/`
- Any file in `app/api/`
- Any file in `app/auth/`
- `app/main.py` (beyond what is strictly required for logging initialization, addressed in Phase 6)
- Any Pydantic model definition
- Any agent logic

**Validation checks before proceeding to Phase 2:**
- `docker-compose build` completes without error.
- `docker-compose up` starts both containers.
- The API container starts and is reachable on its configured port.
- The PostgreSQL container passes its health check.
- The API container does not start before PostgreSQL reports healthy.
- No third container is present in the running topology.

---

### Phase 2 — PostgreSQL Connection Binding

**What Antigravity modifies:**
- Updates `app/database.py` to create the SQLAlchemy engine using `DATABASE_URL` from the environment (via the settings object, not `os.environ` directly).
- Confirms that connection pool parameters `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` are bound from the settings object.
- Confirms that the `psycopg2` driver is specified or implied by the DSN prefix.
- Confirms that no async driver or async engine variant is used.

**What Antigravity must not modify:**
- ORM model definitions in `app/models/` (column types and constraints are confirmed, not changed, in this phase; any necessary corrections are made only to align with `database_schema_v1.md`)
- Any agent logic
- Any canonical model

**Validation checks before proceeding to Phase 3:**
- The application connects successfully to the PostgreSQL container on startup.
- A manual SQLAlchemy session query against the PostgreSQL instance returns without error (even if no tables exist yet).
- Connection pool parameters are confirmed as bound from environment variables, not hardcoded.

---

### Phase 3 — Alembic Initialization

**What Antigravity modifies:**
- Initializes Alembic in the repository, creating `alembic/` directory and `alembic.ini`.
- Configures `alembic.ini` to not contain a hardcoded database URL.
- Configures `alembic/env.py` to read `DATABASE_URL` from the environment at runtime.
- Configures `alembic/env.py` to import ORM models from `app/models/`.
- Creates the first migration revision (`0001`) enabling UUID support (extension enablement), following Section 3.2 of this document.

**What Antigravity must not modify:**
- Any agent logic
- Any canonical model
- Any API route handler
- The ORM model column definitions (these are confirmed in Phase 2; Alembic works with them as-is)

**Validation checks before proceeding to Phase 4:**
- `alembic current` runs without error and shows no applied migrations (baseline state).
- `alembic upgrade head` applies the UUID extension migration without error.
- `alembic current` shows revision `0001` as current.
- `alembic downgrade -1` reverts without error (subject to the data-existence guard described in Section 4.3).
- `alembic upgrade head` re-applies cleanly.

---

### Phase 4 — Schema Enforcement

**What Antigravity modifies:**
- Creates Alembic migration revisions for all four tables as defined in `database_schema_v1.md`.
- Each migration script is named following the convention defined in Section 4.1.
- Migration scripts are reviewed against `database_schema_v1.md` before being committed.
- Applies all migrations via `alembic upgrade head`.

**What Antigravity must not modify:**
- Any agent logic
- Any canonical model
- Any LLM client behavior
- Any policy guard logic

**Validation checks before proceeding to Phase 5:**
- All validation queries described in Section 3.8 pass successfully.
- `alembic current` shows the latest migration revision as current.
- No table exists in the database beyond the four defined tables.
- All constraints, indexes, and foreign key relationships are confirmed present and correctly named.
- A test record insert into `users`, followed by `applications`, `canonical_records`, and `synthesis_records` succeeds.
- All check constraint violation tests confirm rejection as described in Section 3.8.
- Cascade delete behavior is confirmed as described in Section 3.8.

---

### Phase 5 — Config Integration

**What Antigravity modifies:**
- Implements or confirms the full `config.py` startup validation routine as defined in `env_config_spec.md` Sections 2 and 3.
- Confirms that all twelve required variables are validated at startup.
- Confirms that `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` defaults are applied and logged when absent.
- Confirms that the settings object is the sole configuration access point for all modules.
- Confirms that no module reads `os.environ` directly outside of `config.py`.
- Confirms that the `UPLOAD_DIRECTORY` writability check runs at startup.

**What Antigravity must not modify:**
- Any agent logic
- Any canonical model
- Any API route handler (beyond ensuring they access configuration through the settings object)

**Validation checks before proceeding to Phase 6:**
- Starting the application with a missing required variable causes a non-zero exit and a descriptive stderr message before any network binding occurs.
- Starting the application with an invalid `JWT_SECRET` (too short) causes a non-zero exit.
- Starting the application with an invalid `DATABASE_URL` prefix causes a non-zero exit.
- Starting the application with all valid variables results in a startup configuration summary log at `INFO` level showing all variables with secrets suppressed as `[REDACTED]`.
- `UPLOAD_DIRECTORY` is confirmed writable; the directory is created if absent.

---

### Phase 6 — Logging Integration

**What Antigravity modifies:**
- Implements logging initialization at the start of the application startup sequence in `app/main.py` or a dedicated logging configuration module imported by `main.py`.
- Confirms that the root logger is configured from `LOG_LEVEL` at startup.
- Confirms that all pipeline lifecycle events defined in Section 7.2 emit log messages at the correct levels.
- Introduces log statements into orchestrator, agent modules, LLM client, and policy guard at the levels defined in `env_config_spec.md` Section 5.
- Confirms that no secret values appear in any log output.

**What Antigravity must not modify:**
- Agent logic beyond adding log statements.
- Canonical model structure.
- LLM client behavior beyond adding log statements at defined points.
- Policy guard logic beyond adding log statements at defined points.
- API route handler logic beyond adding log statements at defined points.

**Validation checks before proceeding to Phase 7:**
- Processing a sample PDF through the full pipeline produces log output containing all required pipeline lifecycle events.
- Log output confirms `application_id` is present in pipeline start, LLM invocation, and policy validation log entries.
- Log output confirms no secret values (JWT secret, LLM API key, database password) appear at any log level.
- LLM invocation log entries confirm that prompt content and canonical data are not logged.
- Setting `LOG_LEVEL=DEBUG` produces agent-level invocation and confidence score log entries.
- Setting `LOG_LEVEL=INFO` suppresses agent-level entries while retaining pipeline lifecycle entries.

---

### Phase 7 — End-to-End Container Validation

**What Antigravity modifies:**
- Nothing. Phase 7 is a validation-only phase. No code, schema, or configuration changes are made.

**What Antigravity must not modify:**
- Anything. This phase is read-only validation.

**Validation checks (this is the complete Stage 1 completion gate):**

1. `docker-compose up --build` starts both containers cleanly with a valid `.env` file.
2. PostgreSQL health check passes before the API container starts.
3. API container startup log confirms environment validation passed for all variables.
4. Alembic migrations are confirmed current (`alembic current` shows head revision).
5. All four database tables exist with correct schema as confirmed by validation queries from Section 3.8.
6. POST `/register` creates a user with a hashed password and the correct role.
7. POST `/login` returns a valid JWT for a registered user.
8. POST `/applications/upload` with a sample PDF:
   - Saves the file to the uploads volume.
   - Runs the full deterministic pipeline (Agents 1–11).
   - Calls the LLM synthesis agent exactly once.
   - Runs policy validation.
   - Persists a `canonical_records` row with `canonical_version = "1.0"` and valid JSONB `canonical_data`.
   - Persists a `synthesis_records` row with valid JSONB `synthesis_output` and a `policy_passed` value.
   - Returns a synthesis output response containing `snapshot`, `discussion_focus_areas`, and `suggested_questions`.
9. GET `/applications/{id}` returns the stored synthesis output for a previously processed application.
10. GET `/applications/{id}` returns an authorization error for a user who did not upload the application and does not hold the `admin` role.
11. Log output from the full pipeline run contains all required events at correct levels and contains no secret values.
12. The canonical data in `canonical_records.canonical_data` contains `academic_entries`, `test_entries`, `essay_entries`, `activity_entries`, and `timeline_entries` as arrays. No fixed academic-level key (e.g., `class_12`) appears in the JSONB document.
13. Container restart (`docker-compose restart`) preserves the database volume. The previously created `canonical_records` and `synthesis_records` rows are accessible after restart.
14. No third container exists in the running topology.
15. No Redis connection attempt is present in the logs or container configuration.
16. No LangChain, LangGraph, or equivalent framework import appears in any Python module.

---

## 9. Rollback Strategy

### 9.1 How to Revert to Stage 0

A rollback to Stage 0 restores the application to a state where it runs as a bare Python process against a local database without containerization. The rollback procedure is:

1. Stop and remove all Stage 1 Docker containers and networks: `docker-compose down`.
2. Confirm that the Stage 0 branch or commit is accessible in version control.
3. Restore the Stage 0 codebase from version control.
4. Confirm the Stage 0 database connection target (SQLite or a pre-Stage-1 PostgreSQL instance).
5. Restore environment configuration to Stage 0 values.
6. Start the application as a bare Python process.

Stage 0 rollback does not recover Stage 1 data. If canonical records or synthesis records were created during Stage 1 operation, they remain in the Stage 1 database. If Stage 1 used SQLite in Stage 0 and PostgreSQL in Stage 1, the Stage 0 codebase reconnects to its original SQLite database.

The Docker volumes created during Stage 1 may be retained or removed at operator discretion. Volume retention allows re-entry into Stage 1 without data loss.

### 9.2 Migration Rollback Approach

To roll back the database schema to a pre-Stage-1 state:

1. Confirm that all Stage 1 tables are empty. If data exists, document the rollback data loss before proceeding.
2. Execute `alembic downgrade base` to reverse all applied migrations.
3. Confirm that all four Stage 1 tables no longer exist in the database.
4. If rolling back to a Stage 0 SQLite configuration, no further database action is required. If rolling back to a pre-Alembic PostgreSQL state, the `alembic_version` table must also be removed manually (this is the only permitted manual DDL, and only in the context of a confirmed rollback operation).

Downgrade must not be executed if data exists without explicit operator confirmation and documentation of data loss. Downgrade of table-creation migrations destroys all data in those tables.

### 9.3 Database Fallback Discipline

The database fallback during rollback follows these rules:

**No automatic rollback.** Database rollback is an explicit operator action. No automated trigger, health check failure response, or deployment tooling initiates a schema downgrade automatically.

**Rollback is destructive.** Operators must confirm that the data in the Stage 1 tables is either expendable (test data) or has been exported to a recoverable format before initiating a schema downgrade.

**Alembic state must be consistent after rollback.** After a rollback, `alembic current` must reflect the target revision (or show no current revision if rolled back to base). An inconsistent Alembic state (where the `alembic_version` table disagrees with the actual schema state) is a drift condition that must be remediated before the system is usable again.

**Volume data is independent of schema rollback.** Rolling back the schema does not remove the uploads volume. PDF files stored in the uploads volume remain on disk. Operators must decide whether to retain or remove these files as part of a rollback decision.

---

## 10. Stage 1 Completion Criteria

Stage 1 is complete when all of the following criteria are satisfied. These criteria are non-negotiable. Partial satisfaction does not constitute Stage 1 completion.

### 10.1 Required Validations

All validation checks defined in Phase 7 of Section 8 must pass. These constitute the minimum required validations. No criterion in Phase 7 may be waived.

### 10.2 Schema Correctness Checks

- Exactly four tables exist in the target PostgreSQL database: `users`, `applications`, `canonical_records`, `synthesis_records`.
- All columns in all tables match the definitions in `database_schema_v1.md` with respect to name, type, nullability, and default values.
- All primary keys are UUID type with database-level generation defaults.
- All foreign keys are declared with the correct references and deletion behaviors (RESTRICT for `users → applications`, CASCADE for `applications → canonical_records` and `applications → synthesis_records`).
- All check constraints are active and verified via test inserts.
- All unique constraints are active and enforced.
- `canonical_records.canonical_data`, `synthesis_records.synthesis_output`, and `synthesis_records.policy_violations_log` are of type `jsonb`.
- `canonical_records.canonical_version` index exists.
- `synthesis_records.policy_passed` index exists.
- `applications.uploaded_by` index exists.
- No GIN index on any JSONB column has been introduced.
- No column exists beyond those defined in `database_schema_v1.md`.
- Alembic revision history is clean and committed to version control.
- `alembic current` shows the expected head revision.

### 10.3 Env Validation Checks

- All twelve required environment variables are validated at startup.
- Missing any required variable causes a pre-startup failure with a descriptive error.
- `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` defaults are applied and logged when absent.
- `JWT_SECRET` validation confirms minimum length and rejects known placeholder values.
- `DATABASE_URL` validation confirms synchronous driver prefix.
- `LLM_ENDPOINT` validation confirms HTTPS URL format.
- `APP_ENV` accepts only `development` or `production`.
- `LOG_LEVEL` accepts only the five defined values.
- No secret value appears in startup log output.
- `.env.example` exists in the repository with all variables listed and placeholder values for secrets.
- `.env` is present in `.gitignore`.

### 10.4 Container Startup Validation

- `docker-compose up --build` completes without error.
- Exactly two containers are running after startup.
- PostgreSQL health check passes and the API container respects the `depends_on: condition: service_healthy` dependency.
- No third container is present.
- Database volume persistence is confirmed: data survives container restart.
- Upload volume persistence is confirmed: stored PDFs survive container restart.
- No hardcoded database URL, JWT secret, or LLM API key appears in any committed file.

### 10.5 Canonical + LLM Flow Validation

- A complete pipeline run with a real PDF produces a `canonical_records` row with:
  - `canonical_version = "1.0"`
  - `canonical_data` containing all required top-level keys
  - All collection fields (`academic_entries`, `test_entries`, `essay_entries`, `activity_entries`, `timeline_entries`) present as arrays
  - No fixed academic-level key (e.g., `class_12`, `class_10`, `grade_11`) present as a top-level or nested key in the JSONB document
  - PII fields present only within the `identifiers` object, not merged into academic or essay entries
- A complete pipeline run produces a `synthesis_records` row with:
  - `synthesis_output` containing `snapshot` (string), `discussion_focus_areas` (array), `suggested_questions` (array), `canonical_version_ref` (string matching the associated canonical record's `canonical_version`)
  - `policy_passed` field correctly reflecting whether policy validation passed
  - No evaluative language in the `synthesis_output` content
- The LLM was called exactly once during the pipeline run (confirmed via log output: exactly one LLM invocation start and one LLM invocation completion event, with no retry or secondary call).
- Policy guard was invoked after LLM synthesis and before storage (confirmed via log output: policy validation start and result events appear after LLM invocation completion event).
- GET `/applications/{id}` returns the stored `synthesis_output` without re-invoking the pipeline or LLM.
- No LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent framework import is present in any Python module.
- No Redis, Celery, RQ, Kafka, MinIO, NGINX, Kubernetes, or cloud provider integration is present in any configuration, container definition, or Python module.

---

## Constraint Check

The following table confirms that this migration plan fully complies with all architectural invariants. Each confirmation is based on explicit evidence within the document sections above.

| Constraint | Status | Evidence |
|---|---|---|
| **Deterministic-first preserved** | ✅ | Section 1.2 explicitly states the logical pipeline is unchanged. Section 2.1 confirms all agent modules in `app/agents/` are carried forward without modification. Phase definitions in Section 8 explicitly prohibit modification of any agent logic. No section of this plan introduces LLM involvement in extraction stages. |
| **Single LLM call preserved** | ✅ | Section 1.2 explicitly confirms the LLM synthesis contract is unchanged. Section 2.1 confirms `llm/client.py` is carried forward unchanged. Phase 7 validation (Section 8) requires confirmation that the LLM was called exactly once per pipeline run. No retry, no chaining, no secondary call is introduced by any element of this plan. |
| **No evaluation logic introduced** | ✅ | No section of this plan introduces scoring, ranking, normalization, strength/weakness labeling, concern detection, or admissions inference. Section 3.8 validation queries confirm no prohibited columns exist in the schema. Phase 7 validation confirms no evaluative language appears in synthesis output. Section 10.5 confirms no evaluative language is present in stored synthesis records. |
| **Collection-based canonical preserved** | ✅ | Section 3.8 and Section 10.5 both require confirmation that all canonical collection fields (`academic_entries`, `test_entries`, `essay_entries`, `activity_entries`, `timeline_entries`) are arrays in the stored JSONB document. No section introduces fixed-key alternatives to these collections. `database_schema_v1.md` JSONB governance (referenced in Section 3.8) explicitly forbids relational decomposition of canonical collections. |
| **No rigid key paths introduced** | ✅ | Section 10.5 explicitly requires validation that no fixed academic-level key (e.g., `class_12`, `class_10`, `grade_11`) appears in the JSONB canonical document. No Alembic migration in this plan introduces columns named for specific academic levels, test names, or essay identifiers. No configuration variable encodes academic structure. |
| **No async introduced** | ✅ | Section 5 (Dockerization) defines exactly two containers with no async worker container. Section 6.4 confirms no async driver DSN prefix is permitted. Section 3.3 confirms the `psycopg2` synchronous driver. Section 7 (Section 7 under Dockerization) — no Redis, Celery, RQ, or Kafka configuration variable is defined or introduced. All prohibited async infrastructure categories are explicitly listed as absent in `env_config_spec.md` Section 7, which this plan references and enforces. |
| **No infrastructure creep beyond Stage 1** | ✅ | Section 5.1 defines exactly two containers and prohibits all additional containers by name. Section 6.4 prohibits all configuration variables associated with Redis, queues, object storage, monitoring stacks, cloud providers, Kubernetes, and audit logging. Phase validation gates in Section 8 confirm topology contains exactly two containers. Section 10.4 requires confirmation that no third container is present. |
| **No service separation introduced** | ✅ | Section 5.1 establishes a two-container topology where all agent logic runs inside the single API container as internal modules. No service-to-service communication variable, no inter-service network definition, and no routing configuration is introduced at any point in this plan. Architecture_lock.md Section 7 prohibits service separation before Stage 4, and this plan introduces no mechanism that would enable or imply such separation. |
| **No additional LLM frameworks introduced** | ✅ | Section 2.1 confirms `llm/client.py` is carried forward unchanged — a direct `httpx` synchronous call with no orchestration framework. Phase definitions in Section 8 explicitly prohibit modification of LLM client behavior. Phase 7 validation (Section 8) and Section 10.5 both require confirmation that no LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent framework import is present in any module. No orchestration variable appears in the environment configuration. |

---

*End of `stage_1_migration_plan.md`.*

*Document Version: 1.0 | Stage: 1 — Structured MVP | Governing Architecture Version: architecture_lock.md*
