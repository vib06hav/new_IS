# Stage 0 Finalization Document

---

## 1. Final Project Structure

```
app/
  main.py                        # FastAPI application entry point
  config.py                      # Environment variable loading
  database.py                    # SQLAlchemy engine and session factory

  auth/
    router.py                    # /register and /login route handlers
    service.py                   # Registration and login logic
    security.py                  # Password hashing and JWT encode/decode
    schemas.py                   # Pydantic request/response models for auth

  agents/
    orchestrator.py              # Agent 0: Pipeline Orchestrator
    layout_extractor.py          # Agent 1: Layout Block Extractor
    section_detector.py          # Agent 2: Section Boundary Detector
    personal_extractor.py        # Agent 3: Personal Information Extractor
    academic_extractor.py        # Agent 4: Academic Records Extractor
    test_extractor.py            # Agent 5: Standardized Test Extractor
    essay_extractor.py           # Agent 6: Essay Extractor
    activity_extractor.py        # Agent 7: Activity Extractor
    cross_section_detector.py    # Agent 8: Cross-Section Entity Detector
    timeline_builder.py          # Agent 9: Timeline Builder
    integrity_analyzer.py        # Agent 10: Completeness & Integrity Analyzer
    assembler.py                 # Agent 11: Canonical Structure Assembler
    synthesis_agent.py           # Agent 12: Interview Preparation Generator
    validation_filter.py         # Agent 13: Output Validation Filter

  canonical/
    model.py                     # Pydantic models for canonical representation
    version.py                   # canonical_version constant and versioning logic

  llm/
    client.py                    # LLM wrapper: single-call interface

  policy/
    guard.py                     # Policy validation runner
    config.py                    # Policy rule configuration (externalized)

  models/
    user.py                      # SQLAlchemy ORM model: users table
    application.py               # SQLAlchemy ORM model: applications table
    canonical_record.py          # SQLAlchemy ORM model: canonical_records table
    synthesis_record.py          # SQLAlchemy ORM model: synthesis_records table

  api/
    applications.py              # /applications/upload and /applications/{id} handlers
    schemas.py                   # Pydantic request/response models for applications

uploads/                         # Local PDF storage directory (runtime)
.env                             # Environment variable definitions
requirements.txt
```

**Notes on structure:**
- Every agent is an isolated, importable Python module with no cross-agent dependencies except through explicit structured input/output.
- `canonical/` is logically separate from `agents/` to enforce the distinction between extraction and representation assembly.
- `policy/config.py` holds externalized rule definitions; `policy/guard.py` consumes them. No policy logic lives inside agent modules.

---

## 2. Final Database Schema

### Table: `users`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | Primary key, default generated |
| email | VARCHAR(320) | Not null, unique |
| password_hash | VARCHAR(255) | Not null |
| role | VARCHAR(50) | Not null, constrained to: admin, interviewer |
| created_at | TIMESTAMP | Not null, default now() |

---

### Table: `applications`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | Primary key, default generated |
| uploaded_by | UUID | Foreign key → users.id, not null |
| file_path | VARCHAR(512) | Not null |
| pipeline_status | VARCHAR(50) | Not null (values: processing, complete, failed) |
| pipeline_confidence | NUMERIC(5,4) | Nullable (aggregated confidence, 0.0–1.0) |
| created_at | TIMESTAMP | Not null, default now() |

**Note:** `pipeline_status` supports basic error-state tracking without introducing job queues. It is set synchronously within the request lifecycle.

---

### Table: `canonical_records`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | Primary key, default generated |
| application_id | UUID | Foreign key → applications.id, not null, unique |
| canonical_version | VARCHAR(20) | Not null |
| canonical_data | JSONB | Not null |
| created_at | TIMESTAMP | Not null, default now() |

**Note:** `canonical_data` stores the full canonical representation as a structured JSONB document. JSONB is chosen over TEXT for queryability without imposing rigid relational schema on the collection-based structure.

---

### Table: `synthesis_records`

| Column | Type | Constraints |
|---|---|---|
| id | UUID | Primary key, default generated |
| application_id | UUID | Foreign key → applications.id, not null, unique |
| synthesis_output | JSONB | Not null |
| policy_passed | BOOLEAN | Not null |
| policy_violations_log | JSONB | Nullable |
| created_at | TIMESTAMP | Not null, default now() |

**Note:** `policy_violations_log` stores structured violation metadata for any output that was sanitized, not the raw prohibited text.

---

### Relationships Summary

- `applications.uploaded_by` → `users.id` (many-to-one)
- `canonical_records.application_id` → `applications.id` (one-to-one)
- `synthesis_records.application_id` → `applications.id` (one-to-one)

No additional tables are required in Stage 0.

---

## 3. Canonical JSON Field Naming Conventions

The following defines the top-level structure and field naming of `canonical_data` stored in `canonical_records.canonical_data`. This is a transport-level representation, not a storage schema.

### Top-Level Structure

```
canonical_version         string
identifiers               object
profile_meta              object
academic_entries          array
test_entries              array
essay_entries             array
activity_entries          array
timeline_entries          array
cross_references          object
integrity_report          object
extraction_confidence     object
```

---

### `identifiers` fields (PII, logically separated)

```
application_id            string
full_name                 string or null
date_of_birth             string or null (raw, not parsed)
declared_preferences      object (key-value, label-preserved)
demographic_flags         object (key-value, normalized yes/no only)
```

---

### `profile_meta` fields

```
source_document_page_count     integer
extraction_timestamp           string (ISO 8601)
layout_block_count             integer
detected_section_labels        array of strings
```

---

### `academic_entries` — each entry

```
entry_id                  string (UUID)
academic_level            string (raw label, e.g. "Class 10", "Year 12", "Grade 11")
board_name                string or null
academic_year             string or null (raw, e.g. "2023-24")
marking_scheme_raw        string or null (raw label, e.g. "CGPA", "Percentage", "A-Level grades")
grading_mode              string (extensible: "percentage", "cgpa", "letter_grade", "unknown")
score_raw                 string or null
predicted_score_raw       string or null
subject_entries           array (see below)
component_tags            array of strings
confidence_score          float (0.0–1.0)
```

**`subject_entries` — each item:**
```
subject_name              string
score_raw                 string or null
predicted_score_raw       string or null
component_tag             string or null
```

---

### `test_entries` — each entry

```
entry_id                  string (UUID)
test_name                 string (raw label, e.g. "SAT", "JEE Mains", "IELTS")
test_date                 string or null (raw)
total_score               string or null (raw)
sectional_scores          array of objects (label + raw_score)
percentile                string or null (raw)
rank                      string or null (raw)
result_status             string (values: "available", "awaited", "not_attempted")
confidence_score          float (0.0–1.0)
```

---

### `essay_entries` — each entry

```
entry_id                  string (UUID)
essay_identifier          string (raw prompt label or positional identifier)
raw_text                  string
word_count                integer
character_count           integer
placeholder_flag          boolean
duplication_ratio         float (0.0–1.0)
short_response_flag       boolean
confidence_score          float (0.0–1.0)
```

---

### `activity_entries` — each entry

```
entry_id                  string (UUID)
category                  string or null (raw label)
activity_name             string or null
level                     string or null (raw, e.g. "National", "School")
duration                  string or null (raw)
description_raw           string or null
upload_flag               boolean
confidence_score          float (0.0–1.0)
```

---

### `timeline_entries` — each entry

```
entry_id                  string (UUID)
year                      string (raw, e.g. "2022", "2023-24")
event_label               string
source_type               string (values: "academic", "test", "activity", "essay")
source_reference          string (entry_id of originating entry)
```

---

### `cross_references` structure

```
entity_map                array of objects:
  entity_token            string
  source_references       array of objects:
    source_type           string
    entry_id              string
```

---

### `integrity_report` structure

```
anomalies                 array of objects:
  anomaly_id              string (UUID)
  anomaly_type            string (e.g. "missing_section", "duplicate_essay", "placeholder_response", "ambiguous_grading")
  severity_level          string (values: "low", "medium", "high", "critical")
  source_reference        string or null (entry_id or section label)
  description             string
```

---

### `extraction_confidence` structure

```
agent_scores              array of objects:
  agent_id                integer (0–11)
  agent_name              string
  confidence_score        float (0.0–1.0)
aggregate_confidence      float (0.0–1.0)
```

---

### Canonical Version

`canonical_version` is a plain string following the pattern: `"1.0"`, `"1.1"`, etc. The Stage 0 value is `"1.0"`. It is defined as a constant in `canonical/version.py` and stamped at assembly time.

---

### `synthesis_output` structure (stored in `synthesis_records.synthesis_output`)

```
snapshot                  string
discussion_focus_areas    array of strings
suggested_questions       array of strings
canonical_version_ref     string (must match canonical_version of the linked record)
```

---

## 4. Selected Python Libraries

| Library | Role | Justification |
|---|---|---|
| **FastAPI** | Web framework | Specified by stage_0_implementation_spec.md. Native Pydantic integration, synchronous support, minimal overhead. |
| **Uvicorn** | ASGI server | Standard paired server for FastAPI. Synchronous workloads served without async worker complexity. |
| **SQLAlchemy (2.x)** | ORM | Mature, explicit ORM. Allows declarative model definitions with clear column-level control. Avoids schema inference. |
| **Alembic** | Database migrations | Paired with SQLAlchemy. Provides versioned, explicit schema migration without runtime schema inference. |
| **psycopg2-binary** | PostgreSQL driver | Synchronous PostgreSQL driver compatible with SQLAlchemy. No async driver introduced. |
| **Pydantic (v2)** | Data validation and canonical modeling | Native to FastAPI. Used to define canonical entry models, ensuring structured validation without implicit inference. |
| **python-jose** | JWT encoding/decoding | Lightweight, no third-party auth provider dependency. Complies with architecture_lock.md prohibition on SaaS auth. |
| **passlib[bcrypt]** | Password hashing | Provides bcrypt hashing as required by stage_0_implementation_spec.md. No additional security framework. |
| **pdfminer.six** | PDF layout extraction | Deterministic PDF text and layout block extraction. No LLM involvement. Provides page-level and block-level structure. |
| **python-multipart** | File upload handling | Required by FastAPI for multipart form file uploads. No additional dependency. |
| **httpx** | LLM API HTTP client | Synchronous HTTP client for single LLM API call. Simple, dependency-minimal, no orchestration layer. |
| **python-dotenv** | Environment variable loading | Loads `.env` file into environment. No secrets manager required at Stage 0. |
| **pytest** | Testing | Standard Python testing framework. Unit tests for agents and policy guard. |

**Libraries explicitly not selected:**
- LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel — prohibited by architecture_lock.md
- Celery, RQ — prohibited by Stage 0 scope
- boto3, minio — prohibited by Stage 0 scope
- Redis clients — prohibited by Stage 0 scope

---

## 5. LLM Client Design (Interface Definition Only)

### Module: `llm/client.py`

**Purpose:** Single controlled gateway for all LLM interaction. Exactly one public function is exposed. No other module may make HTTP calls to an LLM endpoint.

---

**Function: `generate_synthesis`**

| Property | Definition |
|---|---|
| Input | A fully assembled canonical representation object (Pydantic-validated) |
| Output | A structured synthesis result object conforming to `synthesis_output` schema |
| LLM calls made | Exactly one |
| Retry behavior | None (Stage 0: single attempt, failure propagated as pipeline error) |
| Timeout | Configurable via environment variable |
| Framework | Direct HTTP call via httpx synchronous client |
| Prompt construction | Internally assembled from canonical categories; no rigid key path references |

**Prompt construction rules (interface-level):**
- The prompt references semantic collection labels (e.g., "academic entries", "essay entries") not field key paths.
- The prompt explicitly injects invariant rules from `llm_synthesis_contract.md` as system-level instructions.
- The prompt specifies the exact output structure expected (`snapshot`, `discussion_focus_areas`, `suggested_questions`).
- No dynamic prompt modification by agents. Prompt template is static and versioned inside `llm/client.py`.

**Post-call behavior:**
- Raw LLM response is parsed into the `synthesis_output` structure.
- Parsed output is passed directly to the Policy Guard before any storage or return.
- The client does not make a second call under any circumstance.

---

## 6. Policy Guard Structure (Configuration Structure Only)

### Module: `policy/guard.py`

**Purpose:** Scans synthesis output for prohibited content patterns. Rejects or sanitizes non-compliant output. Logs violations structurally.

### Module: `policy/config.py`

**Purpose:** Externalized configuration for all policy rules. No rule logic lives here — only declarative rule definitions consumed by `guard.py`.

---

### Policy Configuration Structure

`policy/config.py` exposes a configuration object with the following structural shape:

```
policy_version            string (e.g. "1.0")

rule_sets                 array of rule_set objects:

  rule_set_id             string
  rule_set_name           string (e.g. "evaluative_language", "comparative_constructs", "ranking_statements", "prescriptive_advice", "normative_performance")
  enabled                 boolean
  action                  string (values: "reject", "sanitize")
  severity                string (values: "critical", "high", "medium")

  rules                   array of rule objects:
    rule_id               string
    rule_type             string (values: "pattern_match", "phrase_class", "structural_scan")
    description           string
    target_fields         array of strings (which output fields to scan: "snapshot", "discussion_focus_areas", "suggested_questions")
    match_definition      object (type-specific definition of what constitutes a match — no hardcoded word lists embedded here; lists are loaded from separate data files referenced by path)
    case_sensitive        boolean
```

**Separation principle:** The `match_definition` for `phrase_class` rules references a named external file path or identifier. Word lists and phrase patterns are stored as versioned data files, not embedded in `config.py`. This ensures `config.py` remains a structural configuration, not an implicit logic layer.

---

### Policy Guard Execution Contract

| Step | Behavior |
|---|---|
| 1 | Receive parsed synthesis output from LLM client |
| 2 | Load active policy config from `policy/config.py` |
| 3 | For each enabled rule_set, scan all targeted output fields |
| 4 | On match: apply configured action (reject or sanitize) |
| 5 | Append matched rule_id and field reference to `violations_log` |
| 6 | Return: (passed: boolean, sanitized_output or None, violations_log) |

If `action` is `"reject"`, no synthesis output is stored and the pipeline returns a structured error. If `action` is `"sanitize"`, the offending content is removed or replaced with a neutral placeholder, and the modified output proceeds to storage with `policy_passed: false` and the violations log populated.

---

## 7. Step-by-Step Implementation Order

This order is designed so that each step produces a testable, stable artifact before the next step begins.

---

### Phase 1 — Project Foundation

**Step 1: Repository and environment setup**
Initialize repository. Define `requirements.txt`. Set up `.env` template with all required environment variables (`DATABASE_URL`, `JWT_SECRET`, `LLM_ENDPOINT`, `LLM_MODEL_NAME`, `UPLOAD_DIRECTORY`). Configure `config.py` to load and expose these values. No application logic yet.

**Step 2: Database initialization**
Implement SQLAlchemy engine and session factory in `database.py`. Define all four ORM models in `models/`. Configure Alembic. Generate and apply initial migration. Confirm tables exist and relationships are enforced. No application logic yet.

**Step 3: FastAPI application skeleton**
Implement `main.py` with FastAPI instance, no routes yet. Confirm application starts and health check endpoint responds. Confirm database session dependency injection works.

---

### Phase 2 — Authentication Layer

**Step 4: Auth security primitives**
Implement `auth/security.py`: bcrypt password hashing function and JWT encode/decode functions. Unit test both independently.

**Step 5: Auth service and routes**
Implement `auth/service.py` (registration and login logic against `users` table). Implement `auth/router.py` with POST /register and POST /login. Define `auth/schemas.py`. Test registration creates hashed password. Test login returns valid JWT. Test role field is persisted.

---

### Phase 3 — Canonical Model Definition

**Step 6: Canonical Pydantic models**
Implement all Pydantic models in `canonical/model.py` reflecting the field naming conventions defined in Section 3 of this document. Implement `canonical/version.py` with `CANONICAL_VERSION = "1.0"`. No agent logic yet. Unit test model instantiation with sample data.

---

### Phase 4 — Deterministic Agent Pipeline

Each agent is implemented and unit tested in isolation before integration. Agents are implemented in pipeline order.

**Step 7: Agent 1 — Layout Block Extractor**
Implement PDF ingestion and ordered block extraction using pdfminer.six. Output: ordered list of block objects with page number, position metadata, and raw text. Include confidence score. Unit test against a sample PDF.

**Step 8: Agent 2 — Section Boundary Detector**
Implement section boundary detection over block stream. Support fuzzy header matching and formatting heuristics. Output: list of labeled sections with block ranges and confidence scores. Allow unknown section labels. Unit test with varied section header formats.

**Step 9: Agent 3 — Personal Information Extractor**
Implement label-based field extraction within the personal information section. Output: `identifiers` and `profile_meta` objects. No inference. Unit test.

**Step 10: Agent 4 — Academic Records Extractor**
Implement collection-based academic record extraction. Each record becomes an `academic_entry`. No fixed level keys. Preserve raw values. Unit test with multiple academic system formats.

**Step 11: Agent 5 — Standardized Test Extractor**
Implement test record extraction as collection. Handle missing subfields and awaited results. Unit test.

**Step 12: Agent 6 — Essay Extractor**
Implement essay extraction as collection. Compute word count, character count, detect placeholders and duplication. No quality assessment. Unit test.

**Step 13: Agent 7 — Activity Extractor**
Implement activity extraction as collection. No ranking or importance inference. Unit test.

**Step 14: Agent 8 — Cross-Section Entity Detector**
Implement token-filtered entity detection across essay, activity, academic, and test entries. Build `cross_references.entity_map`. Unit test.

**Step 15: Agent 9 — Timeline Builder**
Implement event-based timeline construction from all entry collections. Each event references its source entry. No trend detection. Unit test.

**Step 16: Agent 10 — Completeness & Integrity Analyzer**
Implement structural anomaly detection. Generate `integrity_report.anomalies` with typed severity levels. No quality inference. Unit test with documents containing deliberate structural gaps.

**Step 17: Agent 11 — Canonical Structure Assembler**
Implement assembly of all agent outputs into the canonical representation defined in Section 3. Stamp `canonical_version`. Separate identifiers from extracted content. Unit test with full mock pipeline output.

---

### Phase 5 — Pipeline Orchestration

**Step 18: Agent 0 — Pipeline Orchestrator**
Implement `agents/orchestrator.py` to execute Agents 1–11 in fixed order. Accept raw PDF path and return assembled canonical representation. Handle recoverable errors (agent-level failures that produce degraded but valid output with low confidence). Abort on critical failures. No extraction logic in orchestrator. Integration test with a sample PDF end-to-end through Agent 11.

---

### Phase 6 — LLM Synthesis Layer

**Step 19: LLM client wrapper**
Implement `llm/client.py` with `generate_synthesis` function as defined in Section 5. Static prompt template referencing semantic categories. Single synchronous httpx call. Parse response into `synthesis_output` Pydantic model. Unit test with mocked LLM response.

**Step 20: Agent 12 — Synthesis Agent**
Implement `agents/synthesis_agent.py` as a thin wrapper that receives the canonical representation, calls `llm/client.py`, and returns the parsed synthesis result. No logic beyond invoking the client and passing output forward.

---

### Phase 7 — Policy Guard

**Step 21: Policy configuration**
Define `policy/config.py` with initial rule_set structure for all five prohibited categories. Reference external pattern data files. Define `policy_version = "1.0"`.

**Step 22: Policy guard implementation**
Implement `policy/guard.py` consuming the config structure. Implement pattern scanning for each rule type. Return structured result with `passed`, `output`, and `violations_log`. Unit test with deliberately non-compliant synthesis outputs. Unit test with compliant output.

**Step 23: Agent 13 — Output Validation Filter**
Implement `agents/validation_filter.py` as a wrapper calling `policy/guard.py`. Returns filtered synthesis output or structured error.

---

### Phase 8 — Application API

**Step 24: File upload and pipeline endpoint**
Implement `api/applications.py` with POST /applications/upload. Accept PDF, save to `UPLOAD_DIRECTORY`, create `applications` record, run orchestrator synchronously, persist `canonical_records` and `synthesis_records`, return synthesis output in response. Implement `api/schemas.py` for request and response models. Protect with JWT auth dependency.

**Step 25: Retrieval endpoint**
Implement GET /applications/{id}. Return stored `synthesis_output` from `synthesis_records`. Verify application belongs to requesting user or requester has admin role. Protect with JWT.

**Step 26: Router registration**
Register `auth/router.py` and `api/applications.py` routers in `main.py`.

---

### Phase 9 — Integration and Validation

**Step 27: End-to-end integration test**
Run full pipeline with a real PDF. Confirm: canonical record stored with correct version, synthesis record stored, policy guard invoked, response returned without evaluative language.

**Step 28: Constraint compliance review**
Manually verify: no LLM calls beyond one, no hardcoded academic level keys in canonical output, all entries are collections, all agent modules are free of evaluation logic, policy config is externalized.

---

## Constraint Check

| Constraint | Status |
|---|---|
| **Deterministic-first preserved** | ✅ Agents 1–11 are all deterministic Python logic. LLM receives only assembled canonical output. pdfminer.six performs layout extraction without any LLM involvement. |
| **Single LLM call preserved** | ✅ `llm/client.py` exposes exactly one function making exactly one HTTP call. No retry, no chaining, no secondary calls. No orchestration framework used. |
| **No evaluation logic introduced** | ✅ No scoring, ranking, normalization, strength/weakness labeling, or admissions inference appears in any agent, model, schema, or configuration structure defined in this document. |
| **Collection-based canonical preserved** | ✅ `academic_entries`, `test_entries`, `essay_entries`, `activity_entries`, `timeline_entries` are all defined as arrays. No singular collapsed objects. |
| **No rigid key paths introduced** | ✅ No keys of the form `academics.class_12`, `tests.sat`, or `essays.career_statement` appear in any field definition. All entries use `entry_id` references and semantic collection labels. |
| **No infrastructure creep beyond Stage 0** | ✅ No Redis, no Celery, no object storage, no NGINX, no Kubernetes, no multi-service architecture, no cloud components appear anywhere in this document. |
| **No additional LLM frameworks introduced** | ✅ LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, and all other orchestration frameworks are absent. The sole LLM interaction is a direct httpx HTTP call in `llm/client.py`. |

---

*End of Stage 0 Finalization Document.*