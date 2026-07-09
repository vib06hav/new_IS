# Phase Direction

This roadmap keeps the current B2B product intact while raising the engineering maturity of the platform before any D2C expansion.

## Phase 1 - Base Stability

Make the current app dependable and easier to evolve.

- Add basic CI/CD for backend tests, frontend build, Docker build, and Alembic checks.
- Clean up dependency/runtime drift where it affects local or production confidence.
- Add request IDs and structured log foundations.
- Keep changes narrow and avoid product rewrites.

## Phase 2 - Async Job Architecture

Move long-running work onto standard queue infrastructure.

- Add Redis/Celery.
- Run PDF processing, report generation, question regeneration, and vector indexing as tasks.
- Keep Postgres job records for UI status and operational visibility.
- Add retry, backoff, and failed-job handling.

## Phase 3 - Vector RAG For Question Generation

Use historical ratings to improve generated interview questions.

- Add Qdrant integration.
- Index generated questions, focus-area context, and rating metadata.
- Retrieve similar high-rated examples during question regeneration.
- Store retrieval snapshots with regenerated question versions.
- Degrade gracefully when retrieval is unavailable.

## Phase 4 - Observability And Evaluation

Make platform behavior measurable.

- Add metrics for requests, jobs, LLM calls, and retrieval.
- Add OpenTelemetry-compatible tracing where useful.
- Use Grafana/Prometheus for operational metrics.
- Use self-hosted Langfuse for LLM/RAG traces and lightweight evaluation hooks.

## Phase 5 - D2C Expansion

Add direct-consumer scenarios after the platform base is stable.

- Start with Common App.
- Reuse the async, RAG, and observability foundation.
- Keep institutional and D2C paths separated by scenario configuration.
