# Phase 2 Implementation Plan

Phase 2 replaces the current polling-style background worker with a Celery + Redis execution layer while keeping the existing B2B product behavior intact.

## Objective

Move long-running work out of API requests and into durable, retryable background tasks.

The main product-facing invariant stays the same: Postgres owns application state and job status; Redis/Celery owns task delivery and worker execution.

## Current Baseline

- `docker-compose.yml` already includes `redis` and a `worker` service.
- `app.processing` already has `ProcessingJob` records, retry metadata, stale-job recovery, and a dedicated polling worker.
- Upload already creates an `Application`, creates a `ProcessingJob`, and returns quickly.
- The biggest synchronous hotspots still left are final report generation, question regeneration, report chat, and export generation.

## Non-Goals

- No Qdrant or vector RAG in this phase.
- No D2C upload scenarios.
- No LangGraph/LangChain orchestration yet.
- No major schema redesign beyond task tracking fields required for Celery integration.
- No frontend redesign, only small status/progress affordances if the existing UI needs them.

## Target Architecture

Use Redis as Celery broker/result backend and keep Postgres as the authoritative job ledger.

- API process: validates input, writes DB state, enqueues Celery tasks, returns immediately.
- Celery worker: executes PDF processing, report generation, question regeneration, export sync, and maintenance tasks.
- Postgres: stores `ProcessingJob` and application lifecycle states for UI/admin visibility.
- Redis: stores queue messages, task routing, locks, and Celery result metadata.

## Workstream 1 - Celery Foundation

Add the Celery app and worker boot path.

- Add `celery` to backend dependencies.
- Add `app/tasks/celery_app.py` with broker/backend config from settings.
- Add queue names for `processing`, `generation`, `maintenance`, and `default`.
- Replace `python -m app.worker` in Docker with a Celery worker command.
- Keep `app.worker` only as a compatibility wrapper or remove it after tests pass.
- Add config values for broker URL, result backend, task time limits, prefetch, concurrency, and eager mode for tests.

Acceptance criteria:

- `docker compose up` starts API, Redis, and a Celery worker.
- Worker can import the app and register tasks.
- `/readiness` reports Celery/Redis queue readiness separately from simple Redis coordination.

## Workstream 2 - Job Dispatch Contract

Create a small service boundary between API routes and background execution.

- Add a dispatcher module that creates/updates `ProcessingJob` rows and calls `task.delay()` or `apply_async()`.
- Store Celery task IDs on job rows.
- Add idempotency guards so duplicate active jobs are not enqueued for the same application/job type.
- Keep API responses compatible with the current product.
- Keep application status transitions centralized and explicit.

Likely schema addition:

- `processing_jobs.celery_task_id`
- `processing_jobs.queue_name`
- `processing_jobs.progress`
- `processing_jobs.error_code`

Acceptance criteria:

- Upload enqueues exactly one active deterministic pipeline task per application.
- Retry reuses the same dispatch path.
- Admin queue removal can revoke or ignore outstanding Celery tasks safely.

## Workstream 3 - Deterministic Pipeline Task

Move the existing PDF processing execution from polling into Celery.

- Convert `process_next_processing_job()` logic into `run_deterministic_pipeline_task(job_id)`.
- Keep storage materialization, Redis lock boundary, and DB session lifecycle inside the task.
- Use Celery retries with exponential backoff, but continue writing attempts/status/error into Postgres.
- Preserve stale-job recovery as a maintenance task for crashed workers.
- Make task idempotent: if the application is already processed/ready and the job completed, return without rerunning.

Acceptance criteria:

- Upload returns immediately.
- Worker processes PDF and moves application through `PROCESSING -> PROCESSED` or `READY`/`FAILED` exactly as today.
- Failure retries are visible in `processing_jobs`.
- Existing processing tests can be adapted to call the task synchronously/eagerly.

## Workstream 4 - Final Report And Regeneration Tasks

Move the remaining expensive LLM operations behind queues where product behavior benefits from it.

- Add `generate_final_report_task(application_id, requested_by_user_id)`.
- Add `regenerate_question_task(application_id, thread_id, requested_by_user_id)`.
- Keep report chat synchronous for now unless latency becomes painful, because it is an interactive copilot endpoint.
- Preserve LLM capacity limiting inside worker tasks.
- Add task-level request/correlation IDs so logs can connect API enqueue to worker execution.

Acceptance criteria:

- Admin final report generation can be queued and status-polled.
- Question regeneration can be queued or kept synchronous behind a feature flag if UI changes would be too large.
- Failed LLM tasks do not leave applications in ambiguous states.

## Workstream 5 - Docker And Local Testing

Make the async stack easy to run locally.

- Update Docker Compose worker command to Celery.
- Add an optional Celery Flower service only if it stays low-friction.
- Add Redis healthcheck.
- Add documented commands inside the plan comments/scripts only if needed, not a docs-heavy pass.

Suggested local verification:

- `docker compose up --build`
- `docker compose exec api alembic upgrade head`
- `docker compose exec api pytest -q dev/tests/test_processing.py`
- `docker compose exec api pytest -q dev/tests/test_api.py`

Acceptance criteria:

- API and worker boot in Docker.
- Upload-processing path works with Redis/Celery.
- Focused backend tests pass inside the container.

## Workstream 6 - Observability Hooks For Phase 4

Add enough task instrumentation now so Phase 4 has a clean attachment point.

- Log `job_id`, `celery_task_id`, `application_id`, `job_type`, `queue`, `attempt`, and `request_id`.
- Add task lifecycle events in one helper: queued, started, retried, completed, failed.
- Expose queue readiness in `/readiness`.
- Avoid adding Grafana/Braintrust task dashboards in this phase.

Acceptance criteria:

- API logs show task enqueue.
- Worker logs show task lifecycle.
- A failed task can be traced from API request to worker failure.

## Suggested Implementation Order

1. Add Celery dependency, settings, app factory, task modules, and Docker worker command.
2. Add job dispatch service and DB migration for Celery metadata.
3. Convert deterministic PDF processing to a Celery task.
4. Adapt upload/retry/delete queue paths to use dispatch/revoke semantics.
5. Add focused tests with eager Celery mode.
6. Move final report generation into a task.
7. Decide whether question regeneration stays synchronous or becomes queued in this phase.
8. Add readiness/task logging polish.
9. Run focused tests inside Docker.

## Phase 2 Exit Criteria

- Redis/Celery is the real background execution layer.
- The current upload-processing path no longer depends on a polling loop.
- Postgres remains the source of truth for job/application status.
- Retries, failures, and stale jobs are visible and recoverable.
- Docker can run API + worker + Redis + Postgres + MinIO together.
- The implementation is ready for Phase 3 Qdrant indexing tasks.
