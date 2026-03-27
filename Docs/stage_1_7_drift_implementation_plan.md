# Stage 1.7 Drift Fix Implementation Plan

## Summary

This document is a drift-remediation implementation plan only. It does not cover QA hardening, security remediation, or broader product cleanup except where those are required to eliminate the deterministic review-flow drift already identified in `Docs/stage_1_7_drift_report.md`.

The objective is to realign the system so that:

- upload processing produces a persisted deterministic review package
- admin and interviewer pre-generation workflows consume that review package
- ROS Pages 1-3 become the visible review artifact
- canonical and deterministic signals remain backend-owned inputs for Pages 4-5 generation

This plan is decision-complete and is intended to be executable by another agent or engineer without further product decisions.

---

## 1. Target Contract

The target contract after this implementation is:

1. Upload a PDF.
2. Run deterministic extraction immediately.
3. Persist a deterministic review package containing:
   - raw PDF reference/access handle
   - canonical
   - deterministic signals
   - ROS Pages 1-3
4. Mark the application `READY`.
5. Admin review detail shows:
   - raw PDF access
   - ROS Pages 1-3
6. Assignment gives interviewer access to:
   - raw PDF access
   - ROS Pages 1-3
7. Pages 4-5 generation uses persisted deterministic backend state:
   - canonical
   - deterministic signals
   - optionally persisted Pages 1-3 context if helpful
8. Canonical JSON is not the default visible UI artifact for admin or interviewer pre-generation review.

---

## 2. Scope Boundaries

### In scope

- backend persistence changes needed to store the deterministic review package
- backend API contract changes for ready/assigned review flows
- backend generation-path wiring changes needed to consume persisted deterministic state
- frontend changes needed to replace canonical JSON review with Pages 1-3 review artifact
- frontend changes needed to surface raw PDF access in admin and interviewer detail views
- published/draft visibility alignment where needed to support the review contract

### Out of scope

- registration/auth remediation
- malformed upload validation and 500-to-4xx cleanup
- destructive action confirmations
- banner-state cleanup
- dashboard polling robustness
- non-drift QA automation expansion

Those belong to the later QA/remediation phase.

---

## 3. Implementation Decisions

The following implementation decisions are fixed for this plan.

### A. Source of truth

- Canonical remains the deterministic source of truth.
- ROS Pages 1-3 are a persisted deterministic review artifact derived from canonical.
- Deterministic signals are persisted immediately after deterministic processing succeeds.

### B. Persistence model

Persist a single deterministic review package per application containing:

- `canonical`
- `deterministic_signals`
- `pages_1_3`
- `pdf_access` metadata or an equivalent backend-owned PDF handle

The implementation may use:

- a new table, or
- an extension of existing persistence structures

but the externally observable behavior must be the same:

- the review package exists and is retrievable for every `READY`, `ASSIGNED`, and `DRAFT` application
- it is not recomputed on every review-page request

### C. Review contract separation

Define distinct contract families:

- list contract:
  - id
  - status
  - assigned interviewer summary
  - created timestamp
- review detail contract:
  - metadata
  - raw PDF access
  - ROS Pages 1-3
  - role-appropriate visibility fields
- generation backend contract:
  - canonical
  - deterministic signals
  - any needed deterministic review package content
- published contract:
  - final Pages 1-5 representation

### D. UI artifact rule

- Admin and interviewer pre-generation review UIs render ROS Pages 1-3.
- They do not render canonical JSON by default.
- Canonical remains backend-available for generation and debugging, but is not the primary review surface.

### E. Visibility rules

Admin:

- `READY`: raw PDF + Pages 1-3
- `ASSIGNED`: raw PDF + Pages 1-3
- `DRAFT`: raw PDF + Pages 1-3 + draft status only
- `PUBLISHED`: final published Pages 1-5

Interviewer:

- `ASSIGNED`: raw PDF + Pages 1-3
- `DRAFT`: raw PDF + Pages 1-3 + latest draft
- `PUBLISHED`: published view according to current final-report policy

Admin must not see draft Pages 4-5 pre-publish.

---

## 4. Backend Work Plan

### Phase 1 - Persist the deterministic review package

Add deterministic-package persistence to the post-upload deterministic path.

Required behavior:

- after canonical assembly completes successfully
- derive deterministic signals without waiting for LLM generation
- derive ROS Pages 1-3 deterministically
- persist the deterministic review package before returning `READY`

Implementation details:

- move deterministic signal generation into the ready-state persistence path, not only the later synthesis path
- ensure the Pages 1-3 projection is persisted at the same lifecycle point
- keep canonical persistence behavior intact
- bind the package to application id as a one-to-one deterministic review artifact

Recommended implementation order:

1. Create or extend persistence structure for review package.
2. Update orchestrator deterministic path to produce:
   - canonical
   - deterministic signals
   - Pages 1-3
3. Persist all three in one deterministic save flow.
4. Keep `READY` transition dependent on successful review-package persistence.

### Phase 2 - Add review-oriented backend detail contracts

Change admin and interviewer application detail flows so they return review-oriented payloads.

Admin detail payload must include:

- application id
- status
- created_at
- assigned interviewer summary
- raw PDF access handle
- Pages 1-3 object
- published draft only when `PUBLISHED`
- no draft body pre-publish

Interviewer detail payload must include:

- application id
- status
- created_at
- assigned interviewer summary
- raw PDF access handle
- Pages 1-3 object
- latest draft when present

Implementation details:

- update response schemas
- update helper builders
- update detail endpoints
- keep list endpoints unchanged except where they need additional summary fields

### Phase 3 - Add backend PDF access path

Provide a backend-owned PDF access mechanism for admin and interviewer review flows.

Required behavior:

- admin can fetch/view the source PDF for applications they are allowed to review
- interviewer can fetch/view the source PDF only for applications assigned to them
- frontend receives a safe access handle or URL
- raw filesystem paths are never exposed

Implementation details:

- add an authenticated PDF-serving endpoint or tokenized access path
- enforce role/assignment checks in the PDF access path
- attach PDF access metadata to review detail responses

### Phase 4 - Rewire Pages 4-5 generation to use persisted deterministic state

The generation path must no longer rely on ad hoc reconstruction from the canonical-only review contract.

Required behavior:

- generation loads canonical from persisted deterministic state
- generation loads deterministic signals from persisted deterministic state
- generation executes Pages 4-5 synthesis using persisted deterministic inputs

Implementation details:

- update generation pipeline entry to load persisted deterministic signals
- do not require the frontend to send Pages 1-3 or canonical back to the server
- preserve current draft/publish state semantics unless they conflict with the drift target

Default:

- canonical remains source of truth
- deterministic signals are loaded from persistence
- Pages 1-3 persistence is for review and consistency, not to replace canonical as source of truth

---

## 5. Frontend Work Plan

### Phase 5 - Replace canonical JSON review with Pages 1-3 rendering

Update admin and interviewer application detail pages so they render Pages 1-3 instead of generic canonical JSON.

Required behavior:

- remove canonical JSON as the default review presentation
- render a Pages 1-3 UI model aligned with the ROS structure
- keep draft and published behaviors role-appropriate

Implementation details:

- replace `JsonSection` usage for pre-generation review payloads
- introduce explicit review components for:
  - Page 1 background/profile
  - Page 2 academics and engagement
  - Page 3 essays
- use backend-provided review detail contract directly

### Phase 6 - Surface raw PDF access in detail pages

Add raw PDF access controls to:

- admin detail page
- interviewer detail page

Required behavior:

- source PDF is accessible alongside Pages 1-3
- source PDF access is role/assignment compliant

Default UI behavior:

- provide a “View PDF” or “Open Source PDF” control in both detail views
- keep PDF access in the review header area, not buried in debug sections

### Phase 7 - Preserve visibility boundaries

Update frontend rendering rules so that:

- admin never sees draft Pages 4-5 before publish
- interviewer sees latest draft only in `DRAFT`
- published flow shows final output according to current status rules

This phase is not about redesigning draft/publish semantics; it is only about aligning visible data with the intended contract.

---

## 6. API and Type Changes

The implementation must introduce or revise public/internal contracts in these areas:

### Backend schema/types

Add a persisted deterministic review package type containing:

- application identifier
- PDF access handle
- Pages 1-3 object
- deterministic signals
- canonical reference or canonical payload

### Admin detail response

Replace canonical-first admin detail with review-first admin detail:

- metadata
- assigned interviewer
- PDF access
- Pages 1-3
- published draft only when allowed

### Interviewer detail response

Replace canonical-first interviewer detail with review-first interviewer detail:

- metadata
- PDF access
- Pages 1-3
- latest draft when present

### Generation input boundary

Pages 4-5 generation must load persisted deterministic state by application id and must not depend on the frontend review payload as the generation source.

---

## 7. Acceptance Criteria

The drift fix is complete only when all of the following are true:

1. Every newly `READY` application has persisted:
   - canonical
   - deterministic signals
   - ROS Pages 1-3
   - PDF access reference

2. Admin detail API returns review-oriented payloads, not canonical-only payloads.

3. Interviewer detail API returns review-oriented payloads, not canonical-only payloads.

4. Admin UI renders ROS Pages 1-3 for pre-generation review.

5. Interviewer UI renders ROS Pages 1-3 for pre-generation review.

6. Admin can access the raw PDF from the detail view.

7. Interviewer can access the raw PDF from the detail view when assigned.

8. Pages 4-5 generation uses persisted deterministic backend state and does not depend on UI-visible canonical JSON.

9. Admin does not see draft Pages 4-5 before publish.

10. Assignment now effectively grants access to a deterministic review package, not just to canonical JSON on an application record.

---

## 8. Test Scenarios For Drift Fix Validation

These are implementation-completion checks for the drift fix itself.

### Upload and persistence

- upload valid PDF
- deterministic processing completes
- persisted review package exists
- application becomes `READY`

### Admin review path

- open admin detail for `READY`
- Pages 1-3 render
- raw PDF opens
- canonical JSON is not the primary review surface

### Assignment handoff

- assign interviewer to `READY` application
- interviewer gains access to the same review package
- admin still sees Pages 1-3 and PDF, but not draft content

### Interviewer review path

- open interviewer detail for assigned application
- Pages 1-3 render
- raw PDF opens
- generation controls remain available

### Generation backend dependency

- invoke Pages 4-5 generation after assignment
- backend loads canonical and deterministic signals from persisted state
- no frontend-provided canonical payload is required

---

## 9. Defaults and Assumptions

- This plan intentionally excludes non-drift QA fixes.
- This plan does not prescribe the exact storage schema so long as the runtime contract is satisfied.
- The implementation should prefer minimal architectural change consistent with the drift target.
- Existing list/status flows should remain stable unless a change is required to support the review-package contract.
- Canonical remains the authoritative deterministic source of truth even after Pages 1-3 are persisted separately.
