# `env_config_spec.md`

**(Stage 1 — Structured MVP: Environment Configuration Specification)**

---

## 1. Configuration Philosophy

### Core Principle

All runtime configuration must be supplied exclusively through environment variables. No configuration value that varies between environments, that constitutes a secret, or that governs external service connectivity may be hardcoded anywhere in the application codebase.

Configuration loading occurs once at application startup. The application must not re-read or re-evaluate environment variables at request time. No runtime schema inference based on environment state is permitted. No logic branching driven by hidden global state is permitted.

### Configuration Domain Separation

Configuration is organized into five strictly separated domains. Each domain governs a distinct system concern. No domain may bleed into another at the variable definition level.

**Application Configuration** governs runtime behavior of the FastAPI application itself: environment identity and logging verbosity. These variables have no bearing on data processing logic.

**Database Configuration** governs connectivity to the PostgreSQL instance defined in `database_schema_v1.md`. These variables supply connection parameters only. They do not influence canonical model structure, pipeline behavior, or LLM interaction.

**LLM Configuration** governs the single controlled LLM synthesis call as defined in `llm_synthesis_contract.md`. These variables supply endpoint, model identity, and timeout parameters only. They do not govern how the canonical representation is constructed or how policy validation operates.

**Security Configuration** governs JWT-based authentication as defined in `architecture_lock.md` and `stage_0_implementation_spec.md`. These variables are secrets and must be treated as such. They have no bearing on pipeline logic or canonical structure.

**Logging Configuration** governs the verbosity and format of application log output. These variables do not introduce monitoring infrastructure, distributed tracing, or observability stacks.

These five domains are the complete and exhaustive configuration surface of Stage 1. No additional domain is permitted.

---

## 2. Required Environment Variables

### 2.1 Database Configuration

---

#### `DATABASE_URL`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Format | PostgreSQL DSN: `postgresql://{user}:{password}@{host}:{port}/{dbname}` |
| Description | Full connection string for the PostgreSQL 15+ instance. Must target the database containing the four tables defined in `database_schema_v1.md`. |
| Default | None. Application must not start if absent. |
| Secret | Yes. Contains database credentials. Must not be logged. Must not appear in application output. |
| Stage constraint | Must use synchronous `psycopg2` driver. Must not use `asyncpg` or any async-compatible DSN prefix. The DSN prefix must be `postgresql://` or `postgresql+psycopg2://`. DSN prefixes indicating async drivers (e.g., `postgresql+asyncpg://`) are prohibited at Stage 1. |

---

#### `DB_POOL_SIZE`

| Property | Definition |
|---|---|
| Required | No |
| Type | Integer |
| Accepted range | 1–20 |
| Default | `5` |
| Description | Number of persistent connections maintained in the SQLAlchemy connection pool. Controls concurrency baseline for synchronous database access. |
| Stage constraint | Must not be set to a value implying async worker concurrency. Stage 1 is synchronous. Pool size governs connection reuse, not parallelism. |

---

#### `DB_MAX_OVERFLOW`

| Property | Definition |
|---|---|
| Required | No |
| Type | Integer |
| Accepted range | 0–20 |
| Default | `10` |
| Description | Maximum number of connections that may be created above `DB_POOL_SIZE` when the pool is exhausted. Total maximum connections at any time is `DB_POOL_SIZE + DB_MAX_OVERFLOW`. |
| Stage constraint | No async overflow logic. Overflow connections are standard synchronous psycopg2 connections. |

---

### 2.2 Authentication Configuration

---

#### `JWT_SECRET`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Minimum length | 32 characters |
| Description | Secret key used to sign and verify JWT tokens. Must be a high-entropy, randomly generated string. Must never be a human-readable phrase, project name, or default placeholder. |
| Default | None. Application must not start if absent. |
| Secret | Yes. Must never be logged. Must never appear in any response body, error message, or stack trace. Must never be hardcoded in source code. |
| Stage constraint | No rotation mechanism. No key versioning. Single active secret. Key rotation is out of scope for Stage 1. |

---

#### `JWT_ALGORITHM`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Accepted values | `HS256`, `HS384`, `HS512` |
| Recommended value | `HS256` |
| Description | Algorithm used by `python-jose` to sign and verify JWT tokens. Must be a supported HMAC-based algorithm. Asymmetric algorithms (RS256, ES256) are not supported in Stage 1 as they require key-pair management infrastructure that is out of scope. |
| Default | None. Must be explicitly set. |
| Secret | No. Algorithm identifier is not sensitive. |

---

#### `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | Integer |
| Accepted range | 15–1440 |
| Description | Lifetime of an issued JWT access token in minutes. Tokens are validated against this value at request time. Expired tokens are rejected. |
| Default | None. Must be explicitly set. |
| Secret | No. |
| Stage constraint | No refresh token mechanism. No sliding expiry. Token expiry is fixed at issuance time. Refresh token configuration is explicitly prohibited by `architecture_lock.md`. |

---

### 2.3 LLM Configuration

---

#### `LLM_ENDPOINT`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Format | Full HTTPS URL of the LLM API endpoint (e.g., `https://api.anthropic.com/v1/messages`) |
| Description | The target URL to which the single synchronous LLM HTTP request is sent. This URL is consumed exclusively by `llm/client.py`. No other module may reference this variable. |
| Default | None. Application must not start if absent. |
| Secret | Partial. The URL itself may not be sensitive, but it must not be hardcoded. It is treated as configuration, not secret, unless it embeds an API key in the URL (which is prohibited — keys must travel as headers). |
| Stage constraint | Exactly one endpoint. No fallback URL. No load-balanced endpoint pool. No retry-with-alternate-endpoint logic. Single target, single call. |

---

#### `LLM_MODEL_NAME`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Description | Identifier of the model to be invoked at `LLM_ENDPOINT`. Passed as a parameter in the request body constructed by `llm/client.py`. Allows model version to be updated without code changes. |
| Default | None. Must be explicitly set. |
| Secret | No. |
| Stage constraint | Single model name. No model routing. No A/B model selection. No fallback model. The single LLM call contract defined in `llm_synthesis_contract.md` is not altered by this variable — it governs which model receives the single call. |

---

#### `LLM_API_KEY`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Description | API key credential for authenticating with the LLM provider at `LLM_ENDPOINT`. Must be transmitted as an HTTP header in the request made by `llm/client.py`. Must never be embedded in the URL. Must never be logged. |
| Default | None. Application must not start if absent. |
| Secret | Yes. Must be treated with the same discipline as `JWT_SECRET`. Must not appear in logs, error messages, response bodies, or stack traces. |
| Stage constraint | Single key. No key rotation. No multi-key pool. Key rotation is out of scope for Stage 1. |

---

#### `LLM_TIMEOUT_SECONDS`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | Integer |
| Accepted range | 10–300 |
| Description | Maximum number of seconds the synchronous `httpx` client will wait for a response from the LLM endpoint before raising a timeout error. On timeout, the pipeline treats the LLM call as a critical failure and propagates a structured error. No retry is attempted. |
| Default | None. Must be explicitly set. |
| Secret | No. |
| Stage constraint | Timeout applies to the single LLM call only. There is no retry on timeout. There is no fallback call. Failure is propagated as a pipeline error state and recorded in `applications.pipeline_status` as `'failed'`. |

---

### 2.4 File Storage Configuration

---

#### `UPLOAD_DIRECTORY`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Format | Absolute filesystem path to a writable local directory (e.g., `/app/uploads`) |
| Description | The directory into which uploaded PDF files are written before pipeline processing begins. The value stored in `applications.file_path` is derived from this directory path combined with a generated filename. |
| Default | None. Application must not start if absent. |
| Secret | No. |
| Stage constraint | Local filesystem only. No S3 path. No MinIO bucket. No UNC network path. No cloud storage URI. The directory must be accessible on the local filesystem of the running container or process. Object storage is explicitly prohibited in Stage 1 by `stage_1_scope_lock.md`. |

---

#### `MAX_UPLOAD_SIZE_MB`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | Integer |
| Accepted range | 1–50 |
| Description | Maximum permitted size in megabytes for an uploaded PDF file. Requests that exceed this limit must be rejected at the API layer before any file is written to disk or pipeline processing begins. |
| Default | None. Must be explicitly set. |
| Secret | No. |
| Stage constraint | Enforced synchronously at upload time. No streaming size check against object storage. Local disk write is gated by this value. |

---

### 2.5 Application Configuration

---

#### `APP_ENV`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Accepted values | `development`, `production` |
| Description | Identifies the runtime environment context. Used exclusively for adjusting logging verbosity and debug output behavior. Must not influence pipeline logic, canonical model construction, LLM behavior, or database schema. |
| Default | None. Must be explicitly set. |
| Secret | No. |
| Stage constraint | Only two accepted values. `development` permits more verbose output. `production` suppresses debug output. No cloud-specific branching. No Kubernetes-specific branching. No multi-tenant branching. No additional environment values (e.g., `staging`, `qa`) are defined in Stage 1. |

---

#### `LOG_LEVEL`

| Property | Definition |
|---|---|
| Required | Yes |
| Type | String |
| Accepted values | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| Description | Controls the minimum severity level of log messages emitted by the application. All messages below this threshold are suppressed. |
| Default | None. Must be explicitly set. Recommended default in `development`: `DEBUG`. Recommended default in `production` container: `INFO`. |
| Secret | No. |
| Stage constraint | Controls stdout log verbosity only. Does not configure a log aggregation service, distributed tracing system, or monitoring stack. Log output goes to stdout/stderr only. |

---

## 3. Variable Validation Discipline

### Startup-Time Validation Requirement

All environment variable validation must occur at application startup, before the FastAPI application begins accepting requests. The validation routine in `config.py` must execute as part of the application initialization sequence, prior to database connection establishment, route registration, or any agent module initialization.

Validation must not be deferred to first use. No variable may be read lazily at request time without prior startup validation.

### Required vs Optional Distinction

| Classification | Behavior if Absent |
|---|---|
| Required | Application must refuse to start. A clear, descriptive error message must be emitted to stderr identifying the missing variable by name. The process must exit with a non-zero exit code. |
| Optional | Application may start. The documented default value is applied. The applied default must be logged at startup at `INFO` level so that the runtime configuration is visible in logs. |

The following variables are **Required** (application must not start if absent):

`DATABASE_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `LLM_ENDPOINT`, `LLM_MODEL_NAME`, `LLM_API_KEY`, `LLM_TIMEOUT_SECONDS`, `UPLOAD_DIRECTORY`, `MAX_UPLOAD_SIZE_MB`, `APP_ENV`, `LOG_LEVEL`

The following variables are **Optional** (defaults apply if absent):

`DB_POOL_SIZE` (default: `5`), `DB_MAX_OVERFLOW` (default: `10`)

### Type Enforcement Rules

| Variable | Expected Type | Validation Rule |
|---|---|---|
| `DATABASE_URL` | String | Must begin with `postgresql://` or `postgresql+psycopg2://`. Must not begin with `postgresql+asyncpg://` or any async driver prefix. |
| `DB_POOL_SIZE` | Integer | Must be parseable as a positive integer. Must be within the range 1–20 inclusive. |
| `DB_MAX_OVERFLOW` | Integer | Must be parseable as a non-negative integer. Must be within the range 0–20 inclusive. |
| `JWT_SECRET` | String | Must have a minimum length of 32 characters. Must not equal a known placeholder value (e.g., `"secret"`, `"changeme"`, `"your_secret_here"`). |
| `JWT_ALGORITHM` | String | Must be one of the accepted values: `HS256`, `HS384`, `HS512`. Case-sensitive. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | Must be parseable as a positive integer. Must be within the range 15–1440 inclusive. |
| `LLM_ENDPOINT` | String | Must be a valid URL beginning with `https://`. Must not be empty. |
| `LLM_MODEL_NAME` | String | Must be a non-empty string. No format constraint beyond non-empty. |
| `LLM_API_KEY` | String | Must be a non-empty string. Minimum length of 8 characters. Must not be logged during validation. |
| `LLM_TIMEOUT_SECONDS` | Integer | Must be parseable as a positive integer. Must be within the range 10–300 inclusive. |
| `UPLOAD_DIRECTORY` | String | Must be a non-empty string representing an absolute path. Must be confirmed writable at startup via a filesystem check. If the directory does not exist, the application must attempt to create it. If creation fails, the application must not start. |
| `MAX_UPLOAD_SIZE_MB` | Integer | Must be parseable as a positive integer. Must be within the range 1–50 inclusive. |
| `APP_ENV` | String | Must be one of the accepted values: `development`, `production`. Case-insensitive at read time; normalized to lowercase after validation. |
| `LOG_LEVEL` | String | Must be one of the accepted values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Case-insensitive at read time; normalized to uppercase after validation. |

### Failure Behavior

If any required variable is absent or fails type validation, the application must:

1. Emit a descriptive error message to stderr naming the specific variable and the reason for failure.
2. Not suppress or catch the failure silently.
3. Terminate the process with a non-zero exit code before accepting any network connections.

Partial startup — where the application begins accepting requests before configuration is confirmed valid — is prohibited.

### No Runtime Dynamic Fallback

The application must not implement dynamic fallback logic that silently substitutes alternative configuration values if a variable is unset or invalid. All fallbacks must be static, documented defaults applied only for explicitly optional variables. No environment variable may be derived from another at runtime.

---

## 4. Secret Handling Discipline

### Variables Classified as Secrets

The following variables contain sensitive material and must be treated as secrets throughout the application lifecycle:

- `JWT_SECRET`
- `LLM_API_KEY`
- `DATABASE_URL` (contains database credentials)

### Prohibition on Hardcoding

No secret variable may appear as a literal string in any source file, configuration template, test fixture, or documentation example with a real value. Placeholder indicators (e.g., `<your-jwt-secret>`) are acceptable in documentation. Actual values are never acceptable in source code.

### `.env` File Usage in Stage 1

The use of a `.env` file loaded by `python-dotenv` at startup is permitted and is the defined mechanism for supplying environment variables in both local development and containerized deployment at Stage 1. The `.env` file must be:

- Listed in `.gitignore` and never committed to version control.
- Provided as a `.env.example` file with placeholder values for developer onboarding.
- Treated as equivalent to a secret store for the purposes of Stage 1 discipline.

In the Docker container context, environment variables may be supplied via the `docker-compose.yml` `environment` block or via a `.env` file mounted into the container. Both are acceptable at Stage 1.

### No Secret Manager Integration

No integration with external secret management services is permitted in Stage 1. This includes but is not limited to: HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Doppler, and any equivalent SaaS or self-hosted secret store. Secret manager integration is a Stage 5 concern at the earliest.

### No Key Rotation Automation

No automated key rotation mechanism for `JWT_SECRET` or `LLM_API_KEY` is implemented in Stage 1. Key rotation requires manual update of the `.env` file or container environment and a service restart. This is acceptable at Stage 1 volume and threat model.

### Log Suppression Requirement

During startup validation, during request processing, and during error handling, the application must never emit the value of any secret variable to any log output, stdout, stderr, error response body, or stack trace. Validation code that reads secret variables must not log the variable value — only the variable name and a pass/fail outcome.

---

## 5. Logging Configuration Discipline

### Log Level Control

Log verbosity is governed exclusively by the `LOG_LEVEL` environment variable defined in Section 2.5. The application's root logger must be configured at startup using this value. All application modules must derive their log level from the root logger configuration. No module may hardcode its own log level override.

### Recommended Log Level by Environment

| `APP_ENV` Value | Recommended `LOG_LEVEL` | Rationale |
|---|---|---|
| `development` | `DEBUG` | Full visibility into agent execution, canonical assembly, and pipeline progression during local development. |
| `production` | `INFO` | Operational events are captured without debug verbosity. Debug output is suppressed in the production container. |

### Events That Must Be Logged

The following events must be logged at the specified level regardless of `LOG_LEVEL` configuration (i.e., they are emitted at a level that will always appear given the recommended settings):

| Event | Log Level |
|---|---|
| Application startup with configuration summary (secrets suppressed) | `INFO` |
| Application startup validation failure | `ERROR` |
| Application upload received (application_id, file size) | `INFO` |
| Pipeline execution started (application_id) | `INFO` |
| Each agent invocation (agent_id, agent_name) | `DEBUG` |
| Each agent completion with confidence score | `DEBUG` |
| Canonical assembly completed (canonical_version, application_id) | `INFO` |
| LLM invocation started (application_id, model_name — no prompt content) | `INFO` |
| LLM invocation completed (application_id, response received) | `INFO` |
| LLM invocation timeout or failure (application_id, error type) | `ERROR` |
| Policy validation started (application_id) | `DEBUG` |
| Policy validation result (application_id, policy_passed, violation count if any) | `INFO` |
| Pipeline completion (application_id, final status) | `INFO` |
| Pipeline failure (application_id, failure reason) | `ERROR` |

### Events That Must Never Be Logged

The following must never appear in any log output:

- JWT secret value
- LLM API key value
- Database password (extracted from DATABASE_URL)
- Raw PDF content or text blocks
- Full canonical representation document (may generate excessively large log lines; agent-level confidence scores are sufficient)
- Full LLM prompt content (contains canonical data; must not be logged to avoid sensitive data exposure in logs)
- Full LLM response content

### Structured vs Plain Logging Policy

At Stage 1, plain text logging to stdout is acceptable and is the defined approach. Log lines must be human-readable and include at minimum: timestamp, log level, module name, and message.

Structured JSON logging is not mandated in Stage 1 but is not prohibited if the implementation team chooses to adopt it using the Python standard `logging` module's `JsonFormatter` or equivalent. If structured logging is adopted, the same secret suppression rules apply.

Distributed tracing, trace ID propagation, span-based instrumentation, and monitoring stack integration are explicitly prohibited in Stage 1. Log output is to stdout/stderr only.

### No Monitoring Stack

No integration with Prometheus, Grafana, Datadog, New Relic, OpenTelemetry, or any equivalent monitoring or observability system is introduced in Stage 1. These are explicitly out of scope per `stage_1_scope_lock.md`.

---

## 6. Environment Isolation Strategy

### Two Permitted Environments

Stage 1 defines exactly two runtime environments:

**Local Development (`APP_ENV=development`):** The application runs as a plain Python process on the developer's machine, loading configuration from a local `.env` file via `python-dotenv`. PostgreSQL runs locally (either natively installed or via the Docker Compose database container). PDF uploads are stored in a local directory path. Log level is typically `DEBUG`.

**Production Container (`APP_ENV=production`):** The application runs inside a Docker container as defined by Stage 1's containerization scope. Environment variables are supplied via Docker Compose's `environment` block or an `.env` file mounted into the container. PostgreSQL runs in a separate container within the same Docker Compose network. PDF uploads are stored in a directory path accessible within the container's filesystem. Log level is typically `INFO`.

### No Stage-Specific Branching in Code

The `APP_ENV` variable must not be used to drive branching logic within pipeline agents, canonical assembly, LLM invocation, policy guard, or database access code. Its permitted uses are:

- Adjusting log verbosity (in combination with `LOG_LEVEL`).
- Suppressing debug output in production.
- Adjusting FastAPI's auto-generated API documentation visibility (e.g., disabling `/docs` and `/redoc` in `production` if desired).

No pipeline behavior, no canonical structure, no LLM contract, and no database schema may differ between `development` and `production`. The logical system is identical across both environments.

### No Cloud-Specific Branching

No configuration variable or code path may introduce cloud-provider-specific behavior at Stage 1. There is no AWS mode, no GCP mode, no Azure mode. The system runs on local infrastructure only. Cloud-ready deployment is a Stage 6 concern.

### No Additional Environments

No `staging`, `qa`, `test`, `ci`, or other environment identifiers are defined in Stage 1. The two permitted values of `APP_ENV` are exhaustive. If a CI/CD pipeline requires running the application, it must use `development` as the environment identifier. Environment multiplication is not permitted at this stage.

### `.env.example` Discipline

A `.env.example` file must be maintained in the repository root. It must:

- List every environment variable defined in this document.
- Supply placeholder values for all secrets (e.g., `JWT_SECRET=<generate-a-random-32-char-string>`).
- Supply representative non-secret values for all non-secret variables.
- Be kept in sync with this specification document as the authoritative variable list.
- Never contain real secrets or real credentials.

---

## 7. What Is Explicitly Not Included

The following configuration categories are confirmed absent from Stage 1. Their absence is intentional and required by the governing specification documents.

| Category | Specific Exclusion | Governing Document |
|---|---|---|
| Redis configuration | No `REDIS_URL`, no `REDIS_HOST`, no `REDIS_PORT`, no cache TTL variables | `stage_1_scope_lock.md` |
| Queue configuration | No `CELERY_BROKER_URL`, no `RQ_REDIS_URL`, no `KAFKA_BOOTSTRAP_SERVERS`, no job queue variables | `stage_1_scope_lock.md` |
| Object storage configuration | No `AWS_S3_BUCKET`, no `MINIO_ENDPOINT`, no `MINIO_ACCESS_KEY`, no `GCS_BUCKET`, no object storage URI variables | `stage_1_scope_lock.md` |
| Audit logging configuration | No `AUDIT_LOG_DESTINATION`, no `AUDIT_LOG_LEVEL`, no event log targets | `stage_1_scope_lock.md` |
| Multi-tenant configuration | No `TENANT_ID`, no `INSTITUTION_ID`, no `ORG_SLUG`, no tenant routing variables | `stage_1_scope_lock.md` |
| OAuth and third-party auth | No `OAUTH_CLIENT_ID`, no `OAUTH_CLIENT_SECRET`, no `AUTH0_DOMAIN`, no SSO variables | `architecture_lock.md` |
| Refresh token configuration | No `JWT_REFRESH_SECRET`, no `REFRESH_TOKEN_EXPIRE_DAYS`, no token rotation variables | `architecture_lock.md` |
| HTTPS configuration | No `SSL_CERT_PATH`, no `SSL_KEY_PATH`, no TLS termination variables | `stage_1_scope_lock.md` |
| Kubernetes configuration | No `K8S_NAMESPACE`, no `K8S_SERVICE_ACCOUNT`, no pod identity variables | `stage_1_scope_lock.md` |
| NGINX configuration | No reverse proxy variables, no upstream configuration variables | `stage_1_scope_lock.md` |
| Monitoring and observability | No `PROMETHEUS_PORT`, no `DATADOG_API_KEY`, no `OTEL_EXPORTER_ENDPOINT`, no tracing variables | `stage_1_scope_lock.md` |
| Cloud provider configuration | No `AWS_ACCESS_KEY_ID`, no `GCP_PROJECT_ID`, no `AZURE_SUBSCRIPTION_ID`, no cloud identity variables | `stage_1_scope_lock.md` |
| Secret manager integration | No `VAULT_ADDR`, no `AWS_SECRETS_MANAGER_REGION`, no secret store connection variables | `architecture_lock.md` |
| Worker process configuration | No `WORKER_CONCURRENCY`, no `WORKER_QUEUE_NAME`, no background task variables | `stage_1_scope_lock.md` |
| Async database configuration | No `ASYNC_DATABASE_URL`, no `ASYNCPG_DSN`, no async driver variables | `stage_1_scope_lock.md` |

---

## 8. Stage 1 Completion Criteria (Configuration-Level)

The Stage 1 configuration is considered compliant when all of the following conditions are true:

### Variable Completeness

- All twelve required environment variables defined in Section 2 are present and validated at startup.
- Both optional variables (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`) have documented defaults that are applied when absent.
- No environment variable exists in the codebase that is not defined in this specification document.

### Validation Implementation

- `config.py` performs all validation at startup before the application accepts requests.
- All type enforcement rules defined in Section 3 are implemented.
- Missing required variables cause a non-zero exit before any network binding occurs.
- No variable is read lazily at request time without prior startup validation.

### Secret Discipline

- `JWT_SECRET` and `LLM_API_KEY` are never present in any committed source file with real values.
- `DATABASE_URL` is never hardcoded with real credentials.
- A `.env.example` file exists with placeholder values for all variables.
- `.env` is listed in `.gitignore`.
- No secret value appears in any log output at any log level.

### Logging Compliance

- `LOG_LEVEL` is loaded from environment and applied to the root logger at startup.
- All events listed in Section 5 as required to be logged are emitted at the correct level.
- No secret values appear in log output.
- No monitoring stack integration exists.
- Log output goes to stdout/stderr only.

### Environment Isolation Compliance

- `APP_ENV` accepts only `development` or `production`.
- No pipeline logic, canonical structure, or LLM behavior differs between the two environments.
- No cloud-specific, Kubernetes-specific, or multi-tenant configuration exists.
- No additional environment identifiers beyond the two defined values are in use.

### Prohibited Configuration Absent

- Every category listed in Section 7 as explicitly not included is confirmed absent from the codebase, `.env.example`, and any configuration module.
- No prohibited variable name appears in any source file, configuration file, or documentation.

### DATABASE_URL Compliance

- The `DATABASE_URL` value in use specifies a synchronous PostgreSQL driver (`postgresql://` or `postgresql+psycopg2://`).
- No async driver prefix is present in any environment.

### LLM Configuration Compliance

- `LLM_ENDPOINT`, `LLM_MODEL_NAME`, and `LLM_API_KEY` configure exactly one LLM call target.
- No fallback endpoint, alternate model, or secondary key is configured.
- `LLM_TIMEOUT_SECONDS` is applied to the single `httpx` synchronous call in `llm/client.py` and nowhere else.

---

## Constraint Check

| Constraint | Status | Evidence |
|---|---|---|
| **Deterministic-first preserved** | ✅ | No environment variable governs, enables, or influences LLM involvement in extraction. The LLM configuration variables (`LLM_ENDPOINT`, `LLM_MODEL_NAME`, `LLM_API_KEY`, `LLM_TIMEOUT_SECONDS`) govern only the single synthesis call in `llm/client.py`. No variable introduces LLM participation in Agents 1–11. |
| **Single LLM call preserved** | ✅ | `LLM_ENDPOINT` defines a single endpoint. `LLM_MODEL_NAME` defines a single model. `LLM_TIMEOUT_SECONDS` applies to a single call. No retry variable, no fallback endpoint variable, no secondary model variable, and no chaining variable is defined. The configuration surface permits exactly one LLM call per application. |
| **No evaluation logic introduced** | ✅ | No variable governs scoring, ranking, normalization, strength/weakness labeling, concern detection, or predictive modeling. Configuration variables influence connectivity, identity, and verbosity only. No variable introduces evaluative behavior into any pipeline component. |
| **Collection-based canonical preserved** | ✅ | No environment variable governs canonical structure. `canonical_model_philosophy.md` is not influenced by any configuration value defined here. The canonical representation remains collection-based regardless of environment configuration. |
| **No rigid key paths introduced** | ✅ | No variable encodes or references academic-level keys, test name keys, or essay identifier keys. No configuration value introduces fixed structural assumptions into the canonical model or the LLM prompt. |
| **No async configuration introduced** | ✅ | No Redis URL, no Celery broker, no async database driver, no background worker configuration, no queue variable, and no job polling variable is defined. The synchronous `psycopg2` driver is explicitly required. Async driver DSN prefixes are explicitly prohibited. |
| **No infrastructure creep beyond Stage 1** | ✅ | No S3, MinIO, NGINX, Kubernetes, cloud provider, monitoring stack, secret manager, or distributed tracing variable is defined. Section 7 explicitly confirms and names every prohibited configuration category. The configuration surface is bounded to the four containers (API, PostgreSQL) and local filesystem defined by Stage 1 scope. |
| **No service separation introduced** | ✅ | No inter-service communication variable, no service discovery variable, no routing key variable, and no service mesh configuration variable is defined. All configuration targets a single FastAPI application process communicating with a single PostgreSQL instance. |
| **No additional LLM frameworks introduced** | ✅ | No LangChain, LangGraph, AutoGen, CrewAI, Semantic Kernel, or equivalent framework configuration variable is defined. No variable introduces orchestration, tool-calling, reflection, or multi-step reasoning configuration. The sole LLM interaction surface is the single `httpx` call governed by the four LLM variables defined in Section 2.3. |

---

*End of `env_config_spec.md`.*

*Configuration Specification Version: 1.0 | Stage: 1 — Structured MVP | Governing Architecture Version: architecture_lock.md*
