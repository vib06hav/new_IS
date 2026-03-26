# Backend Entity Model + API Surface

## Document Scope

> **This is a target-state specification.** It describes the schema and API surface that needs to be built, not what currently exists in the backend. Use the table below to understand what's already implemented vs what this document is specifying.

### Current Backend vs Target

| Area | Currently implemented | Target (this doc) |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, JWT, hashing | Keep as-is |
| Upload | `POST /applications/upload` (synchronous, full pipeline) | Modify: set `UPLOADED`, stop before LLM |
| Fetch application | `GET /applications/{id}` | Modify: role-aware response |
| Status values | `processing`, `complete`, `failed` (lowercase) | `UPLOADED PROCESSING READY FAILED ASSIGNED DRAFT PUBLISHED` |
| `users` table | id, email, password_hash, role, created_at | Add `name` |
| `applications` table | id, uploaded_by, file_path, pipeline_status, pipeline_confidence, created_at | Rename column, drop confidence, expand states |
| `canonical_records` | Exists, correct | Keep as-is |
| `synthesis_records` | Exists, active, unique per app | Drop — replaced by `drafts` |
| `assignments` | Does not exist | New table |
| `drafts` | Does not exist | New table |
| List endpoints | None | Add `GET /applications`, `GET /me/applications`, `GET /assignments`, `GET /users/interviewers` |
| Workflow endpoints | None | Add retry, assign, generate, publish, remove interviewer |
| Role guards | Ad-hoc inline checks | Reusable `require_admin` / `require_interviewer` dependencies |

---

## Background

The existing backend has a working pipeline but was designed as a single-shot processor (upload → full synthesis → done). The frontend spec requires a multi-stage, stateful, multi-user workflow. This document defines all schema changes and new API surface needed.

---

## 1. Schema Changes

### Summary of what changes

| Table | Action | Reason |
|---|---|---|
| `users` | Add `name` column | UI shows interviewer names |
| `applications` | Rename `pipeline_status` → `status`, expand states, drop `pipeline_confidence` | Full lifecycle state machine |
| `canonical_records` | Keep as-is | Stores deterministic Pages 1–3 projection — correct |
| `synthesis_records` | **Drop / repurpose** | Unique constraint conflicts with multi-draft model |
| `assignments` | **New table** | Application → interviewer mapping |
| `drafts` | **New table** | Versioned Pages 4–5 generation output |

---

### `users` (modify)

```
id              UUID        PK
email           String      unique, not null
password_hash   String      not null
role            String      'admin' | 'interviewer'
name            String      not null         ← ADD THIS
created_at      DateTime    server default
```

---

### `applications` (modify)

```
id              UUID        PK
uploaded_by     UUID        FK users.id
file_path       String      path or MinIO key
status          String      not null         ← rename + expand
created_at      DateTime    server default
```

**`status` values (full lifecycle):**
```
UPLOADED → PROCESSING → READY → ASSIGNED → DRAFT → PUBLISHED
                              ↘ FAILED
```

Drop `pipeline_status` (rename to `status`) and drop `pipeline_confidence` (soft failure removed).

---

### `canonical_records` (keep as-is)

```
id                  UUID    PK
application_id      UUID    FK applications.id, unique
canonical_version   String
canonical_data      JSONB   ← deterministic Pages 1–3 projection
created_at          DateTime
```

This table is correct. It stores the immutable deterministic output per application.

---

### `synthesis_records` (drop)

This table is currently a single-record store for the full synthesis (Pages 1–5 combined). Under the new model this is replaced by `drafts`. Drop it entirely.

> **Migration note:** This is a dev environment. Drop the table and discard all existing data. Any application rows with `pipeline_status = 'complete'` should be manually reset to `READY` or wiped — whichever is cleaner for the current state of testing.

---

### `assignments` (new table)

```
id              UUID        PK
application_id  UUID        FK applications.id, unique  ← one active assignment per app
interviewer_id  UUID        FK users.id
assigned_by     UUID        FK users.id                 ← admin who assigned
assigned_at     DateTime    server default
```

**Behavior:**
- Unique on `application_id` — only one assignment at a time
- Reassignment = UPDATE this row (delete old, insert new — or just update)
- On interviewer removal → delete their assignment rows, reset app status to READY

---

### `drafts` (new table)

```
id              UUID        PK
application_id  UUID        FK applications.id
version         Integer     not null           ← increments per application
content         JSONB       not null           ← Pages 4–5 output
generated_by    UUID        FK users.id        ← interviewer who triggered
is_published    Boolean     default false
created_at      DateTime    server default
```

**Behavior:**
- Multiple rows per application allowed
- On regenerate → new row, version +1
- On publish → set `is_published = true` on latest draft, block further inserts
- Latest draft = `ORDER BY version DESC LIMIT 1`
- Only latest draft is ever surfaced in the UI

---

## 2. Application Status State Machine

```
UPLOADED
→ PROCESSING   (system starts pipeline)
→ READY        (pipeline succeeded, canonical_records row created)
→ FAILED       (pipeline failed, retry resets to UPLOADED)
→ ASSIGNED     (admin assigns interviewer, assignments row created)
→ DRAFT        (interviewer generates, first drafts row created)
→ PUBLISHED    (interviewer publishes, drafts.is_published = true)
```

**Status transition rules (enforced at API layer):**

| Action | Requires status | Sets status to |
|---|---|---|
| Upload | — | UPLOADED |
| Pipeline start | UPLOADED | PROCESSING |
| Pipeline success | PROCESSING | READY |
| Pipeline fail | PROCESSING | FAILED |
| Retry | FAILED | UPLOADED |
| Assign | READY | ASSIGNED |
| Reassign | ASSIGNED or DRAFT | ASSIGNED (resets draft) |
| Generate | ASSIGNED | DRAFT |
| Regenerate | DRAFT | DRAFT (stays) |
| Publish | DRAFT | PUBLISHED |

---

## 3. API Surface

### Auth (existing — keep)

| Method | Route | Description |
|---|---|---|
| POST | `/auth/register` | Create user (admin or interviewer) |
| POST | `/auth/login` | Login → JWT |

---

### Applications (admin)

| Method | Route | Description |
|---|---|---|
| POST | `/applications/upload` | Upload PDF (modify existing) |
| GET | `/applications` | List all applications (with optional status filter) |
| GET | `/applications/{id}` | View application detail |
| POST | `/applications/{id}/retry` | Retry FAILED application |
| POST | `/applications/{id}/assign` | Assign interviewer (status must be READY) |
| PUT | `/applications/{id}/assign` | Reassign interviewer (status ASSIGNED or DRAFT) |

---

### Interviewer (dashboard + workflow)

| Method | Route | Description |
|---|---|---|
| GET | `/me/applications` | List applications assigned to current user |
| POST | `/applications/{id}/generate` | Generate or regenerate Pages 4–5 |
| POST | `/applications/{id}/publish` | Publish latest draft |

---

### Users / Interviewer management (admin)

| Method | Route | Description |
|---|---|---|
| GET | `/users/interviewers` | List all interviewers |
| DELETE | `/users/{id}` | Remove interviewer (triggers unassignment + reset) |

---

### Assignments (read-only admin view)

| Method | Route | Description |
|---|---|---|
| GET | `/assignments` | List all assignments (for Assignment Manager page) |

---

## 4. Data Returned Per Endpoint

### `GET /applications` (admin list)

Per item:
- `id`, `status`, `created_at`, `file_path`
- `assigned_interviewer`: `{id, name, email}` or null

### `GET /applications/{id}` (admin view)

Returns based on status:
- Always: `id`, `status`, `created_at`, raw PDF reference
- If READY+: `canonical_data` (Pages 1–3 projection)
- If PUBLISHED only: `published_draft.content` (Pages 4–5)

### `GET /me/applications` (interviewer)

Per item:
- `id`, `status`, `created_at`

### `GET /applications/{id}` (interviewer view)

- Always: `id`, `status`, Pages 1–3 from `canonical_data`
- If DRAFT: latest draft `content` (Pages 4–5)
- If PUBLISHED: `published_draft.content`

### `POST /applications/{id}/generate`

Returns: new draft `{id, version, content, created_at}`

### `GET /assignments`

Per item:
- `application_id`, `interviewer: {id, name, email}`, `status`

---

## 5. File Storage

**Current:** local disk (`settings.UPLOAD_DIRECTORY`)
**Target:** MinIO (already in docker-compose presumably)

**Decision for now:** Keep local disk for dev, add MinIO abstraction layer later. The `file_path` column should store a path/key string that works for both. No code change needed yet.

---

## 6. Role-Based Access Enforcement

| Route | Admin | Interviewer |
|---|---|---|
| Upload | ✅ | ❌ |
| List all applications | ✅ | ❌ |
| View application | ✅ | ✅ (own only) |
| Retry | ✅ | ❌ |
| Assign / Reassign | ✅ | ❌ |
| Generate / Regenerate | ❌ | ✅ (own only) |
| Publish | ❌ | ✅ (own only) |
| List interviewers | ✅ | ❌ |
| Remove interviewer | ✅ | ❌ |
| View assignments | ✅ | ❌ |
| Own dashboard | ❌ | ✅ |

**Implementation note:** Enforcement must use reusable FastAPI dependencies — `require_admin` and `require_interviewer` — injected per route. No inline role checks scattered across endpoints. The `require_interviewer` dependency must also validate that the `application_id` in the route belongs to the current user's assignment.
