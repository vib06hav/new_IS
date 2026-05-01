# Spec Gap List For Doc Revision

## Purpose

This document captures the gaps between:

- the intended workflow described in:
  - `Frontend_Docs/backend_entity_model.md`
  - `Frontend_Docs/frontend_final_spec.md`
  - `Frontend_Docs/frontend_ui_flow.md`
- the current backend implementation under `app/`

It is meant to help revise the three docs so they reflect either:

1. the backend you actually have today, or
2. the backend you still intend to build next.

This is a documentation gap list only. No code changes are proposed here.

---

## Executive Summary

The current backend is still built around an older single-shot pipeline:

- upload PDF
- run deterministic extraction plus both LLM calls synchronously
- persist one canonical record and one synthesis record
- return the full output immediately

The three docs describe a different product shape:

- multi-user
- multi-stage state machine
- explicit admin/interviewer workflow
- assignment ownership
- versioned drafts
- publish gate
- role-based visibility rules

At the moment, the codebase aligns much more closely with a "process everything on upload and return a final report" model than with the documented "READY -> ASSIGNED -> DRAFT -> PUBLISHED" workflow.

Because of that, the docs currently read more like a target architecture than a description of the implemented backend.

---

## Scope Of Review

Reviewed docs:

- `Frontend_Docs/backend_entity_model.md`
- `Frontend_Docs/frontend_final_spec.md`
- `Frontend_Docs/frontend_ui_flow.md`

Reviewed backend area:

- all files under `app/`

Validation run:

- `python -c "import app.main"`: passed
- `compileall` on `app/`: passed
- `pytest -q`: failed during collection
- `PYTHONPATH=. pytest tests -q`: failed during collection because tests are stale relative to the current code

---

## Gap Categories

## 1. Data Model Gaps

### 1.1 `users.name` is documented but not implemented

Docs say:

- `users` must include `name`
- UI surfaces interviewer names in multiple places

Current backend:

- `User` has `id`, `email`, `password_hash`, `role`, `created_at`
- no `name` column exists

Evidence:

- `app/models/user.py`

Doc impact:

- If the product still requires names everywhere in the UI, the docs are correct and backend is behind
- If names are optional for now, the docs should say that explicitly instead of assuming the field exists

### 1.2 `applications.status` state machine is documented, but backend still uses `pipeline_status`

Docs say:

- `applications.pipeline_status` should become `status`
- states should be:
  - `UPLOADED`
  - `PROCESSING`
  - `READY`
  - `FAILED`
  - `ASSIGNED`
  - `DRAFT`
  - `PUBLISHED`

Current backend:

- model still uses `pipeline_status`
- model still stores `pipeline_confidence`
- runtime uses lower-case values like `processing`, `complete`, `failed`

Evidence:

- `app/models/application.py`
- `app/api/applications.py`
- `app/agents/orchestrator.py`

Doc impact:

- The docs currently describe a future-state schema, not the current schema
- They should be labeled as "target model" if that is intentional
- If they are meant to describe the current backend contract, they are incorrect

### 1.3 `pipeline_confidence` is still present even though docs say to remove it

Docs say:

- drop `pipeline_confidence`
- no soft-failure confidence model

Current backend:

- `pipeline_confidence` exists in the model
- API returns `confidence_score`
- orchestrator still computes and persists aggregate confidence

Evidence:

- `app/models/application.py`
- `app/api/schemas.py`
- `app/agents/orchestrator.py`

Doc impact:

- The docs should decide whether confidence is still a backend concern
- Right now the implementation and docs disagree on whether that field exists at all

### 1.4 `synthesis_records` is documented for removal, but is still the main output table

Docs say:

- `synthesis_records` should be dropped or repurposed
- versioned `drafts` should replace it

Current backend:

- `synthesis_records` is still active
- it enforces `application_id` uniqueness
- it stores the entire final ROS payload
- it is used both for success and for failed-policy persistence

Evidence:

- `app/models/synthesis_record.py`
- `app/agents/orchestrator.py`
- `app/api/applications.py`

Doc impact:

- This is one of the biggest model mismatches
- The docs should clarify whether `drafts` is already a requirement for the next phase or whether the system is still in single-output mode

### 1.5 `assignments` table is documented but entirely absent

Docs say:

- create `assignments`
- one active assignment per application
- admin assignment and reassignment are first-class workflow steps

Current backend:

- no `assignments` model
- no assignment ownership logic
- no assignment query surface

Evidence:

- no matching file or model under `app/models`
- no matching route or service in `app/`

Doc impact:

- The docs currently assume a workflow primitive that does not exist anywhere in the backend

### 1.6 `drafts` table is documented but entirely absent

Docs say:

- multiple drafts per application
- version counter
- latest draft visible
- publish freezes further changes

Current backend:

- no `drafts` model
- no versioned draft persistence
- no publish flag

Evidence:

- no matching file or model under `app/models`
- no draft routes or services in `app/`

Doc impact:

- The docs currently depend on a versioned draft system that the backend does not implement at all

---

## 2. State Machine Gaps

### 2.1 The documented lifecycle does not match runtime states

Docs say:

- `UPLOADED -> PROCESSING -> READY -> ASSIGNED -> DRAFT -> PUBLISHED`
- failure branch to `FAILED`

Current backend:

- upload creates row directly in `processing`
- orchestrator ends in `complete` or `failed`
- there is no `ready`, `assigned`, `draft`, or `published`

Evidence:

- `app/api/applications.py`
- `app/agents/orchestrator.py`

Doc impact:

- The docs should make clear whether:
  - this is a future target state machine, or
  - these are current production states

Right now they read as if they are current, but they are not.

### 2.2 Upload does not pass through `UPLOADED`

Docs say:

- upload enters `UPLOADED`
- a queue worker later moves it to `PROCESSING`

Current backend:

- upload creates `pipeline_status="processing"` immediately
- the request handler itself runs the pipeline

Evidence:

- `app/api/applications.py`

Doc impact:

- The Upload Queue behavior in the UI flow assumes asynchronous job pickup
- That is not how the backend currently behaves

### 2.3 `READY` does not exist as a backend checkpoint

Docs say:

- deterministic Pages 1-3 should become available at `READY`
- later interviewer flow builds Pages 4-5

Current backend:

- canonical data is persisted before the LLM boundary
- but the application row does not transition to a `READY` state
- the request continues into both LLM stages immediately

Evidence:

- `app/agents/orchestrator.py`

Doc impact:

- The docs should clarify whether `READY` is:
  - a required persisted state, or
  - just a conceptual stage in the target architecture

### 2.4 `PUBLISHED` does not exist; final synthesis is effectively available immediately

Docs say:

- Pages 4-5 should appear only after interviewer generation and publish

Current backend:

- upload runs both LLM calls and stores the final Pages 4-5 output immediately
- no publish action exists

Evidence:

- `app/api/applications.py`
- `app/agents/orchestrator.py`

Doc impact:

- The docs currently assume a publish gate that has no backend counterpart

---

## 3. API Surface Gaps

### 3.1 The documented admin/interviewer API surface is mostly missing

Docs list many routes, including:

- `GET /applications`
- `POST /applications/{id}/retry`
- `POST /applications/{id}/assign`
- `PUT /applications/{id}/assign`
- `GET /me/applications`
- `POST /applications/{id}/generate`
- `POST /applications/{id}/publish`
- `GET /users/interviewers`
- `DELETE /users/{id}`
- `GET /assignments`

Current backend only exposes:

- `POST /auth/register`
- `POST /auth/login`
- `POST /applications/upload`
- `GET /applications/{id}`
- `GET /health`

Evidence:

- `app/main.py`
- `app/auth/router.py`
- `app/api/applications.py`

Doc impact:

- The docs currently specify an API platform that does not exist yet
- If the frontend is being built against these routes, that needs to be treated as future work, not current backend behavior

### 3.2 There is no admin list endpoint for queue or reports pages

Docs assume:

- Upload Queue page can list `UPLOADED`, `PROCESSING`, `FAILED`
- Generated Reports page can list `READY`, `ASSIGNED`, `DRAFT`, `PUBLISHED`

Current backend:

- no list endpoint exists at all

Doc impact:

- The docs should either:
  - mark these list endpoints as required-but-unimplemented, or
  - avoid describing them as if they already exist

### 3.3 There is no retry endpoint

Docs say:

- failed items can be retried

Current backend:

- no retry route
- no reset-to-uploaded route

Doc impact:

- Upload Queue doc assumes a user action that is not implemented

### 3.4 There is no generate/regenerate endpoint split

Docs say:

- interviewer can `Generate`
- interviewer can later `Regenerate`

Current backend:

- there is no interviewer-triggered generation action at all
- generation happens at upload time

Doc impact:

- The Generate/Regenerate language in the docs is target-state only

### 3.5 There is no publish endpoint

Docs say:

- publish is a one-way action

Current backend:

- no route
- no publish state
- no publish persistence

Doc impact:

- This should be called out as future-state, not current behavior

---

## 4. Role And Authorization Gaps

### 4.1 Upload is not admin-only in the current backend

Docs say:

- upload is admin-only

Current backend:

- any authenticated user can upload
- `upload_application` only checks that a user exists

Evidence:

- `app/api/applications.py`

Doc impact:

- The docs should not imply that upload is currently protected by admin-only enforcement

### 4.2 The reusable role guards documented in the backend model do not exist

Docs say:

- use reusable dependencies such as `require_admin` and `require_interviewer`

Current backend:

- those dependencies are not defined
- route logic uses ad-hoc current-user retrieval

Evidence:

- no `require_admin` or `require_interviewer` in `app/`

Doc impact:

- This is a design requirement, not a description of the current backend

### 4.3 Ownership is based on uploader, not assignment

Docs say:

- interviewer should only access items assigned to them

Current backend:

- `GET /applications/{id}` allows access to the uploader or an admin
- there is no assignment ownership concept

Evidence:

- `app/api/applications.py`

Doc impact:

- The docs should explicitly note this mismatch if they are being used as a source of truth for current API behavior

### 4.4 Register/login docs omit a current limitation: no interviewer profile data beyond email and role

Current backend auth payloads return:

- `id`
- `email`
- `role`

There is no support yet for:

- `name`
- assignment count
- interviewer profile metadata

Evidence:

- `app/auth/router.py`
- `app/auth/schemas.py`
- `app/auth/service.py`

Doc impact:

- Interviewer manager and assignment UIs currently assume richer user data than the backend actually exposes

---

## 5. Visibility And Content Contract Gaps

### 5.1 Admin draft visibility rules do not match current API behavior

Docs say:

- admin never sees drafts
- admin sees Pages 1-5 only after publish

Current backend:

- the only application detail route returns `synthesis`
- that synthesis includes Pages 4-5 immediately once upload processing succeeds
- there is no draft/private/public separation

Evidence:

- `app/api/applications.py`
- `app/api/schemas.py`
- `app/ros/assembler.py`

Doc impact:

- The docs should not imply those visibility guarantees currently exist

### 5.2 Interviewer-only draft workspace is not representable with the current response model

Docs assume:

- interviewer sees latest draft
- admin does not
- publish changes visibility

Current backend:

- `ApplicationResponse` has a single `synthesis` field
- there is no distinction between canonical-only data, draft-only data, and published-only data

Evidence:

- `app/api/schemas.py`

Doc impact:

- The docs should clarify the exact response shapes required to support those views
- Right now the documented visibility rules are stronger than the implemented contract

### 5.3 The documented separation of Pages 1-3 vs Pages 4-5 is only partially reflected in persistence

Current backend does have a meaningful internal split:

- `canonical_records` stores deterministic Pages 1-3 source material
- `synthesis_records` stores final ROS output including Pages 4-5

But the API does not expose that split in the way the docs describe.

Evidence:

- `app/models/canonical_record.py`
- `app/models/synthesis_record.py`
- `app/agents/orchestrator.py`

Doc impact:

- The docs should note that the internal persistence split exists
- but the external workflow split does not yet exist

---

## 6. Processing And Runtime Behavior Gaps

### 6.1 The backend is synchronous, but the UI docs assume queued async processing

Docs assume:

- uploads sit in queue
- system picks them up
- row-level processing updates happen separately

Current backend:

- upload request performs the full pipeline inline
- the request does not return until processing succeeds or fails

Evidence:

- `app/api/applications.py`

Doc impact:

- The docs should explicitly state whether async processing is:
  - already available, or
  - still intended but not yet built

### 6.2 The frontend docs assume live row refresh and polling, but no backend support is documented or implemented

Docs mention:

- live state refresh
- polling
- row-level transitions

Current backend:

- no queue status endpoint
- no background job abstraction
- no polling-specific contract

Doc impact:

- This should be expressed as a frontend expectation or target behavior, not as a backend capability that already exists

### 6.3 File upload size is configured but not actually enforced at the upload route

Current backend:

- `MAX_UPLOAD_SIZE_MB` is required and parsed in config
- upload endpoint does not check file size before saving

Evidence:

- `app/config.py`
- `app/api/applications.py`

Doc impact:

- If upload limits matter to frontend behavior, the docs should distinguish between configured intent and enforced runtime behavior

---

## 7. Auth And Config Consistency Gaps

### 7.1 JWT settings are documented/configured more strictly than runtime actually uses

Current backend:

- config validates `JWT_ALGORITHM`
- config validates `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- auth runtime ignores both and hardcodes:
  - algorithm: `HS256`
  - expiry: 1 day

Evidence:

- `app/config.py`
- `app/auth/security.py`

Doc impact:

- If the docs describe configurable JWT behavior, that is not fully true today

### 7.2 Startup depends heavily on environment variables and exits hard on config problems

Current backend:

- `Settings()` validates env at import time
- config errors call `sys.exit(1)`

Evidence:

- `app/config.py`

Doc impact:

- If the docs are meant to support onboarding or local setup, they should mention that startup is config-strict and import-time validated

---

## 8. Testing And Validation Gaps

### 8.1 The current test suite is stale relative to the codebase

Observed failures:

- tests reference removed module `app.agents.timeline_builder`
- tests import removed or renamed canonical types such as `ProfileMeta`
- tests expect removed LLM API `generate_interview_prep`
- tests expect removed policy API `validate_synthesis_output`

Evidence:

- `tests/test_agents.py`
- `tests/test_canonical.py`
- `tests/test_llm_client.py`
- `tests/test_policy.py`

Doc impact:

- If the docs mention tests as a confidence signal, they should note that the suite currently does not reflect the present architecture

### 8.2 Default `pytest -q` also picks up junk outside the active test suite

Observed failures during broad collection:

- import-path issues
- binary log files under `retired/logs`
- outdated retired tests and scripts

Doc impact:

- If you add engineering docs later, include a "how to run only the active tests" section

### 8.3 What actually passed during validation

Passed:

- import of `app.main`
- Python bytecode compilation of `app/`

Failed:

- meaningful automated test verification of current backend behavior

Doc impact:

- The docs should avoid implying that the documented workflow is already validated by the existing test suite

---

## 9. Places Where The Docs Are Internally Strong

Even though they do not match the backend yet, the docs are internally coherent in these areas:

- clear role split between admin and interviewer
- strong page/state separation
- explicit state transition rules
- clear draft vs published distinction
- good visibility rules
- good UI behavior notes for loading and empty states

That means the main issue is not the docs conflicting with each other.
The main issue is the docs describing a future architecture that the backend has not implemented yet.

---

## 10. Recommended Documentation Decisions

To improve the three docs, decide which of these two modes you want:

### Option A: Keep them as target-state specs

If that is your goal, update the docs to say clearly:

- these docs describe the intended next backend/frontend contract
- current backend does not yet implement:
  - assignments
  - drafts
  - publish
  - queue-style async processing
  - admin/interviewer list and management endpoints

This turns the docs into roadmap/spec docs rather than misleading current-state docs.

### Option B: Rewrite them as current-state backend-aligned docs

If that is your goal, the docs would need to reflect that today:

- upload triggers immediate full processing
- there is no assignment workflow
- there are no drafts
- there is no publish gate
- the main stored final artifact is `synthesis_records`
- access is uploader/admin-based, not assignment-based

This would make the docs accurate, but it would remove the intended product workflow currently described.

---

## 11. Suggested Revisions Per Existing Doc

### `Frontend_Docs/backend_entity_model.md`

Should clarify:

- whether it is current-state or target-state
- that `assignments` and `drafts` do not exist yet
- that `synthesis_records` is still active in the current backend
- that current status values are not the documented state-machine values

### `Frontend_Docs/frontend_final_spec.md`

Should clarify:

- whether all listed states/actions are already backed by API support
- that Generate/Regenerate/Publish are not currently backend actions
- that admin/interviewer visibility rules are target-state only for now

### `Frontend_Docs/frontend_ui_flow.md`

Should clarify:

- that queue-style row transitions and async refresh behavior depend on future backend work
- that assignment and publish UX currently have no backend implementation
- that some pages are spec-only until list/assignment endpoints exist

---

## 12. Open Questions To Resolve In The Docs

These are not code bugs. They are product/documentation decisions that should be made explicit.

1. Are the three docs supposed to describe:
   - the backend as it exists today, or
   - the backend/frontend contract you want next?

2. Is the canonical split already considered stable enough to document as:
   - current persistence reality, with
   - future workflow layering still pending?

3. Should `pipeline_confidence` be treated as:
   - removed from the product model, or
   - still present internally but not important to UI flows?

4. Is upload intended to remain synchronous in the short term, or should the docs fully commit to queued async processing?

5. Do you want the docs to include a "current backend limitations" section so frontend work is not planned against endpoints that do not yet exist?

---

## 13. Bottom Line

The backend currently supports:

- auth
- upload
- deterministic extraction
- LLM signal/question generation
- canonical persistence
- final synthesis persistence
- simple application fetch

The docs currently describe:

- a richer workflow platform with staged ownership, assignment, drafts, and publish

So the primary documentation gap is:

> the three docs describe a target workflow architecture, while the current backend still implements an earlier single-shot processing architecture.

That distinction should be made explicit in the docs before they are used as a source of truth.
