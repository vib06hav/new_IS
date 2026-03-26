# Backend Target-State Implementation Plan

Transition the backend from a single-shot upload-and-process architecture to a stateful, multi-user workflow with assignments, versioned drafts, publish gating, and role-enforced API surface.

**Scope:** Backend only ([app/](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py#107-133), `tests/`, `alembic/`). No frontend changes.

**Reference docs:** [Frontend_Docs/backend_entity_model.md](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/backend_entity_model.md), [Frontend_Docs/frontend_final_spec.md](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/frontend_final_spec.md)

---

## Proposed Changes

---

### Phase 1 — Schema Migration

#### [MODIFY] [application.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/application.py)
- Rename `pipeline_status` → `status`
- Expand allowed values to: `UPLOADED PROCESSING READY FAILED ASSIGNED DRAFT PUBLISHED`
- Drop `pipeline_confidence` column

#### [MODIFY] [user.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/user.py)
- Add `name` column (`String`, not null)

#### [NEW] `app/models/assignment.py`
- Table `assignments`: [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_auth.py#16-19), `application_id` (unique FK), `interviewer_id` (FK), `assigned_by` (FK), `assigned_at`

#### [NEW] `app/models/draft.py`
- Table `drafts`: [id](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_auth.py#16-19), `application_id` (FK), `version` (Integer), `content` (JSONB), `generated_by` (FK), `is_published` (Boolean), `created_at`

#### [DELETE] [app/models/synthesis_record.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/synthesis_record.py)
- Drop entirely; all synthesis persistence moves to `drafts`

#### [MODIFY] [app/models/__init__.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/__init__.py)
- Remove [SynthesisRecord](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/synthesis_record.py#7-16) import, add `Assignment`, `Draft`

#### [NEW] Alembic migrations
- One migration per change: add `users.name`, rename/expand `applications.status`, drop `applications.pipeline_confidence`, drop `synthesis_records`, create `assignments`, create `drafts`

---

### Phase 2 — Auth Guards

#### [NEW] `app/auth/dependencies.py`
- `require_admin(current_user)` — raises 403 if role != `admin`
- `require_interviewer(current_user)` — raises 403 if role != `interviewer`
- `require_assigned_to(application_id, current_user, db)` — raises 403 if interviewer has no assignment row for this app

#### [MODIFY] [security.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/security.py)
- Fix JWT to use `settings.JWT_ALGORITHM` and `settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES` instead of hardcoded values

#### [MODIFY] [schemas.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/schemas.py)
- Add `name` field to `UserCreate` and `UserResponse`

#### [MODIFY] [service.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/service.py)
- Persist `name` on register

---

### Phase 3 — Upload + Lifecycle Refactor

#### [MODIFY] [applications.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py)
- Upload: persist row as `UPLOADED`, run only deterministic pipeline (agents 1–13 → canonical), set `READY` on success, `FAILED` on failure. Stop before LLM call.
- The LLM generation moves to the `generate` endpoint (Phase 4)

#### [MODIFY] [orchestrator.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/orchestrator.py)
- Split pipeline into two callable functions:
  - `run_deterministic_pipeline(application_id, file_path, db)` → canonical only, returns canonical data
  - `run_synthesis_pipeline(application_id, canonical_data, db)` → LLM + signal → returns Pages 4–5 content

---

### Phase 4 — Admin API Surface

New file or extend [app/api/applications.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py) and add `app/api/users.py`:

| Method | Route | Guard | Action |
|---|---|---|---|
| GET | `/applications` | `require_admin` | List all, optional `?status=` filter |
| GET | `/applications/{id}` | admin or assigned interviewer | Role-aware response |
| POST | `/applications/{id}/retry` | `require_admin` | Reset FAILED → UPLOADED, re-run deterministic |
| POST | `/applications/{id}/assign` | `require_admin`, status==READY | Create assignment row, set ASSIGNED |
| PUT | `/applications/{id}/assign` | `require_admin`, status in ASSIGNED/DRAFT | Update assignment row, discard drafts, set ASSIGNED |
| GET | `/users/interviewers` | `require_admin` | List users where role==interviewer |
| DELETE | `/users/{id}` | `require_admin` | Delete user, delete assignments, reset apps to READY, discard drafts |
| GET | `/assignments` | `require_admin` | List all assignment rows with interviewer + status |

#### [NEW] [app/api/schemas.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py) additions
- `ApplicationListItem` — id, status, created_at, assigned_interviewer (name/email or null)
- `ApplicationDetailAdmin` — role-aware: canonical only before publish, Pages 4–5 only after publish
- `ApplicationDetailInterviewer` — canonical + latest draft content if DRAFT/PUBLISHED
- `AssignmentListItem` — application_id, interviewer (id/name/email), status
- `InterviewerListItem` — id, name, email, active_assignment_count

---

### Phase 5 — Interviewer API Surface

#### [NEW] `app/api/interviewer.py`

| Method | Route | Guard | Action |
|---|---|---|---|
| GET | `/me/applications` | `require_interviewer` | List apps assigned to current user |
| POST | `/applications/{id}/generate` | `require_interviewer` + `require_assigned_to` | Run synthesis pipeline, insert draft row, version +1, set DRAFT |
| POST | `/applications/{id}/publish` | `require_interviewer` + `require_assigned_to`, status==DRAFT | Set latest draft `is_published=true`, set PUBLISHED |

---

### Phase 6 — Legacy Cleanup

#### [MODIFY] [app/api/applications.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py)
- Remove old response shape ([SynthesisOutput](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py#36-43), [ApplicationResponse](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py#44-53) with full synthesis)
- Remove `synthesis_records` references
- Remove uploader-based ownership check (replace with assignment-based)

#### [MODIFY] [app/api/schemas.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py)
- Remove [SynthesisOutput](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py#36-43), [ApplicationsListResponse](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py#54-56) (old shapes)
- Keep only new role-aware response models

#### [MODIFY] [app/main.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/main.py)
- Register new routers (`interviewer.py`, `users.py`)

---

### Phase 7 — Test Suite Rebuild

Stale tests to **delete**: [test_agents.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_agents.py) (references removed modules), [test_policy.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_policy.py), [test_llm_client.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_llm_client.py), [test_api.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_api.py) (stub)

Tests to **keep**: [test_auth.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_auth.py), [test_security.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_security.py) (currently passing, just update for `name` field)

New tests to **write**:

| File | Covers |
|---|---|
| `tests/test_models.py` | Schema shape, constraints, FK behaviour via SQLite in-memory |
| `tests/test_lifecycle.py` | State machine transitions: all valid paths + blocked transitions |
| `tests/test_auth_guards.py` | `require_admin` blocks interviewer; `require_interviewer` blocks admin; `require_assigned_to` blocks unassigned interviewer |
| `tests/test_admin_api.py` | All admin endpoints: happy paths + state guards + side effects (reassign discards draft, remove resets to READY) |
| `tests/test_interviewer_api.py` | Generate, regenerate (version increments), publish, blocked after publish |
| `tests/test_visibility.py` | Admin never sees draft content; interviewer sees only own apps |

---

## Verification Plan

### Automated Tests

All tests use `pytest` with SQLite in-memory DB override (same pattern as existing [test_auth.py](file:///c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/test_auth.py)).

```powershell
# Run only backend tests (excludes stale retired tests)
cd c:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser
PYTHONPATH=. pytest tests/test_auth.py tests/test_security.py tests/test_models.py tests/test_lifecycle.py tests/test_auth_guards.py tests/test_admin_api.py tests/test_interviewer_api.py tests/test_visibility.py -v
```

**Per-phase checkpoints:**

After Phase 1 (schema):
```powershell
# Verify Alembic runs clean on fresh DB
alembic upgrade head
# Inspect schema
python -c "from app.models import *; print('models ok')"
```

After Phase 2 (auth guards):
```powershell
PYTHONPATH=. pytest tests/test_auth.py tests/test_security.py tests/test_auth_guards.py -v
```

After Phases 3–5 (API):
```powershell
PYTHONPATH=. pytest tests/test_lifecycle.py tests/test_admin_api.py tests/test_interviewer_api.py tests/test_visibility.py -v
```

Final full suite:
```powershell
PYTHONPATH=. pytest tests/test_auth.py tests/test_security.py tests/test_models.py tests/test_lifecycle.py tests/test_auth_guards.py tests/test_admin_api.py tests/test_interviewer_api.py tests/test_visibility.py -v
```

### Manual Smoke Check (after all phases complete)

Start the server:
```powershell
cd c:\Users\vibha\OneDrive\Desktop\AG_InterviewStandardiser
uvicorn app.main:app --reload
```

Then using curl or any REST client:
1. `POST /auth/register` — create admin user with `name`
2. `POST /auth/register` — create interviewer user with `name`
3. `POST /auth/login` — get admin JWT
4. `POST /applications/upload` — upload a PDF → response should show status `READY`
5. `GET /applications` — admin list should show the app as `READY`
6. `POST /applications/{id}/assign` — assign interviewer → status becomes `ASSIGNED`
7. Login as interviewer → `GET /me/applications` → see the assigned app
8. `POST /applications/{id}/generate` → status becomes `DRAFT`, version=1
9. `POST /applications/{id}/generate` again → still `DRAFT`, version=2
10. `GET /applications/{id}` as admin → should NOT contain Pages 4–5 content
11. `POST /applications/{id}/publish` → status becomes `PUBLISHED`
12. `GET /applications/{id}` as admin → should NOW contain Pages 4–5
13. `POST /applications/{id}/generate` again → should return 403/409 (blocked)

### Health Check
```powershell
curl http://localhost:8000/health
# Expected: {"status": "ok", "message": "Service is healthy and database is reachable."}
```
