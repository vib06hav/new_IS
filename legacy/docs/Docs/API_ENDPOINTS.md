# API Endpoints

This document describes the current HTTP API exposed by the FastAPI backend in this repository.

Source of truth:
- [main.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/main.py)
- [router.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/router.py)
- [applications.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/applications.py)
- [admin.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/admin.py)
- [interviewer.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/interviewer.py)
- [users.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/users.py)
- [schemas.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/api/schemas.py)
- [schemas.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/auth/schemas.py)

## Overview

- Framework: FastAPI
- App title: `Interview Standardiser API`
- Version: `0.1.0`
- Authentication:
  - cookie-based session auth by default
  - bearer token auth is also accepted by the backend dependency layer
- CSRF:
  - enforced for non-safe methods when session-cookie auth is used
  - exempt path: `/auth/login`
- Main route groups:
  - `auth`
  - `applications`
  - `admin`
  - `interviewer`
  - `users`

## Base Behavior

### Security headers

Every response gets:
- `Content-Security-Policy`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security` in production only

### Authentication

The backend accepts auth from either:
- `Authorization: Bearer <token>`
- session cookie named by `SESSION_COOKIE_NAME` (default `agis_session`)

Role guards:
- admin-only routes use `require_admin`
- interviewer-only routes use `require_interviewer`
- mixed routes use `get_current_user` and then apply resource-specific checks

### CSRF requirements

For state-changing requests made with the session cookie:
- request must come from a trusted `Origin` or `Referer`
- request must include header `X-CSRF-Token` by default
- header value must match cookie `agis_csrf` by default

CSRF is not required when:
- method is `GET`, `HEAD`, `OPTIONS`, or `TRACE`
- using bearer auth instead of session cookie
- calling `/auth/login`

## Common Response Models

### SessionResponse

```json
{
  "user": {
    "id": "uuid",
    "name": "string",
    "email": "string",
    "role": "admin | interviewer"
  }
}
```

### UserResponse

```json
{
  "id": "uuid",
  "name": "string",
  "email": "string",
  "role": "admin | interviewer"
}
```

### ApplicationListItem

```json
{
  "id": "uuid",
  "display_id": "string",
  "status": "string",
  "is_hidden": false,
  "is_hidden_for_interviewer": false,
  "created_at": "datetime",
  "last_activity_at": "datetime",
  "assigned_interviewer": {
    "id": "uuid",
    "name": "string",
    "email": "string"
  }
}
```

### DraftSummary

```json
{
  "id": "uuid",
  "version": 1,
  "is_published": false,
  "created_at": "datetime",
  "content": {}
}
```

### ReviewPackageSummary

```json
{
  "canonical_version": "string",
  "pdf_url": "/applications/{application_id}/source-pdf",
  "pages_1_3": {
    "page_1_background_profile": {},
    "page_2_academic_and_engagement": {},
    "page_3_essays": {}
  }
}
```

## Health

### `GET /health`

Purpose:
- health check
- verifies database connectivity with `SELECT 1`

Auth:
- none

Response:

```json
{
  "status": "ok",
  "message": "Service is healthy and database is reachable."
}
```

## Auth Endpoints

Base prefix: `/auth`

### `POST /auth/register`

Purpose:
- create a new interviewer account

Access:
- admin only

Request body:

```json
{
  "name": "Interviewer Name",
  "email": "user@example.com",
  "password": "min-8-chars",
  "role": "interviewer"
}
```

Notes:
- this endpoint rejects any `role` other than `interviewer`

Success:
- `201 Created`
- returns `UserResponse`

Common failures:
- `403` if non-admin
- `403` if role is not `interviewer`

### `POST /auth/login`

Purpose:
- authenticate a user and establish session

Access:
- public

Request body:
- `application/x-www-form-urlencoded`
- uses `OAuth2PasswordRequestForm`

Fields:
- `username`: email
- `password`

Notes:
- rate limited by IP and account identifier
- on success sets:
  - session cookie
  - CSRF cookie

Success:
- `200 OK`
- returns `SessionResponse`

Common failures:
- `401` invalid credentials
- rate limit failure from login limiter

### `GET /auth/session`

Purpose:
- return current session user

Access:
- authenticated user

Notes:
- if CSRF cookie is missing, it is reissued

Success:
- `200 OK`
- returns `SessionResponse`

### `POST /auth/logout`

Purpose:
- clear session and CSRF cookies

Access:
- no explicit auth check required by route, but intended for active session logout

Success:
- `204 No Content`

### `PUT /auth/change-password`

Purpose:
- let the currently logged-in user change their own password

Access:
- authenticated user

Request body:

```json
{
  "current_password": "string",
  "new_password": "min-8-chars"
}
```

Success:
- `200 OK`
- returns `SessionResponse`

### `PUT /auth/profile`

Purpose:
- let the currently logged-in user update their own profile name

Access:
- authenticated user

Request body:

```json
{
  "name": "New Display Name"
}
```

Success:
- `200 OK`
- returns `SessionResponse`

## Applications Endpoints

Base prefix: `/applications`

### `POST /applications/upload`

Purpose:
- upload a source PDF and create an application
- immediately triggers the deterministic parsing pipeline

Access:
- admin only

Request:
- `multipart/form-data`
- field name: `file`

Rules:
- file must be a PDF
- filename without `.pdf` becomes the initial `display_id`
- resulting display ID must be unique
- file size must not exceed `MAX_UPLOAD_SIZE_MB`
- uploaded PDF must have at least one page

Behavior:
- creates application with status progression:
  - `UPLOADED`
  - `PROCESSING`
  - pipeline result status, usually `READY` or `FAILED`

Success:
- `201 Created`
- returns:

```json
{
  "id": "uuid",
  "display_id": "string",
  "status": "READY | FAILED | ...",
  "created_at": "datetime"
}
```

Common failures:
- `400` non-PDF or invalid PDF
- `409` duplicate display ID
- `413` upload too large

### `GET /applications/{application_id}`

Purpose:
- fetch application detail

Access:
- admin can fetch any application
- interviewer can fetch only if assigned to that application

Response for admin:

```json
{
  "id": "uuid",
  "display_id": "string",
  "status": "string",
  "created_at": "datetime",
  "last_activity_at": "datetime",
  "assigned_interviewer": {},
  "review_package": {},
  "published_draft": {}
}
```

Response for interviewer:

```json
{
  "id": "uuid",
  "display_id": "string",
  "status": "string",
  "created_at": "datetime",
  "last_activity_at": "datetime",
  "is_hidden_for_interviewer": false,
  "assigned_interviewer": {},
  "review_package": {},
  "latest_draft": {}
}
```

Important visibility rule:
- admin sees `published_draft`
- interviewer sees `latest_draft`

Common failures:
- `403` interviewer not assigned
- `404` application not found

### `GET /applications/{application_id}/source-pdf`

Purpose:
- download or open the original uploaded PDF

Access:
- admin can access any application source PDF
- interviewer can access only if assigned

Success:
- `200 OK`
- returns `application/pdf`

Common failures:
- `403` unauthorized
- `404` source PDF not found

## Admin Endpoints

No route prefix beyond the literal paths below.

All endpoints in this section are admin-only.

### `GET /applications`

Purpose:
- list applications for the admin dashboard

Query params:
- `status` optional

Supported behavior:
- no `status`: returns non-hidden applications
- `status=HIDDEN`: returns hidden applications
- any other status value: returns non-hidden applications filtered by status

Success:
- `200 OK`
- returns `ApplicationListItem[]`

### `POST /applications/{application_id}/retry`

Purpose:
- retry deterministic processing for a failed application

Rules:
- only `FAILED` applications can be retried

Behavior:
- sets status to `PROCESSING`
- reruns deterministic pipeline

Success:
- `200 OK`
- returns `ApplicationListItem`

Common failures:
- `409` if application is not `FAILED`

### `POST /applications/{application_id}/assign`

Purpose:
- assign a ready application to an interviewer for the first time

Request body:

```json
{
  "interviewer_id": "uuid"
}
```

Rules:
- application must be `READY`
- application must not already have an assignment
- interviewer must exist and have role `interviewer`

Behavior:
- creates assignment row
- sets application status to `ASSIGNED`

Success:
- `200 OK`
- returns `ApplicationListItem`

Common failures:
- `400` interviewer not found
- `409` application not `READY`
- `409` already assigned

### `PUT /applications/{application_id}/assign`

Purpose:
- reassign an already assigned application

Request body:

```json
{
  "interviewer_id": "uuid"
}
```

Rules:
- application must be `ASSIGNED` or `DRAFT`
- assignment must already exist

Behavior:
- deletes existing drafts for that application
- moves assignment to new interviewer
- clears interviewer-specific hidden state
- resets application status to `ASSIGNED`

Success:
- `200 OK`
- returns `ApplicationListItem`

Common failures:
- `400` interviewer not found
- `404` assignment not found
- `409` invalid application status

### `POST /applications/{application_id}/hide`

Purpose:
- hide an application from admin application listings

Behavior:
- sets `application.is_hidden = true`
- updates `last_activity_at`

Success:
- `200 OK`
- returns `ApplicationListItem`

### `POST /applications/{application_id}/unhide`

Purpose:
- restore a globally hidden application to normal admin listings

Behavior:
- sets `application.is_hidden = false`

Success:
- `200 OK`
- returns `ApplicationListItem`

### `DELETE /applications/{application_id}/queue`

Purpose:
- remove an upload from the queue-style lifecycle

Rules:
- only applications in `UPLOADED` or `FAILED` can be removed through this route

Behavior:
- deletes:
  - drafts
  - canonical records
  - assignments
  - application row
  - source file on disk if present

Success:
- `204 No Content`

Common failures:
- `409` if status is not `UPLOADED` or `FAILED`

### `DELETE /applications/{application_id}`

Purpose:
- hard delete any application

Behavior:
- deletes related drafts, canonical data, assignments, application row, and source file

Success:
- `204 No Content`

### `PUT /applications/{application_id}/display-id`

Purpose:
- change the visible application display ID

Request body:

```json
{
  "display_id": "New Display ID"
}
```

Rules:
- display ID cannot be empty
- display ID must be unique across applications

Success:
- `200 OK`
- returns `ApplicationListItem`

Common failures:
- `400` empty display ID
- `409` duplicate display ID

### `GET /assignments`

Purpose:
- list all assignments across the system

Success:
- `200 OK`
- returns:

```json
[
  {
    "application_id": "uuid",
    "application_display_id": "string",
    "status": "string",
    "assigned_at": "datetime",
    "interviewer": {
      "id": "uuid",
      "name": "string",
      "email": "string"
    }
  }
]
```

## Interviewer Endpoints

All endpoints in this section are interviewer-only.

### `GET /me/applications`

Purpose:
- list applications assigned to the current interviewer

Behavior:
- only returns applications assigned to current interviewer
- excludes globally hidden applications
- ordered by `last_activity_at desc`, then `created_at desc`

Success:
- `200 OK`
- returns `ApplicationListItem[]`

### `POST /applications/{application_id}/generate`

Purpose:
- generate or regenerate a draft report for the assigned application

Rules:
- interviewer must be assigned
- application status must be `ASSIGNED` or `DRAFT`
- `PUBLISHED` applications cannot be regenerated
- canonical data must exist

Behavior:
- rate limited
- runs synthesis pipeline
- creates a new `Draft`
- increments version number
- sets application status to `DRAFT`

Success:
- `200 OK`
- returns:

```json
{
  "application_id": "uuid",
  "status": "DRAFT",
  "draft": {
    "id": "uuid",
    "version": 2,
    "is_published": false,
    "created_at": "datetime",
    "content": {}
  }
}
```

Common failures:
- `403` not assigned
- `409` invalid status
- `409` missing canonical data
- `502` synthesis returned invalid output

### `POST /applications/{application_id}/publish`

Purpose:
- publish the latest draft

Rules:
- interviewer must be assigned
- application status must be `DRAFT`
- latest draft must exist

Behavior:
- rate limited
- clears `is_published` on other drafts for the application
- marks latest draft `is_published = true`
- sets application status to `PUBLISHED`

Success:
- `200 OK`
- returns `DraftMutationResponse`

Common failures:
- `403` not assigned
- `409` application not in `DRAFT`
- `409` no draft available

### `POST /me/applications/{application_id}/hide`

Purpose:
- hide an assigned application only from the current interviewer’s list

Rules:
- interviewer must be assigned
- application cannot be globally hidden

Behavior:
- sets `assignment.is_hidden_for_interviewer = true`

Success:
- `200 OK`
- returns `ApplicationListItem`

Common failures:
- `403` not assigned
- `404` assignment not found
- `409` application is globally hidden

### `POST /me/applications/{application_id}/unhide`

Purpose:
- restore an interviewer-hidden application to the current interviewer’s list

Rules:
- interviewer must be assigned
- application cannot be globally hidden

Behavior:
- sets `assignment.is_hidden_for_interviewer = false`

Success:
- `200 OK`
- returns `ApplicationListItem`

## Users Endpoints

Base prefix: `/users`

All endpoints in this section are admin-only.

### `POST /users/interviewers`

Purpose:
- create an interviewer account

Request body:

```json
{
  "name": "Interviewer Name",
  "email": "user@example.com",
  "password": "min-8-chars"
}
```

Success:
- `201 Created`
- returns `UserResponse`

### `GET /users/interviewers`

Purpose:
- list interviewer accounts with active assignment counts

Success:
- `200 OK`
- returns:

```json
[
  {
    "id": "uuid",
    "name": "string",
    "email": "string",
    "active_assignment_count": 3
  }
]
```

### `GET /users/interviewers/{user_id}/assignments`

Purpose:
- get assignment management summary for one interviewer

Response:

```json
{
  "interviewer_id": "uuid",
  "active_assignment_count": 2,
  "currently_assigned": [
    {
      "application_id": "uuid",
      "application_display_id": "string",
      "status": "ASSIGNED"
    }
  ],
  "available_to_assign": [
    {
      "application_id": "uuid",
      "application_display_id": "string",
      "status": "READY"
    }
  ],
  "available_to_reassign": [
    {
      "application_id": "uuid",
      "application_display_id": "string",
      "status": "DRAFT",
      "current_interviewer": {
        "id": "uuid",
        "name": "string",
        "email": "string"
      }
    }
  ]
}
```

### `PUT /users/interviewers/{user_id}/assignments`

Purpose:
- save the full staged assignment set for one interviewer

Request body:

```json
{
  "assigned_application_ids": ["uuid-1", "uuid-2"]
}
```

Behavior:
- final submitted set becomes the interviewer’s active set
- newly added `READY` applications get assigned
- reassigned `ASSIGNED` or `DRAFT` applications move to this interviewer
- reassignment deletes existing drafts and resets app status to `ASSIGNED`
- removed current assignments are deleted and affected apps return to `READY`

Rules:
- application must be `READY`, `ASSIGNED`, or `DRAFT`
- published applications cannot be staged here
- only `READY` applications can be newly assigned when no assignment exists

Success:
- `200 OK`
- returns updated `InterviewerAssignmentSummary`

Common failures:
- `404` interviewer not found
- `404` application not found
- `409` invalid application state

### `PUT /users/interviewers/{user_id}`

Purpose:
- update interviewer profile fields as admin

Request body:

```json
{
  "name": "Updated Name",
  "email": "updated@example.com"
}
```

Success:
- `200 OK`
- returns `UserResponse`

### `PUT /users/interviewers/{user_id}/password`

Purpose:
- set a new password for an interviewer as admin

Request body:

```json
{
  "new_password": "min-8-chars"
}
```

Success:
- `200 OK`
- returns `UserResponse`

### `DELETE /users/{user_id}`

Purpose:
- delete an interviewer account

Rules:
- target user must exist
- target user must have role `interviewer`
- cannot delete if referenced as uploader on any application
- cannot delete while any assignments still exist

Success:
- `204 No Content`

Common failures:
- `404` user not found
- `409` non-interviewer target
- `409` uploader reference exists
- `409` active assignments exist

## Status Values Seen In API Logic

Application status values used directly in route logic:
- `UPLOADED`
- `PROCESSING`
- `READY`
- `FAILED`
- `ASSIGNED`
- `DRAFT`
- `PUBLISHED`

Special admin filter value:
- `HIDDEN`

## Rate Limits Used In Code

Current hardcoded rate limits:
- login by IP: `10 / 60s`
- login by account identifier: `5 / 60s`
- upload by admin user: `10 / 60s`
- generate draft per interviewer/application: `5 / 60s`
- publish draft per interviewer/application: `5 / 60s`

## Notes For Frontend Consumers

- Login uses form-encoded payloads, not JSON.
- Most authenticated frontend calls use cookie auth plus CSRF header.
- `/applications/{id}` is polymorphic:
  - admin gets `published_draft`
  - interviewer gets `latest_draft`
- Generated report highlights live inside `draft.content.signal_data.annotations`.
- Admin-assignment flows can delete drafts during reassignment.
- Interviewer hide/unhide is assignment-scoped, not global.

