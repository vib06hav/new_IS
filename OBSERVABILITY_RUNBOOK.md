# Observability Runbook

## Scope

Phase 4 uses two observability layers:

- OpenTelemetry exports operational telemetry to Grafana Cloud when configured.
- Langfuse captures LLM and RAG traces when configured.

Both are disabled by default and safe to leave unconfigured.

## Grafana / OpenTelemetry

Set these after creating the Grafana Cloud stack:

- `OBSERVABILITY_ENABLED=true`
- `OBSERVABILITY_EXPORTER=otlp`
- `OTEL_SERVICE_NAME=ag-interview-standardiser`
- `OTEL_DEPLOYMENT_ENVIRONMENT=development`
- `OTEL_EXPORTER_OTLP_ENDPOINT=<grafana-otlp-endpoint>`
- `OTEL_EXPORTER_OTLP_HEADERS=<grafana-auth-headers>`
- `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`

Useful dashboard panels:

- API request rate: `agis_http_requests_total`
- API p95 latency: `agis_http_request_duration_seconds`
- Processing job rate: `agis_processing_jobs_total`
- Processing job duration: `agis_processing_job_duration_seconds`
- Celery task rate: `agis_celery_tasks_total`
- Celery task duration: `agis_celery_task_duration_seconds`
- LLM request rate: `agis_llm_requests_total`
- LLM latency by operation/model: `agis_llm_request_duration_seconds`
- LLM retry count: `agis_llm_retries_total`
- RAG retrieval rate: `agis_rag_retrievals_total`
- RAG retrieval duration: `agis_rag_retrieval_duration_seconds`
- RAG indexing rate: `agis_rag_index_total`
- RAG indexing duration: `agis_rag_index_duration_seconds`
- RAG fallback count: `agis_rag_retrieval_results_total`

Recommended alerts:

- API 5xx count is non-zero for 5 minutes.
- Processing job failures are non-zero.
- Celery task failures are non-zero.
- LLM error rate exceeds 10 percent.
- RAG fallback count spikes above the normal baseline.
- LLM p95 latency exceeds the acceptable demo threshold.

## Langfuse

Start the local Langfuse stack:

```powershell
docker compose -f docker-compose.langfuse.yml up -d
```

Open:

```text
http://localhost:3001
```

After creating a project, set:

- `LANGFUSE_ENABLED=true`
- `LANGFUSE_HOST=http://localhost:3001`
- `LANGFUSE_PUBLIC_KEY=<project-public-key>`
- `LANGFUSE_SECRET_KEY=<project-secret-key>`
- `LANGFUSE_CAPTURE_IO=false`

Keep `LANGFUSE_CAPTURE_IO=false` unless you explicitly want prompts and responses sent to Langfuse. With it disabled, traces still capture operation, model, latency, token estimates, retrieval metadata, selected Qdrant point IDs, and fallback reasons.

Useful Langfuse traces to inspect:

- `call_1`
- `call_2`
- `call_3`
- `question_regeneration`
- `report_chat`
- `interview_refinement`
- `rag_retrieval.question_generation`
- `rag_retrieval.question_regeneration`

## Verification Flow

1. Start the app stack.
2. Start Langfuse if testing LLM traces.
3. Add Grafana/Langfuse env values.
4. Restart API and worker containers.
5. Upload a demo PDF.
6. Wait for deterministic processing to complete.
7. Generate the final report.
8. Rate a question and regenerate one question.
9. Check Grafana for API, job, LLM, and RAG metrics.
10. Check Langfuse for LLM generation and RAG retrieval traces.

## Safety Notes

- Observability failures must not break user-facing product behavior.
- Do not use application IDs, user IDs, or raw PDF content as metric labels.
- Keep prompt/response capture disabled unless intentionally testing trace content.
- Treat Qdrant and Langfuse as derived observability systems; Postgres remains the source of truth.
