# Phase 1 Implementation Plan

Phase 1 focuses on base stability only. The goal is to make the current B2B system easier to trust before adding Celery, Qdrant, or D2C flows.

## Goals

- Establish a basic CI/CD safety net.
- Stabilize dependency/runtime issues that affect confidence.
- Add lightweight request tracing and structured logs.
- Avoid broad refactors, product changes, and docs-heavy work.

## Non-Goals

- No Qdrant work.
- No Celery migration.
- No D2C scenarios.
- No LangGraph/LangChain integration.
- No large service-layer rewrite.

## Workstream 1 - CI/CD Baseline

Add GitHub Actions workflows for:

- Backend tests with `pytest`.
- Frontend dependency install and production build.
- Docker image build.
- Alembic migration sanity check.

Recommended workflow files:

- `.github/workflows/backend.yml`
- `.github/workflows/frontend.yml`
- `.github/workflows/docker.yml`

Acceptance criteria:

- CI runs on pull requests and pushes to main.
- Backend workflow installs Python dependencies and runs `pytest`.
- Frontend workflow runs `npm ci` and `npm run build`.
- Docker workflow builds the backend image without pushing it.
- Migration check can run against a temporary Postgres service or a lightweight migration command.

## Workstream 2 - Dependency And Runtime Stabilization

Tighten dependency management enough that local and CI behavior match.

Tasks:

- Pin critical backend dependencies more deliberately.
- Fix known auth hashing dependency drift around `passlib` and `bcrypt`.
- Separate dev/test-only dependencies if practical.
- Confirm frontend uses lockfile-based installs in CI.

Acceptance criteria:

- Fresh install works in CI.
- Auth hashing works consistently.
- Dependency versions are intentional and reviewable.

## Workstream 3 - Request IDs And Structured Logs

Add minimal tracing foundations without a full observability stack.

Tasks:

- Add middleware that reads `X-Request-ID` or generates one.
- Return `X-Request-ID` on every response.
- Make request ID available to route/service logs.
- Add structured log fields for method, path, status code, duration, and request ID.

Acceptance criteria:

- Every HTTP response includes `X-Request-ID`.
- Logs can be correlated by request ID.
- No endpoint behavior changes.

## Workstream 4 - Basic Health And Readiness Signals

Keep this small and practical.

Tasks:

- Preserve `/health` for basic liveness.
- Add or extend a readiness check for DB, Redis coordination mode, storage backend, and LLM config presence.
- Avoid exposing secrets or sensitive config values.

Acceptance criteria:

- Readiness response shows dependency status without leaking credentials.
- Production can distinguish app boot from dependency readiness.

## Workstream 5 - Small Cleanup Around Status Strings

Start reducing scattered state strings without changing data models.

Tasks:

- Add central constants for application, processing job, workspace, and user access statuses.
- Replace only the most repeated or risky inline strings.
- Do not perform a large enum migration yet.

Acceptance criteria:

- New constants are used in the main route/service paths touched in Phase 1.
- Existing API payloads remain unchanged.

## Suggested Order

1. Add CI workflow skeletons.
2. Stabilize dependency pins.
3. Add request ID middleware and structured request logs.
4. Add readiness signal.
5. Add central status constants.
6. Run the CI-equivalent commands locally when the environment is available.

## Phase 1 Exit Criteria

- CI exists and covers backend, frontend, Docker, and migrations at a basic level.
- Request IDs are present in responses and logs.
- Runtime dependency drift is cleaned up enough for repeatable installs.
- Basic readiness checks exist.
- No major product behavior has changed.
