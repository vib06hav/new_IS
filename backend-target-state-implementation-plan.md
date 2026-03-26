# Backend Target-State Implementation Plan

## Goal
Rebuild the backend from the current single-shot upload-and-process flow into the target-state workflow defined by [Frontend_Docs/backend_entity_model.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/backend_entity_model.md), [Frontend_Docs/frontend_final_spec.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/frontend_final_spec.md), [Frontend_Docs/frontend_ui_flow.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/frontend_ui_flow.md), and [Frontend_Docs/spec_gap_list_for_doc_revision.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/spec_gap_list_for_doc_revision.md).

## Scope
- Backend only: `app/`, `tests/`, migrations, and backend docs.
- `frontend/` and `base_frontend/` are mock/non-authoritative and must not drive implementation decisions.
- The three target docs plus the gap doc are the contract for entities, lifecycle, permissions, and API behavior.

## Tasks
- [ ] Task 1: Freeze the backend contract before implementation starts. Write one short backend ADR that declares this work backend-only, names the authoritative docs, lists the final lifecycle states, and locks the required endpoint surface. Verify: the ADR exists and every later schema, route, and permission rule traces back to it.

- [ ] Task 2: Replace the old persistence model with the target schema. Update [application.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/application.py) to use `status` instead of `pipeline_status`, expand statuses to `UPLOADED`, `PROCESSING`, `READY`, `FAILED`, `ASSIGNED`, `DRAFT`, `PUBLISHED`, and remove `pipeline_confidence`. Update [user.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/user.py) to add `name`. Add `assignments` and `drafts` models, retire or delete [synthesis_record.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/models/synthesis_record.py), and wire model exports. Verify: fresh migrations run cleanly, schema inspection shows the new tables/columns, and ORM metadata matches the intended target model.

- [ ] Task 3: Create the migration plan and cutover behavior explicitly. Decide whether dev data is reset or backfilled, whether `synthesis_records` is dropped immediately or temporarily bridged, and whether migration shims are needed for old API consumers during development. Verify: the migration approach is documented alongside the schema change and can be executed from a clean database without ambiguity.

- [ ] Task 4: Add reusable auth and authorization dependencies. Create route guards for admin-only access, interviewer-only access, and assignment-based interviewer access. Update JWT runtime behavior so [security.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/security.py) uses configured algorithm and expiry values instead of hardcoded ones. Verify: auth tests prove role blocking and ownership enforcement, and token creation/validation reflects config values.

- [ ] Task 5: Split upload from synthesis and enforce the real lifecycle. Refactor [applications.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py) and [orchestrator.py](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/orchestrator.py) so upload persists `UPLOADED`, runs only deterministic extraction/canonical generation, and transitions to `READY` or `FAILED`. Move Pages 4-5 synthesis out of upload-time and into the interviewer generation stage. Verify: one application can move through `UPLOADED -> PROCESSING -> READY`, failure lands in `FAILED`, and retry can re-enter the deterministic path.

- [ ] Task 6: Build the admin API surface around the new state model. Add admin endpoints for application list/detail, retry, assign, reassign, interviewer listing, interviewer deletion/reset, and assignment listing. Enforce valid state transitions such as assign only from `READY`, retry only from `FAILED`, and reassignment behavior that discards draft state when the spec requires it. Verify: endpoint tests cover success cases, blocked transitions, and reassignment/removal side effects.

- [ ] Task 7: Build the interviewer workflow API surface. Add interviewer endpoints for assigned-application listing, draft generation/regeneration, and publish. Persist Pages 4-5 output in `drafts`, increment draft versions on regenerate, expose only the latest applicable draft, and block further generation after publish. Verify: one assigned application can move `ASSIGNED -> DRAFT -> DRAFT -> PUBLISHED` with correct version increments and publish lockout.

- [ ] Task 8: Redesign response schemas around role-based visibility. Replace the old one-size-fits-all `synthesis` response shape with admin list/detail responses, interviewer list/detail responses, and state-aware payloads. Admin must never see Pages 4-5 draft content before publish; interviewers must see only their assigned applications; published content must become visible to admin only after publish. Verify: schema tests and API tests confirm field-level visibility for `READY`, `ASSIGNED`, `DRAFT`, and `PUBLISHED`.

- [ ] Task 9: Remove legacy backend assumptions so the new workflow is the only source of truth. Delete or retire inline legacy statuses (`processing`, `complete`, `failed`), uploader-based ownership logic, `synthesis_records` usage, and any upload-time code path that still writes final synthesis output. Preserve deterministic extraction/canonical logic, but invoke it only in the correct stage. Verify: code search across `app/` finds no active legacy state or ownership assumptions outside intentional migration shims.

- [ ] Task 10: Rebuild the backend test suite around the new architecture. Delete or retire stale tests that reference removed modules or obsolete API contracts, keep only still-relevant auth/security coverage, and add focused tests for schema integrity, lifecycle transitions, auth guards, admin APIs, interviewer APIs, draft versioning, publish rules, and role-based visibility. Verify: there is one documented backend-only test command and it passes from a clean environment.

- [ ] Task 11: Run final verification and publish a backend handoff note for the future frontend. Execute migrations, backend tests, and one manual end-to-end smoke path covering register, login, upload, assign, generate, regenerate, publish, and role-aware detail fetches. Then write a short backend contract summary listing final endpoints, statuses, permissions, response-shape rules, and explicit non-goals. Verify: migration command passes, backend test command passes, smoke behavior matches the target docs, and the handoff note exists.

## Verification Detail

### Schema and Migration Checkpoints
- Run `alembic upgrade head` on a fresh database.
- Import the application package successfully after migration.
- Confirm `users.name`, `applications.status`, `assignments`, and `drafts` exist with expected constraints.

### API and Lifecycle Checkpoints
- Upload ends at canonical-ready state, not published synthesis.
- Retry is allowed only for failed applications.
- Assign/reassign enforce role and state guards.
- Generate creates draft version 1, regenerate increments to version 2+, publish freezes the app.

### Visibility Checkpoints
- Admin detail before publish contains canonical data only.
- Assigned interviewer detail contains canonical data plus latest draft when applicable.
- Unassigned interviewers cannot read or mutate another interviewer's applications.

### Suggested Final Test Command
```powershell
PYTHONPATH=. pytest tests -q
```

### Suggested Manual Smoke Path
1. Register an admin user with `name`.
2. Register an interviewer user with `name`.
3. Log in as admin.
4. Upload one PDF and confirm the resulting application becomes `READY`.
5. Assign the application to the interviewer and confirm it becomes `ASSIGNED`.
6. Log in as the interviewer and confirm `GET /me/applications` shows only that application.
7. Generate a draft and confirm status `DRAFT`, version `1`.
8. Generate again and confirm version `2`.
9. Fetch application detail as admin and confirm draft Pages 4-5 are still hidden.
10. Publish as interviewer and confirm status `PUBLISHED`.
11. Fetch application detail as admin and confirm published Pages 4-5 are now visible.
12. Attempt another generate after publish and confirm it is rejected.

## Done When
- [ ] The backend persists and enforces `UPLOADED`, `PROCESSING`, `READY`, `FAILED`, `ASSIGNED`, `DRAFT`, and `PUBLISHED`.
- [ ] `assignments` and `drafts` are the ownership and synthesis source of truth.
- [ ] Upload no longer performs final Pages 4-5 synthesis inline.
- [ ] Admin and interviewer APIs enforce the documented permissions and visibility rules.
- [ ] Admin cannot see draft Pages 4-5 content before publish.
- [ ] Interviewers can act only on their own assigned applications.
- [ ] Legacy single-shot assumptions are removed or isolated behind deliberate migration shims.
- [ ] The active backend test suite passes and reflects the new architecture.

## Notes
- Critical path: contract freeze -> schema/migration -> auth guards -> lifecycle split -> admin APIs -> interviewer APIs -> visibility refactor -> legacy cleanup -> test rebuild -> final verification.
- Best execution baseline: use the more detailed phase structure from Claude's plan, but keep this document's contract-first guardrails as the source of decision-making.
- Safest implementation strategy: preserve deterministic extraction/canonical generation and move only Pages 4-5 synthesis from upload-time to interviewer-time.
