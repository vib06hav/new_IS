# Backend Target-State ADR

## Decision
The backend implementation is governed by:
- [backend_entity_model.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/backend_entity_model.md)
- [frontend_final_spec.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/frontend_final_spec.md)
- [frontend_ui_flow.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/frontend_ui_flow.md)
- [spec_gap_list_for_doc_revision.md](/c:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/Frontend_Docs/spec_gap_list_for_doc_revision.md)

This work is backend-only. `frontend/` and `base_frontend/` are mock/non-authoritative and do not define the contract.

## Target Lifecycle
`UPLOADED -> PROCESSING -> READY -> ASSIGNED -> DRAFT -> PUBLISHED`

Failure path:
`PROCESSING -> FAILED`

Retry path:
`FAILED -> UPLOADED`

## Target Data Model
- `users`: includes `name`
- `applications`: uses `status`
- `canonical_records`: deterministic Pages 1-3 source of truth
- `assignments`: active ownership mapping
- `drafts`: versioned Pages 4-5 source of truth

`synthesis_records` is retired from the active architecture.

## Target API Surface
- Auth: `/auth/register`, `/auth/login`
- Admin:
  - `POST /applications/upload`
  - `GET /applications`
  - `GET /applications/{id}`
  - `POST /applications/{id}/retry`
  - `POST /applications/{id}/assign`
  - `PUT /applications/{id}/assign`
  - `GET /assignments`
  - `GET /users/interviewers`
  - `DELETE /users/{id}`
- Interviewer:
  - `GET /me/applications`
  - `POST /applications/{id}/generate`
  - `POST /applications/{id}/publish`

## Enforcement Rules
- Only admins can upload, retry, assign, reassign, list all applications, list assignments, and manage interviewers.
- Interviewers can only read and mutate applications assigned to them.
- Admins never see draft Pages 4-5 content before publish.
- Upload stops after deterministic canonical generation; Pages 4-5 are generated only in interviewer workflow.
