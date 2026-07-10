# AG Interview Standardiser - System And Product Documentation

Generated: 2026-07-10

This document describes the AG Interview Standardiser product and its technical architecture. It focuses on what the system does, how the major subsystems fit together, which technologies and production patterns are used, and what limitations remain. It intentionally avoids internal file-by-file inventory and low-level implementation trivia.

## 1. Product Overview

AG Interview Standardiser is a full-stack AI workflow product for admissions interview standardization. It is designed for an institutional review process where administrators upload applicant PDFs, the system extracts and structures the application, and interviewers receive standardized focus areas, question sets, and preparation tools.

The product is currently centered on a B2B institutional workflow. A D2C/Common App direction was considered, but the active engineering direction has been to first stabilize and mature the core platform before expanding into consumer scenarios.

At a product level, the system supports:

- Application PDF upload and storage.
- Automated parsing of admissions-style PDFs.
- Canonical applicant-record creation.
- Admin review and assignment workflows.
- AI-generated structured review packages.
- AI-generated interviewer focus areas.
- AI-generated interviewer question sets.
- Final report generation and export.
- Interviewer-specific workspace state.
- Report/application copilot chat.
- Interview note refinement.
- Question regeneration.
- Theme and question-version feedback.
- Ratings-driven retrieval to improve future question generation.

The core idea is that the system does not simply ask an LLM to summarize a PDF. It turns uploaded applications into structured, reviewable, versioned, and auditable product artifacts that support a real admin/interviewer workflow.

## 2. User Roles And Product Workflow

### Admin Workflow

Admins manage the institutional side of the product. They can upload applications, view application status, assign applications to interviewers, generate reports, inspect final artifacts, manage interviewer users, and use the report copilot against application/report context.

Admin responsibilities in the product include:

- Bringing source applications into the system.
- Monitoring processing and report status.
- Assigning the right interviewer to the right application.
- Generating and reviewing final interview-preparation artifacts.
- Managing visibility and application lifecycle state.
- Monitoring capacity for expensive AI operations.

### Interviewer Workflow

Interviewers work with assigned applications only. They see generated focus areas and question sets, create workspace notes, refine interview text, rate generated material, regenerate weak questions, activate preferred question versions, and complete interview-preparation workflows.

Interviewer responsibilities in the product include:

- Reviewing a structured application summary.
- Understanding the generated focus areas.
- Preparing from generated question sets.
- Improving or regenerating questions where needed.
- Capturing interview workspace state.
- Providing ratings that feed future question quality.

### End-To-End Lifecycle

The product lifecycle is:

1. An admin uploads an application PDF.
2. The PDF is stored as a source artifact.
3. A durable processing job is created.
4. A background worker processes the PDF asynchronously.
5. The system extracts structured applicant data.
6. A canonical applicant record is stored.
7. The system creates the initial review package.
8. The system generates final interviewer-facing artifacts.
9. An interviewer receives the assignment.
10. The interviewer reviews focus areas and question sets.
11. The interviewer can rate, regenerate, or activate question versions.
12. Ratings and generated-question history feed the retrieval corpus.
13. Future question generation can use the retrieval layer as quality guidance.

## 3. High-Level Architecture

The system is organized into clear architectural layers:

- Frontend product surface: role-specific admin and interviewer interfaces built with Next.js, React, TypeScript, and Tailwind-style UI patterns.
- API layer: FastAPI routes for admin, interviewer, application, report, auth, and user workflows.
- Domain layer: product logic for processing, report chat, question feedback, question regeneration, assignments, storage, and workspace state.
- Document-intelligence pipeline: deterministic PDF extraction, canonicalization, signal detection, LLM synthesis, validation, report assembly, and annotation generation.
- Persistence layer: PostgreSQL stores users, applications, assignments, canonical records, final reports, workspaces, processing jobs, generated questions, ratings, and audit snapshots.
- Async execution layer: Celery and Redis handle long-running processing and indexing work outside the request-response path.
- Object storage layer: MinIO/local storage abstraction stores PDFs and exported report artifacts.
- Retrieval layer: Qdrant and FastEmbed provide semantic retrieval over generated questions and rating metadata.
- Security layer: authentication, role and assignment authorization, CSRF, CORS, trusted hosts, security headers, upload validation, and rate limiting.
- Observability layer: request IDs, structured logs, OpenTelemetry metrics/spans, and Langfuse traces for AI/RAG boundaries.

The central architectural principle is separation of responsibility:

- PostgreSQL is the source of truth for product state.
- Redis/Celery handles task delivery and worker execution.
- Qdrant is a derived semantic index that can be rebuilt.
- Object storage owns binary source/export artifacts.
- Observability providers are optional and must not break product flow.

This gives the system a production-style shape: durable state in the database, expensive work offloaded to workers, derived AI/retrieval indexes kept rebuildable, and product artifacts persisted for auditability.

## 4. Technology Stack

Backend technologies:

- Python 3.11
- FastAPI for the API layer
- SQLAlchemy for ORM/database access
- Alembic for schema migrations
- PostgreSQL for durable product state
- Redis for queues, coordination, and rate limiting
- Celery for background jobs
- Qdrant for vector search
- FastEmbed for local embeddings
- MinIO-compatible object storage for source PDFs and exported artifacts
- HTTPX for LLM provider calls
- OpenTelemetry for operational telemetry
- Langfuse for AI/RAG trace observability

Frontend technologies:

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Base UI / shadcn-style component patterns
- Motion/animation tooling

Infrastructure and tooling:

- Docker Compose for local backend infrastructure
- GitHub Actions for CI
- Pytest for backend regression coverage
- Alembic migrations in CI
- Optional self-hosted Langfuse stack
- Graphify knowledge graph for codebase navigation

## 5. Data Model And Product State

The product state is modeled around the lifecycle of an application and the artifacts generated from it.

### Identity And Access

The system stores users with role, access status, password/auth metadata, and identity-provider metadata. Roles distinguish admins from interviewers, while assignment records enforce which interviewer can access which application.

This gives the app more than coarse role-based access control. Interviewer permissions depend on both role and assignment, which matters for institutional data privacy.

### Application State

An application record represents an uploaded applicant file and tracks its lifecycle. It links to the source PDF in object storage, stores status, supports display identifiers, and tracks activity/visibility state.

Application state connects the entire product: upload, processing job, canonical record, assignment, final report, workspace, generated questions, ratings, and export artifacts.

### Canonical Applicant Record

The canonical record is the stable structured representation of the uploaded PDF. It separates raw document ingestion from downstream AI/report workflows.

It stores normalized applicant data, deterministic signals, and the structured review package used by later report and interviewer flows.

This is one of the most important design decisions in the product. The system does not rely on repeatedly prompting over a raw PDF. It first creates a structured data layer, then uses that layer to drive AI synthesis and reporting.

### Final Report

The final report stores the generated interview-preparation artifact. It is versioned at the report-schema level, stored as structured content, and can be exported as an object-storage-backed artifact.

This means the final output is not just transient LLM text. It is a durable product artifact with versioning and download/export support.

### Interview Workspace

The interview workspace stores interviewer-specific preparation state. It tracks draft/launched/completed lifecycle and keeps interviewer notes or preparation content separate from generated report content.

This separation matters because generated AI artifacts, interviewer edits, and workflow completion state have different ownership and lifecycle rules.

### Processing Jobs

Processing jobs represent long-running backend work. They store job type, status, attempts, progress, queue metadata, task identity, error codes, last error, retry availability, and timestamps.

This job ledger makes background execution visible and recoverable. The product can tell whether processing is queued, running, completed, failed, retried, or stale.

### Generated Questions And Versions

Generated interview questions are stored as stable threads with versioned outputs. A regenerated question does not overwrite the original. It creates a new version, links back to its parent, stores generation context, and becomes active only when selected.

This allows the product to preserve history, compare versions, switch active versions, and audit why a question changed.

### Ratings And Feedback

The system captures ratings for generated focus areas and question versions. These ratings are not only UI feedback; they feed the retrieval layer so future generation can learn from historically useful questions.

This creates a human-in-the-loop quality loop:

- AI generates interview material.
- Humans rate what is useful.
- Rated outputs are indexed.
- Future generation retrieves high-quality examples.
- Regeneration becomes guided by product feedback.

### Vector Corpus

The system includes both a legacy lexical corpus and a newer Qdrant-backed semantic index. The semantic index is treated as derived infrastructure rather than canonical product state.

This means the vector layer can be rebuilt from Postgres if needed.

## 6. PDF Processing And Document Intelligence

The PDF pipeline is staged and hybrid. It combines deterministic parsing with LLM synthesis instead of sending the raw PDF directly to a model and trusting the result.

The deterministic stages include:

- Layout extraction from PDF text and geometry.
- Page/block/row representation.
- Section detection.
- Section scope resolution.
- Personal information extraction.
- Family background extraction.
- Geographic context extraction.
- Academic record extraction.
- Standardized test extraction.
- Essay extraction.
- Activity extraction.
- Additional information extraction.
- Cross-section consistency detection.
- Integrity analysis.
- Canonical assembly.

The AI and derived-analysis stages include:

- Deterministic signal detection.
- Projection building for LLM-readable structured context.
- Essay fragment construction.
- LLM-based signal interpretation.
- Focus-area bundle construction.
- Interview focus-area synthesis.
- Question bundle construction.
- Retrieval of question-quality examples.
- Interview question generation.
- Policy validation.
- Final report assembly.
- Report annotation generation.

The important design pattern is that every major stage has a defined role:

- Deterministic stages extract and normalize evidence.
- LLM stages interpret, synthesize, and phrase interviewer-facing output.
- Validation stages constrain the LLM output.
- Assembly stages turn structured pieces into product artifacts.

This makes the pipeline more reliable and explainable than a single monolithic prompt.

## 7. Review Package And Report Generation

The system produces structured review artifacts rather than only free-form summaries.

The early review package contains normalized applicant information and evidence-rich structured data. The final report builds on this with interviewer-facing focus areas, question groups, signal data, and annotations.

Report-generation characteristics:

- Report content is stored structurally.
- The report schema is versioned.
- Final artifacts can be exported.
- Report annotations connect generated content back to underlying evidence.
- Seeded final report data supports consistent frontend development and visual verification.

The report system is designed for repeatability and reviewability. It produces a durable artifact that can be rendered, exported, discussed, and inspected later.

## 8. LLM Architecture

The application has a centralized LLM gateway rather than scattered direct provider calls.

The LLM layer supports:

- OpenAI-compatible endpoints.
- AICredits-style provider routing.
- Operation-specific model policies.
- Separate configuration for generation, report chat, interview refinement, and question regeneration.
- Primary and fallback models.
- Per-operation concurrency limits.
- Per-operation retry and backoff settings.
- Max-token controls.
- Temperature and structured-output controls.
- Live-call disabling for CI/tests.

Reliability behavior includes:

- Empty input validation.
- Timeout handling.
- Transport error handling.
- Provider error handling.
- Budget exhaustion handling.
- Rate-limit handling.
- Upstream 5xx handling.
- Invalid JSON handling.
- Unsupported structured-output fallback behavior.
- Retryable error classification.
- Jittered exponential backoff.
- Fallback model switching.

The LLM layer also emits operational data:

- Estimated prompt tokens.
- Estimated response tokens.
- Latency.
- Model and provider metadata.
- Operation name.
- Status and retry counts.

This layer is important because it turns LLM usage from ad hoc calls into managed infrastructure. Different product features can have different cost, latency, concurrency, and reliability policies.

## 9. Prompting And Validation Design

The system uses multiple prompt families, each tied to a specific stage of the product workflow.

Prompt families include:

- Signal interpretation.
- Focus-area synthesis.
- Interview question generation.
- Question regeneration.
- Report chat.
- Interview note refinement.

The system applies validation after LLM generation. This is a key production pattern because the app does not trust model output solely because it matches the prompt.

Validation and recovery patterns include:

- Schema-aware output checks.
- Policy guards for focus areas and question groups.
- Signal validation.
- Sanitization of LLM output.
- Malformed JSON recovery.
- Retry modes for report-chat output failures.
- Scope guard responses for out-of-bounds report-chat questions.
- Degraded fallback responses when the LLM is unavailable.

This makes the AI behavior constrained by product rules rather than being an unrestricted generative layer.

## 10. Report Chat / Copilot

The report chat system is a grounded copilot for asking questions about an application or report.

It is not an open-ended chatbot. It builds context from the structured review package, final report content, current workspace state, current page/surface, workflow stage, and available actions.

Report chat capabilities include:

- Question validation by length and word count.
- Intent and target detection.
- Context routing by report/application area.
- Source construction for referenced sections.
- JSON response parsing and validation.
- Partial-output recovery.
- Retry modes for malformed responses.
- Workflow-aware fallback answers.
- Default follow-up suggestions.
- Detection of disallowed evaluative/judgment requests.
- Structural leak detection to prevent implementation/schema language from surfacing.

The design goal is to keep the copilot grounded in the report workflow and prevent it from becoming an uncontrolled admissions evaluator.

## 11. Interview Workspace

The interview workspace gives interviewers a stateful preparation area tied to an assigned application.

It supports:

- Draft preparation state.
- Launched state.
- Completed state.
- Interviewer-specific content.
- Integration with final report context.
- Integration with report chat.
- Interview note refinement.

The workspace model separates human working state from generated report artifacts. This is important because generated material, interviewer notes, and workflow completion have different lifecycle semantics.

## 12. Question Generation, Regeneration, And Feedback

The generated question system has several important concepts:

- Stable question threads.
- Versioned question outputs.
- Active question version.
- Parent-child version history.
- Generation source tracking.
- Human ratings.
- Application context snapshots.
- Retrieval context snapshots.
- Vector indexing after generation/regeneration.

Regeneration creates a new question version instead of mutating the old one. This preserves history and allows the product to explain how the question changed.

The feedback system creates a quality loop:

1. The system generates questions.
2. Users rate question versions.
3. Ratings are stored with product context.
4. Question versions are indexed for retrieval.
5. Future generation/regeneration retrieves useful historical examples.
6. Retrieval context is stored with the new version.

This is one of the strongest AI-product patterns in the system because it connects user feedback to future model behavior without requiring model fine-tuning.

## 13. Async Processing Architecture

Long-running work is handled through a Celery and Redis task architecture with Postgres-backed job state.

The async layer is used for:

- PDF processing.
- Deterministic pipeline execution.
- Question vector indexing.
- Vector backfills.
- Maintenance-style background work.

The job system supports:

- Queued/running/completed/failed states.
- Attempt counting.
- Progress tracking.
- Task identity tracking.
- Queue name tracking.
- Retry availability timestamps.
- Error code and last-error storage.
- Permanent failure handling.
- Stale running-job recovery.
- Idempotency guards to prevent duplicate active jobs.
- Locks around claim and execution boundaries.

The important architecture choice is that Celery does not own product truth. Celery executes work; Postgres records the state users and admins care about.

This design improves:

- API responsiveness.
- Reliability of long-running PDF/AI jobs.
- Operator visibility.
- Recovery after worker crashes.
- Future scalability through queue separation.

## 14. Redis Usage

Redis serves several roles:

- Celery broker/result backend.
- Rate-limiting backend.
- Distributed coordination and locking.

The app includes fallbacks for local/test resilience, but production should prefer Redis-backed behavior because in-memory fallback is weaker in multi-process environments.

The Redis usage shows a pragmatic architecture: Redis is used for coordination and execution infrastructure, while Postgres remains authoritative for product data.

## 15. Qdrant RAG System

The vector retrieval system uses Qdrant and FastEmbed to improve generated interview questions.

The corpus is built from generated question versions and associated product metadata:

- Question text.
- Theme/focus-area context.
- Question role.
- Rationale.
- Generation source.
- Rating average/count.
- Application and thread context.

Retrieval behavior:

- Builds a semantic query from the current focus area, theme, direction, question role, and question text.
- Searches Qdrant for semantically similar generated questions.
- Excludes the current application.
- Prefers examples from matching focus areas.
- Prefers examples with matching question roles.
- Uses rating metadata during reranking.
- Returns compact examples to guide generation.
- Stores retrieval provider, strategy, selected examples, scores, and fallback reasons.

Fallback behavior:

- If Qdrant is disabled, unavailable, empty, or errors, the app records the reason and falls back gracefully.
- The product remains functional even when retrieval is not available.

The retrieval layer is used as guidance, not as a hard source of truth. It helps the LLM understand what strong questions look like without copying examples directly.

## 16. Embeddings

The RAG layer uses local embeddings through FastEmbed. The default model is a small BGE embedding model, which keeps the system free from an additional paid embedding provider.

Embedding-related configuration controls:

- Model name.
- Embedding dimension.
- Candidate retrieval limit.
- Final retrieval limit.
- Qdrant timeout.
- Qdrant collection.

The embedding model and retrieval strategy are recorded in snapshots so retrieval behavior can be debugged later.

## 17. Storage And Asset Handling

The system abstracts storage behind local and MinIO-compatible backends.

Stored assets include:

- Source application PDFs.
- Final report exports.
- Profile/image assets where applicable.

Storage behavior includes:

- Uploading files.
- Streaming downloads.
- Checking object existence.
- Deleting objects.
- Materializing stored files to temporary local files for processing.
- Preserving content type and export metadata.

This makes the product closer to a production file-handling architecture than a simple local-filesystem upload app.

## 18. Security Model

The system includes several layers of security and access control.

Authentication and identity:

- JWT-based authentication.
- Password hashing.
- Session-cookie support.
- WorkOS/AuthKit integration readiness.

Authorization:

- Role-based access control.
- Admin/interviewer separation.
- Assignment-aware interviewer access.
- Permission checks for question management and report access.

Request security:

- CSRF protection for session-cookie requests.
- Trusted CSRF origins.
- CORS allowlist.
- Trusted host middleware.
- Security headers.
- Proxy trust controls for client IP handling.

Abuse/resource controls:

- Redis-backed rate limiting.
- Expensive AI path limiting.
- LLM concurrency limits.
- Upload size limits.
- Profile image size limits.

Configuration security:

- Minimum JWT secret length.
- Placeholder/weak secret rejection.
- JWT algorithm allowlist.
- Absolute URL validation for configured origins/endpoints.
- Secret redaction in logs.

The security model is meaningful because it combines coarse role controls with product-specific access rules. Interviewer access is not only based on being an interviewer; it depends on assignment.

## 19. Rate Limiting And LLM Capacity Controls

The system has two related protection layers:

- User/action rate limits.
- LLM operation capacity limits.

Rate limits protect interactive endpoints such as report chat, question feedback, and question regeneration.

LLM capacity controls limit concurrent usage separately for:

- General generation.
- Report chat.
- Interview refinement.
- Question regeneration.

This matters because different AI features have different cost and latency profiles. A report-chat surge should not necessarily exhaust the same capacity pool as background report generation or question regeneration.

## 20. Configuration And Environment Management

The backend is heavily environment-configurable.

Configuration areas include:

- Database connection and pool sizing.
- Auth and JWT.
- LLM provider settings.
- Per-operation LLM model policies.
- Report-chat limits.
- Interview-refinement limits.
- Parser engine version.
- Upload and storage settings.
- MinIO settings.
- Redis settings.
- Celery queue and task settings.
- Qdrant and RAG settings.
- OpenTelemetry settings.
- Langfuse settings.
- CORS, trusted hosts, and frontend origin.
- WorkOS/AuthKit settings.
- Development bootstrap options.

The config layer validates values rather than accepting arbitrary strings blindly. It checks required settings, numeric values, URL formats, secret strength, JWT algorithm choices, upload directory writability, observability protocol choices, and origin formats.

This centralizes environment behavior and makes misconfiguration fail early.

## 21. Observability

The repo includes an observability baseline intended to support both operational telemetry and AI-specific tracing.

Operational telemetry:

- Request IDs.
- Structured access logs.
- Health endpoint.
- Readiness endpoint.
- OpenTelemetry-compatible spans.
- Custom metrics for HTTP requests, processing jobs, Celery tasks, LLM calls, RAG retrieval, and RAG indexing.
- Optional OTLP export for Grafana-style backends.
- Safe no-op behavior when observability is disabled.

AI observability:

- Langfuse wrapper for LLM calls.
- Langfuse wrapper for RAG retrieval.
- Generation observations for LLM calls.
- Retrieval metadata for RAG operations.
- Token estimates, model/provider metadata, status, latency, and fallback reason tracking.
- Prompt/response capture disabled by default to avoid leaking applicant data.

Important observability principle:

- Observability should never be user-facing failure infrastructure. If a tracing/metrics provider is unavailable, product flows should continue.

## 22. Health, Readiness, And Middleware

The API includes middleware and endpoints that support production operations.

Request middleware:

- Adds or propagates request IDs.
- Logs request method, path, status, duration, and request ID.
- Adds security headers.
- Enforces CSRF where applicable.
- Records request metrics when observability is enabled.

Health/readiness behavior:

- Health provides basic liveness.
- Readiness checks database, storage, LLM configuration, queue/Redis state, and observability configuration.

This gives operators and deployment systems a way to distinguish "process is alive" from "required dependencies are ready."

## 23. Docker And Local Infrastructure

The backend stack is Dockerized for local development.

Local backend services include:

- API server.
- Database migration runner.
- Celery worker.
- PostgreSQL.
- Redis.
- Qdrant.
- MinIO.
- MinIO bucket initializer.

Persistent volumes are used for database, uploads, Redis, MinIO, and Qdrant storage.

The frontend currently runs separately through Node.js. This is a known limitation: the backend stack is Dockerized, but the whole product is not yet one-command full-stack Docker.

The repo also contains an optional self-hosted Langfuse stack for local AI observability experiments.

## 24. CI And Testing

The project includes CI for backend validation.

CI behavior:

- Runs on pushes and pull requests.
- Starts Postgres and Redis service containers.
- Installs backend dependencies.
- Runs database migrations.
- Runs backend tests.
- Uses test-safe environment settings.
- Disables live LLM calls.
- Uses eager Celery mode for testability.

Testing coverage areas include:

- API health and readiness.
- Auth behavior.
- Role and assignment authorization.
- Admin and interviewer workflows.
- Upload validation.
- Storage behavior.
- Processing job lifecycle.
- Parser hardening.
- Schema validation.
- Security behavior.
- Signal detection.
- RAG retrieval.
- Interview generator RAG integration.
- Orchestrator behavior.

Testing should not dominate the product story, but it is part of the repository's engineering maturity.

## 25. AI Quality And Safety Controls

The system includes multiple AI-specific quality controls:

- Deterministic extraction before LLM synthesis.
- Canonical records separate from final prose.
- Stage-specific prompts.
- Structured output expectations.
- Policy validation after generation.
- Sanitization of model output.
- Malformed-output recovery.
- Degraded/fallback behavior.
- Generated artifact versioning.
- Retrieval snapshots.
- Human ratings.
- Feedback-driven retrieval.
- LLM capacity limits.
- Fallback models.
- Token estimation.
- AI tracing with privacy-safe defaults.

These controls make the app more reliable than a simple LLM wrapper because they address data quality, output validation, auditability, cost control, and failure behavior.

## 26. Production-Readiness Patterns

Reliability patterns:

- Async background processing.
- Durable job state.
- Retry and backoff.
- Stale-job recovery.
- Idempotency guards.
- Locking around critical job sections.
- Graceful fallbacks.
- Provider fallback models.
- Capacity limits.

Security patterns:

- Role and assignment authorization.
- JWT/session auth.
- WorkOS readiness.
- CSRF protection.
- CORS allowlist.
- Trusted host validation.
- Security headers.
- Rate limiting.
- Upload limits.
- Secret validation and redaction.

Operability patterns:

- Health/readiness endpoints.
- Request IDs.
- Structured logs.
- OpenTelemetry metrics and spans.
- AI traces through Langfuse.
- Docker Compose infrastructure.
- Alembic migrations.
- CI validation.
- Runbook-style documentation.

AI product patterns:

- Multi-stage pipeline.
- Product-specific prompt families.
- Output validation.
- Feedback loops.
- Versioned AI artifacts.
- RAG retrieval with snapshots.
- Privacy-aware tracing.

## 27. Scale And Complexity Of The Project

The project combines multiple substantial concerns that are usually separate in smaller applications:

- Full-stack role-based product UI.
- PDF/document intelligence pipeline.
- Structured canonical data model.
- Multi-stage LLM workflow.
- Report generation and export.
- Interactive report copilot.
- Interview workspace lifecycle.
- Human feedback loop.
- Versioned generated questions.
- Semantic retrieval over generated artifacts.
- Async worker architecture.
- Object storage.
- Security hardening.
- Observability and tracing.
- CI and migrations.

The scale is not measured only by number of files. The complexity comes from coordinating AI generation, durable product state, human review workflows, asynchronous execution, security boundaries, and derived retrieval indexes in one coherent system.

## 28. Current Limitations And Caveats

Known limitations:

- The frontend is not yet included in the main Docker Compose stack.
- Grafana Cloud credentials are not configured yet.
- Langfuse provider setup needs final live verification.
- Some latest Langfuse workflow hardening edits are uncommitted and should be reviewed before being treated as shipped.
- D2C/Common App support is planned but not implemented as the current product path.
- Broad local test runs can be sensitive to `.env` and local service state.
- Full live upload-to-report-to-regeneration validation depends on configured LLM/provider keys and local services.
- A concrete production cloud deployment architecture is not yet documented.

Production-readiness caveat:

- The repo contains many production-readiness patterns, but a strict production launch would still require managed infrastructure, secrets management, backups, monitoring dashboards, alert thresholds, access review, load testing, and security review.

## 29. Summary

AG Interview Standardiser is a full-stack AI workflow system with a mature architecture for its stage. It includes a structured PDF-processing pipeline, canonical data modeling, multi-stage LLM generation, validation guardrails, async processing, object storage, role/assignment security, feedback-driven RAG, observability, and CI.

The most important technical characteristic is that AI output is treated as part of a broader product system. Inputs are parsed and normalized, outputs are validated and versioned, human feedback is captured, retrieval is auditable, long-running work is queued, and failure handling, observability, and security are part of the architecture.

