# Stage 1.7 QA Analysis and Action Plan

## Summary

This document captures the post-drift-fix QA findings for the current implementation and translates them into an implementation-focused remediation plan.

Status update as of 2026-03-27:

- anonymous privileged registration has been blocked
- admin interviewer creation now uses an authenticated admin-only endpoint
- malformed fake-PDF uploads now return a controlled validation error instead of a raw `500`
- source-PDF opening now uses an authenticated browser flow instead of a plain unauthenticated anchor
- interviewer deletion now blocks while active assignments exist, and the admin UI asks for confirmation before removal
- stale mutation banners were cleared in the affected admin/interviewer flows
- frontend local QA now has a `npm run dev:clean` recovery path for stale `.next` state

One follow-up remains outside the product-path fixes:

- dedicated automated browser regression coverage has now been added under `frontend/e2e`

This rerun was executed after the review-package drift work landed. A full browser regression was run against a fresh frontend dev session on `http://localhost:3002`, with supporting API verification against the running backend. The major workflow-contract drift that previously affected ready-state review has been corrected in the current build:

- upload now persists a deterministic review package
- admin/interviewer detail APIs return `review_package`
- raw PDF access is now available through a guarded endpoint
- assigned interviewer access now aligns with the review-package model

The current QA result is:

- the drift fix is materially working
- core deterministic review workflow now matches the intended contract much more closely
- the main remaining issues are now:
  - anonymous privileged registration
  - malformed upload handling
  - broken raw-PDF link behavior in the browser UI
  - destructive interviewer deletion
  - stale success/error banners

---

## 1. Tested Scope

The rerun covered the following runtime surfaces.

### API scope

- `POST /auth/login`
- `POST /auth/register`
- `GET /health`
- `GET /applications`
- `POST /applications/upload`
- `GET /applications/{id}`
- `GET /applications/{id}/source-pdf`
- `POST /applications/{id}/assign`
- `GET /me/applications`
- `GET /users/interviewers`
- `DELETE /users/{id}`

### Review-workflow scope

- valid PDF upload after drift fix
- invalid fake-PDF upload through the real admin upload UI
- persisted review package on newly uploaded applications
- review package on previously existing applications
- admin detail access to review package
- interviewer detail access to review package
- real browser interaction with admin and interviewer portals
- wrong-role login rejection in both admin and interviewer portals
- interviewer creation and duplicate-create handling in the real browser UI
- raw PDF access control for assigned and unassigned interviewers
- browser behavior of the source-PDF link
- reassignment visibility across old and new interviewers
- destructive interviewer deletion impact on assigned applications

### Frontend/code-path scope

- admin detail page consumes `review_package`
- interviewer detail page consumes `review_package`
- review package component renders Pages 1-3 and source PDF link
- frontend production build after contract change
- clean frontend browser regression on a fresh Next dev session
- unstable route behavior observed on a stale frontend dev session

### Explicit exclusions

- no LLM generation execution
- no publish-path execution

---

## 2. Observed Working Behavior

The following behaviors were verified as working in the current system:

- Health endpoint responds successfully.
- Valid sample PDFs from `tests/pdfs` still upload successfully and reach `READY`.
- Newly uploaded applications persist deterministic review state:
  - canonical
  - deterministic signals
  - ROS Pages 1-3
- Existing applications without an explicit persisted review package still return a usable `review_package` via fallback derivation.
- Admin detail responses now return `review_package`, not `canonical`.
- Interviewer detail responses now return `review_package`, not `canonical`.
- Assigned interviewer `GET /me/applications` returns assigned work correctly.
- Assigned interviewer can access the guarded raw PDF endpoint when requests include bearer auth.
- Unassigned interviewer receives `403` on the guarded raw PDF endpoint.
- Admin assignment still works after the drift fix.
- Admin reassignment works.
- Old interviewer loses access after reassignment.
- New interviewer gains access after reassignment.
- Frontend production build succeeds with the new review-package contract.
- Clean browser login and review flows work on a fresh frontend session on port `3002`.
- Admin portal rejects interviewer credentials cleanly.
- Interviewer portal rejects admin credentials cleanly.
- Admin can create interviewers from the browser UI.
- Admin can assign and reassign applications from the browser UI.

Additional verified details:

- `GET /applications/{id}` returned `review_package.pdf_url` and structured `pages_1_3`
- `GET /applications/{id}/source-pdf` returned `200` for an assigned interviewer
- `GET /applications/{id}/source-pdf` returned `403` for a different interviewer
- browser-based assignment, reassignment, and interviewer visibility transitions worked correctly
- deleting an assigned temporary interviewer reset the linked application back to `READY` and cleared the assignment
- the fresh browser regression covered login -> upload -> assign -> review -> reassign -> delete

---

## 3. Findings Table

| Severity | Finding | Observed behavior | Expected behavior | Recommended action |
| --- | --- | --- | --- | --- |
| High | Open registration / privileged role creation still exposed | `POST /auth/register` still allows anonymous creation of both `role: admin` and `role: interviewer` | Privileged or internal-role account creation must require authenticated, authorized admin flow | Remove anonymous privileged registration; replace with admin-owned interviewer creation path |
| High | Raw PDF link is broken in the actual browser UI | Clicking `Open source PDF` from both admin and interviewer detail pages produced `401 Not authenticated` in a popup, even though the protected API works with bearer auth | Admin and interviewer should be able to open the source PDF from the UI they are using | Replace the plain anchor with an authenticated fetch/download flow or move auth to a transport the browser navigation can send |
| Medium | Malformed PDF still causes raw 500 | Uploading a fake file with `.pdf` name still returned `500 Internal Server Error`; logs show parser exception bubbling from layout extraction | Invalid upload content should return controlled validation failure, not generic 500 | Add content validation and map parser failures to structured 4xx or explicit handled failure response |
| Medium | Interviewer deletion remains destructive | Deleting an interviewer who owned an assigned application reset that application to `READY` and removed the assignment | Destructive state resets should be explicit, reviewed, and user-confirmed | Add confirmation, impact preview, and explicit post-delete behavior messaging |
| Medium | Stale success/error banner behavior is confirmed in browser | After a successful interviewer creation, a duplicate create attempt still left the old `Interviewer created.` banner visible alongside the later failure state | Status banners should reflect the latest action only | Clear message and error state consistently at mutation boundaries |
| Low | Frontend dev-session stability is weak under stale build state | During QA, an older frontend session began serving `500` on routes such as `/interviewer/login`, `/admin/reports`, and `/admin/upload` with missing-module errors from `.next` output; a clean fresh session recovered the routes | Local QA/dev sessions should remain stable across route navigation without requiring a fresh dev restart | Investigate Next dev/build artifact stability and ensure stale `.next` state does not break route loading during QA |

### Previously reported drift findings that are now resolved

- Ready-state UI/API no longer exposes canonical as the review contract.
- Raw PDF access now exists for admin and assigned interviewer flows.
- Admin/interviewer review access now centers on ROS Pages 1-3 review package semantics.

---

## 4. Error Handling Analysis

This section describes how errors are currently handled and where behavior is still weak in the post-drift-fix build.

### A. Where backend returns structured `detail`

The backend still returns explicit `detail` messages for many auth and policy cases, including:

- auth failures
- unauthorized access
- assignment authorization failures
- interviewer access denials
- protected PDF endpoint access denial

This remains a strong point because the frontend request helper can surface those messages directly.

### B. Where frontend parses and surfaces errors correctly

The shared request helper in `frontend/lib/api.ts` still:

- parses `detail` when it is a string
- flattens validation-array responses
- falls back to HTTP status text otherwise

This continues to work well for:

- login failures
- authorization failures
- assignment conflicts
- access denial on protected resources

### C. Where backend still leaks generic 500s

Malformed upload content still produces a raw `500 Internal Server Error`.

Observed behavior:

- filename suffix validation exists
- content-level validation remains insufficient
- parser failure still escapes as a generic server error

Why it matters:

- admins cannot distinguish invalid input from platform failure
- retries remain guesswork
- failure handling around upload is still too opaque for operations

### D. Where UI has no confirmation or guardrail

The destructive interviewer deletion behavior is still risky at the system level.

Observed behavior:

- deleting an assigned interviewer reset the linked application to `READY`
- assignment ownership was removed immediately

Why it matters:

- work routing can change in one click
- assignment state is discarded without an explicit confirmation contract
- this remains a safety issue even though the review-package drift itself is fixed

### E. Where the UI contract is still broken even though the API contract is fixed

The source-PDF flow is now correct at the API level but broken at the browser level.

Observed behavior:

- the detail payload exposes `review_package.pdf_url`
- the UI renders this as a plain anchor
- auth is stored in localStorage as a bearer token
- browser navigation to the plain anchor does not send that bearer token
- result: both admin and interviewer see `401 Not authenticated` when clicking `Open source PDF`

Why it matters:

- product behavior still does not satisfy the intended “admin/interviewer can inspect raw PDF” workflow
- API-only QA can miss this because the endpoint itself works when called with explicit auth headers
- this is now a high-priority UI/API integration defect

### F. Where message handling is weak

This is no longer just an inferred risk. Browser QA reproduced it directly.

- an old success message can survive into a later failure path
- an old error can survive into a later success path

### G. Likely failure classes that implementation must still handle cleanly

- anonymous privileged registration
- missing or expired session
- role mismatch between portal and account
- bad upload content
- deterministic extraction failure
- authenticated browser navigation to protected raw assets
- destructive interviewer deletion with linked state
- stale mutation banners
- stale frontend build/runtime state in QA/dev sessions
- backend success with delayed or ambiguous frontend visibility

---

## 5. Action Plan

Priorities are ordered by implementation urgency for the current post-drift state.

### P0 - Security and integrity

1. Secure the registration path.
2. Block anonymous privileged account creation.
3. Introduce a dedicated admin-owned interviewer creation workflow.

Rationale:

- this remains the most serious verified issue in the current build
- it crosses trust boundaries, not just UX boundaries

### P1 - Upload validation and controlled failure handling

1. Validate file content, not just `.pdf` suffix.
2. Return controlled validation failures for malformed uploads.
3. Distinguish parser failure from system failure in upload responses.
4. Ensure upload retry guidance is user-readable.

Rationale:

- this is the most important remaining workflow robustness gap after the drift fix

### P1 - Raw PDF browser access fix

1. Replace the plain source-PDF anchor with an authenticated browser flow.
2. Choose one contract and standardize it:
   - use cookie/session auth for browser navigations
   - or fetch the PDF with bearer auth and open/download it client-side
   - or generate a short-lived authorized download URL
3. Re-test both admin and interviewer detail pages after the fix.

Rationale:

- this is the most important newly discovered user-facing regression from the thorough browser QA
- the intended feature exists at the API layer but is currently broken in the actual UI

### P1 - Destructive action safety

1. Add confirmation before interviewer deletion.
2. Show impact warning when deletion will reset assignments or discard owned work state.
3. Make reset behavior explicit in both UI copy and backend/API contract documentation.

Rationale:

- current delete behavior is operationally destructive even though it is technically functioning as implemented

### P2 - UX state consistency

1. Clear banner state at the start of each mutation.
2. Re-test admin/interviewer mutations in browser after the fix.
3. Tighten post-mutation refresh behavior so UI state is unambiguous.

### P2 - Frontend runtime stability

1. Investigate the intermittent route `500`s observed in a stale frontend dev session.
2. Determine whether the problem comes from:
   - Next dev artifact invalidation
   - local `.next` corruption
   - devtools/client-manifest instability
3. Make sure long-running QA sessions do not require a clean restart just to keep routes loading.

### P2 - Regression and QA hardening

Add automated coverage for:

- privileged registration blocking
- malformed upload handling
- persisted review package after upload
- review-package detail responses for admin/interviewer
- raw PDF access control
- raw PDF browser-link behavior
- interviewer deletion side effects
- stale-banner sequences after mixed success/failure actions

---

## 6. Regression Test Plan

The following scenarios should now be the required regression set.

### A. Review package and ready-state processing

1. Upload valid PDF -> deterministic pipeline runs -> application becomes `READY`.
2. Newly uploaded `READY` application has persisted:
   - canonical
   - deterministic signals
   - ROS Pages 1-3
3. Admin detail response returns `review_package`.
4. Interviewer detail response returns `review_package`.
5. Existing pre-change records still resolve a usable review package.

### B. Raw PDF access control

1. Admin can access source PDF.
2. Assigned interviewer can access source PDF.
3. Unassigned interviewer receives `403`.
4. Browser UI `Open source PDF` action works for admin.
5. Browser UI `Open source PDF` action works for assigned interviewer.
6. Browser UI `Open source PDF` action returns the PDF document itself, not `401`.

### C. Upload validation and failure handling

1. Upload fake file named `.pdf` -> controlled 4xx or explicit handled failure, not raw 500.
2. Deterministic extraction failure -> application moves to `FAILED` with clear retry semantics.

### D. Auth and role enforcement

1. Anonymous registration attempt for privileged role is blocked.
2. Anonymous interviewer creation is blocked unless product explicitly intends open registration.
3. Interviewer portal rejects admin login cleanly.
4. Admin portal rejects interviewer login cleanly.
5. Missing token on protected endpoints returns `401`.

### E. Assignment and reviewer visibility

1. Admin assigns interviewer -> interviewer sees assigned application.
2. Assigned interviewer can fetch detail and source PDF.
3. Different interviewer cannot fetch guarded PDF.
4. Reassignment preserves expected visibility rules.

### F. Destructive interviewer deletion

1. Delete unassigned interviewer -> safe removal path.
2. Delete assigned interviewer -> behavior is explicit, confirmed, and documented.
3. If reset-to-`READY` remains the intended policy, UI must warn before executing it.

### G. Banner-state regression

1. Success followed by failure does not leave stale success visible.
2. Failure followed by success does not leave stale error visible.

### H. Frontend runtime stability

1. Long-running frontend dev session continues serving admin and interviewer routes without route-level `500`s.
2. Clean and stale sessions behave consistently enough for QA.

---

## Evidence Summary

The findings in this rerun are grounded in:

- runtime API checks against the post-drift-fix build
- live upload using sample PDFs from `tests/pdfs`
- live inspection of returned `review_package` payloads
- live verification of protected raw PDF access control
- live browser verification of the source-PDF link failure mode
- live browser verification of interviewer creation, assignment, reassignment, and delete flows
- live verification of destructive interviewer deletion side effects
- frontend production build and code-path inspection for the new review-package contract
- direct browser validation on a clean fresh frontend session on port `3002`
- observation of route instability on a stale frontend session
- direct API log inspection for malformed upload failure behavior

This report intentionally distinguishes between:

- issues that were fixed by the drift implementation
- issues that remain open afterward
- issues that only appear in a real browser even when the API itself looks correct

---

## Assumptions

- This document is for implementation agents and engineering handoff.
- No code changes are part of this document update step.
- No LLM generation behavior was executed in this rerun.
- The drift fix is considered functionally present in the current build.
- Browser-level interaction polish still needs a follow-up regression pass even though the API contract is now aligned.
