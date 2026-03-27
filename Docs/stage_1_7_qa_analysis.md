# Stage 1.7 QA Analysis and Action Plan

## Summary

This document captures the non-LLM QA findings from the current implementation and translates them into an implementation-focused remediation plan.

The QA pass covered:

- auth behavior
- upload behavior
- deterministic ready-state behavior
- assignment and reassignment
- interviewer access behavior
- admin/interviewer UI rendering
- non-LLM paths only

The overall result is:

- core deterministic upload and assignment behavior works
- backend/frontend contract drift is visible in the review experience
- there are meaningful security, validation, and UX-safety gaps

---

## 1. Tested Scope

The QA pass covered the following runtime surfaces.

### API scope

- `POST /auth/login`
- `POST /auth/register`
- `GET /health`
- `POST /applications/upload`
- `GET /applications`
- `GET /applications/{id}`
- `POST /applications/{id}/assign`
- `PUT /applications/{id}/assign`
- `GET /assignments`
- `GET /users/interviewers`
- `DELETE /users/{id}`
- `GET /me/applications`

### Frontend scope

- admin login
- interviewer login
- wrong-role login handling
- interviewer creation
- interviewer deletion
- PDF upload from admin UI
- reports page assignment/reassignment
- assignments page visibility
- admin detail page rendering
- interviewer dashboard visibility
- interviewer detail access without generation

### Data scope

- multiple sample PDFs from `tests/pdfs`
- real `READY` transitions from deterministic processing
- real assignment/reassignment state changes

### Explicit exclusions

- no LLM generation execution
- no draft generation behavior
- no publish path execution

---

## 2. Observed Working Behavior

The following behaviors were verified as working in the current system:

- Health endpoint responds successfully.
- Deterministic pipeline runs on upload.
- Sample PDFs uploaded during testing reached `READY`.
- Canonical content is returned in detail API responses.
- Admin assignment works.
- Admin reassignment works.
- `/assignments` reflects current assignment state.
- Interviewer `GET /me/applications` returns assigned items.
- Wrong-role login shows a role-mismatch error in the UI.
- Unauthorized access to protected list endpoints returns `401`.

Additional verified details:

- deterministic agent chain was observed in API logs during upload processing
- canonical data persisted before the LLM boundary
- admin detail pages displayed canonical-derived content

---

## 3. Findings Table

| Severity | Finding | Observed behavior | Expected behavior | Recommended action |
| --- | --- | --- | --- | --- |
| High | Open registration / role creation risk | `POST /auth/register` allows unauthenticated creation of users, including `role: admin` | Privileged account creation must be restricted to authenticated, authorized flows | Lock registration behind an admin-only interviewer-creation path; block anonymous privileged role creation |
| Medium | Malformed PDF causes raw 500 | A fake file with `.pdf` name returned `500 Internal Server Error` on upload | Invalid upload content should return controlled validation failure, not generic 500 | Add real file-content validation and map parser failures to structured 4xx/controlled failure states |
| Medium | Destructive interviewer deletion behavior | Removing an interviewer can reset applications to `READY` and delete drafts | Destructive actions should be explicit, reviewed, and user-confirmed | Add confirmation, impact preview, and explicit post-delete behavior messaging |
| Medium | Stale success/error banner state | Admin pages can retain old success or error messages across later actions | Status banners should reflect the latest action only | Reset message and error state consistently at action boundaries |
| Medium | Ready-state UI exposes canonical JSON instead of Pages 1-3 | Admin and interviewer detail pages render canonical JSON in a generic JSON viewer | Ready/assigned users should see ROS Pages 1-3 review artifact | Replace canonical JSON UI with Pages 1-3 rendering contract |
| Medium | No raw PDF access in tested review flows | PDF is stored server-side but not surfaced in admin/interviewer review UI | Admin and interviewer should be able to inspect the source PDF | Add PDF access to review detail flows |
| Low | Interviewer dashboard timing/hydration sensitivity | Browser checks showed transient timing sensitivity before assigned items visibly appeared | Dashboard should present assigned work reliably with clear loading behavior | Harden loading/polling behavior and test hydration-sensitive cases |
| Low | Backend/frontend success timing mismatch risk | Backend assignment visibility was correct even when browser timing briefly obscured it | Frontend should reflect backend state reliably after assignment/reassignment | Tighten dashboard refresh/polling and post-login/post-mutation synchronization |

---

## 4. Error Handling Analysis

This section describes how errors are currently handled and where behavior is weak.

### A. Where backend returns structured `detail`

The backend already returns explicit `detail` messages for many policy and auth cases, including:

- auth failures
- unauthorized access
- assignment conflicts
- interviewer deletion conflicts
- role mismatch cases enforced server-side

This is good because the frontend error parser in `frontend/lib/api.ts` can surface those messages directly.

### B. Where frontend parses and surfaces errors correctly

The frontend central request helper:

- parses `detail` when it is a string
- flattens validation arrays
- falls back to HTTP status text otherwise

This works well for:

- login failures
- role mismatch errors
- assignment/reassignment errors
- interviewer deletion conflicts

### C. Where backend leaks generic 500s

Malformed upload content currently produces a raw `500 Internal Server Error`.

Observed behavior:

- filename suffix validation exists
- content-level validation is not sufficiently controlled
- parser failure bubbles into a generic server error

Why it matters:

- admins cannot distinguish user error from system failure
- retries become guesswork
- upload queue semantics become less trustworthy

### D. Where UI has no confirmation or guardrail

The current UI lacks confirmation before:

- interviewer deletion

This is risky because backend delete behavior can:

- remove assignments
- reset application state
- delete drafts

The UI currently offers no impact preview before executing the action.

### E. Where messages are accurate but state handling is weak

Several admin pages correctly show success or error banners, but they do not consistently clear stale state before a new action.

Risk:

- users can see an old success message after a later failure
- users can see an old error after a later success

### F. Where silent early returns happen

Several frontend actions return early when token/session is missing.

This avoids crashes, but it also means:

- no user-facing recovery hint
- no forced redirect from action handlers
- no explicit explanation of why the action did nothing

### G. Likely failure classes that implementation must handle cleanly

- auth failure
- role mismatch between portal and account
- missing or expired session
- bad upload content
- failed deterministic extraction
- ready-state/backend-contract mismatch
- reassignment during active work
- destructive interviewer deletion with linked state
- UI polling or hydration timing delay
- backend success with delayed frontend visibility

---

## 5. Action Plan

Priorities are ordered by implementation urgency.

### P0 - Security and integrity

1. Secure registration path.
2. Block anonymous privileged account creation.
3. Introduce a dedicated admin-owned interviewer creation workflow.

Rationale:

- this is the only verified security-critical issue from the current QA pass
- it affects trust boundaries, not just UX

### P1 - Workflow contract alignment

1. Replace canonical-JSON review UI with ROS Pages 1-3 review artifact.
2. Surface raw PDF access in admin and interviewer review flows.
3. Persist the deterministic review package after upload:
   - canonical
   - deterministic signals
   - ROS Pages 1-3
   - raw PDF handle/reference

Rationale:

- this resolves the major architecture/product drift observed in testing
- it aligns human review surfaces with intended workflow semantics

### P1 - Robustness and controlled failures

1. Validate file content, not just `.pdf` suffix.
2. Return controlled validation failures for malformed uploads.
3. Make deterministic pipeline failure states explicit and user-readable.
4. Ensure retry messaging clearly distinguishes:
   - parser failure
   - infrastructure failure
   - invalid user input

### P2 - UX safety and consistency

1. Add confirmation before destructive interviewer deletion.
2. Show impact warning if deletion will reset assignments or discard drafts.
3. Clear banner state at the start of each new action.
4. Improve interviewer dashboard loading/empty/error states to reduce timing confusion.

### P2 - QA hardening

Add automated tests for:

- auth and role enforcement
- privileged registration blocking
- upload validation
- ready-state review contract
- assignment/reassignment visibility
- interviewer deletion behavior
- interviewer dashboard visibility after assignment
- raw PDF visibility in review flows

---

## 6. Regression Test Plan

The following scenarios should become required regression coverage.

### A. Upload and deterministic processing

1. Upload valid PDF -> deterministic pipeline runs -> application becomes `READY`.
2. `READY` application has persisted deterministic review package.
3. Admin ready-state detail shows Pages 1-3, not canonical JSON.

### B. Upload validation and failure handling

1. Upload fake file named `.pdf` -> controlled 4xx or explicit structured failure, not raw 500.
2. Deterministic extraction failure -> application moves to `FAILED` with clear retry semantics.

### C. Auth and role enforcement

1. Anonymous registration attempt for privileged role is blocked.
2. Interviewer portal rejects admin login cleanly.
3. Admin portal rejects interviewer login cleanly.
4. Missing token on protected endpoints returns `401`.

### D. Assignment and interviewer access

1. Admin assigns interviewer -> interviewer sees assigned application.
2. Admin reassigns assigned application -> new interviewer sees it, old interviewer loses access.
3. Reassignment during draft state follows explicit reset/discard policy.

### E. Review artifact contract

1. Admin sees raw PDF + Pages 1-3 pre-publish.
2. Interviewer sees raw PDF + Pages 1-3 pre-generation.
3. Interviewer generation uses backend deterministic state and does not require canonical JSON in UI.
4. Admin does not see draft Pages 4-5 before publish.

### F. Publish visibility boundary

1. Published path preserves role visibility rules.
2. Final review artifact remains stable after publish.

---

## Evidence Summary

The findings in this report are grounded in:

- runtime API checks
- runtime browser checks
- deterministic upload behavior using sample PDFs
- direct inspection of current API schemas and detail builders
- observed server logs during deterministic processing

This report intentionally avoids speculative fixes. Every action item maps back to a verified behavior gap, a verified failure mode, or a code-backed contract mismatch.

---

## Assumptions

- This document is for implementation agents and engineering handoff.
- No code changes are part of this document creation step.
- Non-LLM behavior only was tested directly.
- The drift between canonical review and Pages 1-3 review is treated as a product-contract issue, not merely a cosmetic frontend issue.
