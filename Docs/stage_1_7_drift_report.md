# Stage 1.7 Drift Report and Implementation Plan

## Summary

This document captures the drift between the intended Stage 1.7 product contract and the current implementation. It is written for implementation agents and engineers, not for stakeholder presentation.

The key drift is that the current system exposes raw canonical JSON in the admin and interviewer review flows, while the intended system requires a deterministic review package composed of:

- raw PDF access
- canonical data
- deterministic signals
- rendered ROS Pages 1-3

At present, those layers are split across different parts of the backend pipeline and are not exposed as a coherent ready-state contract.

---

## 1. Intent Snapshot

The intended workflow is:

1. Admin uploads a PDF.
2. Deterministic agents run immediately after upload.
3. The backend persists a deterministic package containing:
   - raw PDF reference
   - canonical JSON
   - deterministic signals JSON
   - ROS Pages 1-3 projection
4. ROS Pages 1-3 are derived from canonical data and treated as the review artifact for human users.
5. Admin can view:
   - raw PDF
   - ROS Pages 1-3
6. Admin assigns the application to an interviewer.
7. Interviewer gains access to:
   - raw PDF
   - ROS Pages 1-3
8. Pages 4-5 are generated later using backend deterministic state:
   - canonical
   - deterministic signals
9. The interviewer-facing UI should not need to expose raw canonical JSON in order to complete Pages 4-5.

Important interpretation:

- ROS Pages 1-3 are the deterministic review artifact.
- Canonical JSON is a backend representation, not the intended primary UI representation.
- Deterministic signals are part of the persisted backend working state before LLM generation, not a late-only hidden pipeline artifact.

---

## 2. Current Implementation Snapshot

The current implementation behaves as follows:

- Upload triggers deterministic extraction inline in `app/api/applications.py`.
- The deterministic pipeline persists canonical data in `canonical_records`.
- The ready-state detail APIs for both admin and interviewer return `canonical`, not ROS Pages 1-3.
- The admin detail page renders `canonical.canonical_data` directly as formatted JSON.
- The interviewer detail page renders `canonical.canonical_data` directly as formatted JSON.
- Raw PDF files are stored on disk via `file_path`, but no tested admin/interviewer UI flow exposes the raw PDF.
- Deterministic signals exist in the Stage 1.7 synthesis pipeline and are generated inside `run_synthesis_pipeline()`.
- Deterministic signals are not persisted in the ready-state contract that admin/interviewer consume.
- ROS Pages 1-3 are derived in the synthesis path via `project_ros(canonical_data)`, but they are not exposed by the current ready-state API contract.

Observed code truth:

- Canonical persistence is implemented in `app/agents/orchestrator.py` and `app/models/canonical_record.py`.
- Admin/interviewer detail builders only return canonical plus draft data in `app/api/helpers.py`.
- Detail schemas expose `canonical` and draft fields only in `app/api/schemas.py`.
- Frontend detail components render a generic JSON block via `frontend/components/JsonSection.tsx`.

---

## 3. Drift Matrix

| Area | Intended | Current | Impact | Required change |
| --- | --- | --- | --- | --- |
| Persisted backend artifacts after upload | Persist raw PDF reference, canonical, deterministic signals, and ROS Pages 1-3 package | Persist canonical only in `canonical_records`; raw PDF path exists separately; deterministic signals and ROS Pages 1-3 are not persisted as the ready-state package | Ready-state contract is incomplete and cannot cleanly support review and downstream generation | Introduce a persisted deterministic review package for every `READY` application |
| Admin ready-state view | Show raw PDF + ROS Pages 1-3 | Shows canonical JSON only | Backend representation leaks into UI; review UX is not aligned with product model | Change admin detail payload and UI to render Pages 1-3 and surface raw PDF access |
| Interviewer assigned-state view | Show raw PDF + ROS Pages 1-3 | Shows canonical JSON only | Interviewer works from the wrong artifact; frontend contract is too backend-shaped | Change interviewer detail payload and UI to render Pages 1-3 and surface raw PDF access |
| Raw PDF access | Admin and interviewer can open the source PDF | PDF is stored server-side but not exposed in tested ready/assigned UI flow | Human reviewers cannot inspect source evidence directly | Add explicit PDF access handle/endpoint to review payloads |
| Deterministic signal availability pre-generation | Signals persisted immediately after deterministic processing | Signals generated inside synthesis path, not exposed in ready-state detail contract | Generation depends on pipeline-internal recomputation instead of a stable persisted package | Persist deterministic signals immediately after upload processing succeeds |
| ROS Pages 1-3 rendering contract | Ready-state APIs expose review-oriented Pages 1-3 artifact | Detail APIs expose canonical only | UI has no stable review-oriented data shape | Add Pages 1-3 object to ready/assigned detail contracts |
| Assign-to-interviewer handoff model | Assignment grants access to a deterministic review package | Assignment grants access to the application record; reviewer fetches canonical JSON | Human workflow and backend workflow are weakly coupled | Model assignment as access to a persisted review package |
| Pre-generation API response shape | Include raw PDF handle + Pages 1-3 + assignment metadata; keep canonical/signals backend-available | Includes metadata + canonical + draft if any | Response shape is not aligned with intended review workflow | Redefine pre-generation detail contracts around the review artifact |

---

## 4. Root-Cause Interpretation

The drift comes from four systemic choices in the current implementation:

### A. Backend representation leaked into frontend presentation

Canonical JSON is a backend assembly format. The current admin/interviewer detail views render it directly, which collapses the distinction between:

- persistence format
- internal deterministic pipeline state
- human review artifact

### B. Ready-state contract exposes canonical instead of review artifact

The current `GET /applications/{id}` contract for both admin and interviewer is canonical-first. That makes the ready-state UI depend on backend storage structure instead of on the product’s deterministic Pages 1-3 contract.

### C. Assignment is modeled as access to an application record, not an interviewer work package

The current assignment flow changes state and ownership, but it does not hand off a stable review bundle. As a result, the interviewer is assigned to an application whose UI contract is still canonical JSON.

### D. Deterministic signal layer is embedded too late in the visible workflow

Deterministic signals are generated in the Stage 1.7 synthesis path, but they are not part of the persisted, user-visible ready-state package. This creates the impression that the reviewer workflow is running ahead of the deterministic signal layer instead of resting on it.

---

## 5. Target-State Implementation Plan

This section is decision-complete and intended to guide implementation.

### A. Persist a deterministic review package after upload

After deterministic upload processing succeeds, the backend must persist a review package containing:

- raw PDF reference or access handle
- canonical
- deterministic signals
- ROS Pages 1-3 projection

This package becomes the authoritative ready-state artifact for both admin and interviewer review flows.

Default recommendation:

- keep canonical as a backend-owned source of truth
- persist deterministic signals beside canonical
- persist Pages 1-3 as a distinct rendered-review object, not as an inferred frontend transform

### B. Redefine admin detail contract around the review artifact

Admin detail responses for `READY`, `ASSIGNED`, and `DRAFT` must expose:

- application metadata
- assignment metadata
- raw PDF handle
- ROS Pages 1-3

Admin detail responses must not require the frontend to interpret raw canonical JSON as the review surface.

Admin visibility rules:

- `READY`: admin sees raw PDF + Pages 1-3
- `ASSIGNED`: admin sees raw PDF + Pages 1-3
- `DRAFT`: admin sees raw PDF + Pages 1-3 and draft status only
- `PUBLISHED`: admin sees final published Pages 1-5

Admin must not see draft Pages 4-5 before publish.

### C. Redefine interviewer detail contract around the assigned review package

Interviewer detail responses for assigned work must expose:

- application metadata
- raw PDF handle
- ROS Pages 1-3
- latest draft metadata and content only when a draft exists

The interviewer UI should not need raw canonical JSON as the primary visible artifact.

Interviewer visibility rules:

- before generation: interviewer sees raw PDF + Pages 1-3
- during draft iteration: interviewer sees raw PDF + Pages 1-3 + latest draft
- after publish: interviewer sees final published report according to role policy

### D. Keep canonical and deterministic signals backend-available for Pages 4-5 generation

Pages 4-5 generation must source from persisted deterministic backend state:

- canonical
- deterministic signals
- any persisted Pages 1-3 context if needed

Generation must not depend on the frontend’s rendered state or on recomputing hidden deterministic context from a canonical-only review contract.

Default recommendation:

- generation loads the persisted deterministic package by application id
- generation uses canonical and deterministic signals as backend input
- Pages 1-3 remain a review artifact and do not become the source of truth for generation

### E. Introduce explicit PDF access in review flows

Raw PDF access must be an explicit part of both admin and interviewer review flows.

Default recommendation:

- expose a backend-controlled PDF download/view endpoint
- return a PDF access handle or URL from detail responses
- do not expose raw storage paths to the frontend

### F. Clarify API contract families

Separate the contract families conceptually:

- list contract: summary/status/assignment only
- review detail contract: raw PDF + Pages 1-3 + role-appropriate metadata
- generation backend contract: canonical + deterministic signals + persisted deterministic package
- published contract: final Pages 1-5 representation

This prevents future drift between backend persistence and frontend review experience.

---

## 6. Acceptance Criteria

Implementation is complete only when all of the following are true:

1. After upload processing succeeds, a `READY` application has persisted:
   - canonical
   - deterministic signals
   - ROS Pages 1-3
   - raw PDF reference/access handle

2. Admin ready-state detail renders ROS Pages 1-3, not canonical JSON.

3. Interviewer assigned-state detail renders ROS Pages 1-3, not canonical JSON.

4. Admin can access the raw PDF in the review UI.

5. Interviewer can access the raw PDF in the review UI.

6. Pages 4-5 generation uses persisted deterministic backend state and does not require canonical JSON to be exposed in the UI.

7. Admin does not see draft Pages 4-5 before publish.

8. Assignment behaves as access handoff to a persisted deterministic review package, not merely to a generic application record.

9. The ready-state API contract is review-oriented and remains stable even if canonical internals evolve.

---

## Implementation Defaults and Assumptions

- The source of truth for deterministic extraction remains canonical.
- Deterministic signals are persisted immediately after deterministic processing succeeds.
- ROS Pages 1-3 are persisted as a review artifact, not computed ad hoc in the browser.
- Admin and interviewer pre-generation views are intentionally review-focused and should not expose canonical JSON by default.
- No assumption is made here about the exact database table layout; the requirement is behavioral and persistence-level, not tied to one schema design.
