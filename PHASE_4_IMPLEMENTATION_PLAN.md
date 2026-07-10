# Phase 4 Implementation Plan

## Direction

Phase 4 should make the platform observable without making it expensive or vendor-heavy. The goal is to produce a credible production observability story for the FastAPI, Celery, LLM, and RAG pipeline while keeping secrets and provider setup outside the first implementation pass.

Recommended stack:

- OpenTelemetry as the instrumentation standard.
- Grafana Cloud as the free hosted backend for metrics, logs, traces, dashboards, and alerts.
- Langfuse as the LLM/RAG observability layer, self-hosted through Docker Compose.

This gives the project a clean resume narrative: operational telemetry for the distributed backend plus AI-native tracing for prompts, retrieval, costs, latency, and quality signals.

## Goals

- Add OpenTelemetry-compatible tracing and metrics to the API and worker runtime.
- Capture request, job, LLM, Qdrant, and report-generation behavior with useful dimensions.
- Add Langfuse traces for LLM generation, report chat, refinement, question generation, and question regeneration.
- Keep the app fully functional when observability providers are not configured.
- Make the implementation environment-variable driven, with empty defaults until keys are added later.
- Add local self-hosted Langfuse support in Docker Compose with headless local project initialization.
- Add a minimal dashboard/metric naming guide so the system is easy to explain and demo.

## Non-Goals

- No paid observability services.
- No Braintrust reintroduction.
- No large frontend observability implementation yet.
- No product analytics or user funnel analytics.
- No full incident-management/on-call setup.
- No mandatory provider dependency in local development or tests.
- No secret or key setup in this implementation pass.

## Current Baseline

The repo already has some useful foundations:

- Request IDs are present in API middleware.
- Structured logs exist across request handling, processing jobs, Celery tasks, LLM calls, and RAG indexing.
- Celery and Redis are already part of the runtime.
- Qdrant RAG snapshots persist useful retrieval metadata.
- LLM client boundaries already know operation types such as generation, report chat, refinement, and regeneration.

Phase 4 should layer observability on these boundaries rather than rewrite them.

## Architecture

### Operational Telemetry

Use OpenTelemetry as the vendor-neutral instrumentation layer.

Primary targets:

- FastAPI request traces and latency.
- Celery task traces and durations.
- Postgres connection/query visibility where simple and safe.
- Redis/Celery queue visibility through application metrics.
- Qdrant search/index timing.
- LLM request timing, retry count, provider/model, and success/failure status.

Grafana receives telemetry through OTLP once credentials are configured. If OTLP is not configured, instrumentation should be disabled or export to console only in development.

### AI Observability

Use Langfuse for AI-specific traces.

Primary trace groups:

- `deterministic_pipeline`
- `report_generation`
- `question_generation`
- `question_regeneration`
- `report_chat`
- `interview_refinement`
- `rag_retrieval`
- `rag_indexing`

Each Langfuse trace should capture:

- Application ID and display ID when available.
- Operation name.
- Model/provider.
- Prompt version or prompt family.
- Latency.
- Estimated prompt and completion tokens.
- Error status.
- Retrieval provider, collection, selected point IDs, and fallback reason for RAG operations.

Do not send raw secrets. Avoid sending full uploaded PDFs. For sensitive applicant content, prefer compact metadata and optionally sampled prompt/response bodies behind a config flag.

## Workstreams

### Workstream 1 - Config And Safe Defaults

Add environment settings for:

- OpenTelemetry enable/disable flag.
- OTLP endpoint.
- OTLP headers or auth token.
- Service name and deployment environment.
- Langfuse enable/disable flag.
- Langfuse host.
- Langfuse public key.
- Langfuse secret key.
- Prompt/body capture enable/disable flag.

Defaults should keep telemetry disabled unless explicitly configured.

### Workstream 2 - OpenTelemetry Foundation

Add a small telemetry package, likely under `app/telemetry/`.

Responsibilities:

- Configure tracing and metrics once at app startup.
- Instrument FastAPI.
- Provide helper functions for custom spans and counters.
- Avoid raising runtime errors when exporters are missing or disabled.
- Share the same setup between API and Celery worker processes.

Suggested dependencies:

- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp`
- `opentelemetry-instrumentation-fastapi`
- `opentelemetry-instrumentation-sqlalchemy`
- `opentelemetry-instrumentation-redis`
- `opentelemetry-instrumentation-celery`

### Workstream 3 - Application Metrics

Add explicit metrics where auto-instrumentation is not enough.

Suggested counters/histograms:

- `agis_http_requests_total`
- `agis_processing_jobs_total`
- `agis_processing_job_duration_seconds`
- `agis_celery_tasks_total`
- `agis_celery_task_duration_seconds`
- `agis_llm_requests_total`
- `agis_llm_request_duration_seconds`
- `agis_llm_retries_total`
- `agis_rag_retrievals_total`
- `agis_rag_retrieval_duration_seconds`
- `agis_rag_index_total`
- `agis_rag_index_duration_seconds`
- `agis_question_regenerations_total`

Useful labels:

- `status`
- `operation`
- `provider`
- `model`
- `queue`
- `task_name`
- `retrieval_provider`
- `fallback_reason`

Keep label cardinality low. Do not use raw application IDs as metric labels.

### Workstream 4 - Langfuse LLM/RAG Tracing

Add a Langfuse client wrapper with safe no-op behavior.

Trace boundaries:

- Around LLM client calls.
- Around report synthesis stages.
- Around question generation and regeneration.
- Around Qdrant retrieval and indexing.

Stored Langfuse metadata should mirror what we already persist in DB snapshots:

- Prompt family.
- Model/provider.
- Operation.
- Retrieval provider.
- Retrieval strategy version.
- Retrieved point IDs.
- Fallback reason.
- Token estimates.
- Latency.

Prompt and response text capture should be controlled by config, because applicant data can be sensitive.

### Workstream 5 - Docker Compose Support

Add optional self-hosted Langfuse services to Docker Compose.

Likely services:

- `langfuse`
- `langfuse-db` or reuse Postgres only if cleanly isolated
- `clickhouse`

Prefer following Langfuse's current self-hosted Docker Compose shape, but keep the app integration independent so local development works even if Langfuse is not running.

Grafana Cloud does not need a local service. It only needs OTLP exporter configuration later.

### Workstream 6 - Dashboards And Runbook Notes

Add lightweight dashboard/runbook documentation after instrumentation exists.

Minimum dashboard panels:

- API request rate and p95 latency.
- API error rate.
- Celery task rate, failures, and p95 duration.
- Processing job success/failure count.
- LLM latency by operation/model.
- LLM error/retry count.
- Qdrant retrieval/index latency.
- RAG fallback count.
- Question regeneration count and failure rate.

This can be a short markdown guide first. Grafana dashboard JSON can come after we know the exact metric names emitted by the implementation.

## Suggested Build Order

1. Add config flags and `.env.example` placeholders.
2. Add telemetry package with no-op defaults.
3. Wire OpenTelemetry setup into FastAPI startup.
4. Wire OpenTelemetry setup into Celery worker startup.
5. Add custom spans/metrics around processing jobs.
6. Add custom spans/metrics around LLM calls.
7. Add custom spans/metrics around Qdrant retrieval and indexing.
8. Add Langfuse no-op wrapper.
9. Add Langfuse traces around LLM and RAG boundaries.
10. Add optional Langfuse Docker Compose services.
11. Add basic tests for disabled/no-op telemetry behavior.
12. Add a short dashboard/runbook guide.
13. Add real Grafana/Langfuse variables and verify live telemetry.

## Exit Criteria

Phase 4 is complete when:

- The app runs normally with observability disabled.
- API requests emit OpenTelemetry traces when configured.
- Celery tasks emit OpenTelemetry traces when configured.
- Core custom metrics exist for API, jobs, LLM, and RAG.
- Langfuse receives traces for live LLM generation and regeneration when configured.
- RAG traces include retrieval provider, selected point IDs, and fallback reason.
- Docker Compose can run self-hosted Langfuse locally.
- No secrets are committed.
- A short dashboard/runbook guide explains what to inspect during a demo.

## Implementation Notes

- Keep telemetry helpers small and boring.
- Do not make observability failures user-facing.
- Use request IDs as trace/log correlation where possible.
- Avoid high-cardinality metrics.
- Prefer metadata-first Langfuse traces until we explicitly decide to capture full prompt and response bodies.
- Treat this phase as production polish, not a monitoring science project.
