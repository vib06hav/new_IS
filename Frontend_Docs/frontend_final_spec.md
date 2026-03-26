# AG Interview Standardiser — Frontend Specification (Final)

> **Target-state specification.** This document defines the complete intended product behavior. The backend currently implements only upload, deterministic processing, and basic fetch. States `ASSIGNED`, `DRAFT`, `PUBLISHED`, and all related actions (assign, generate, regenerate, publish, retry) are not yet implemented in the backend.

---

## 1. Application Lifecycle

Every PDF application moves through a single, linear state machine:

```text
UPLOADED → PROCESSING → READY → ASSIGNED → DRAFT → PUBLISHED
                      ↘ FAILED
```

### State Definitions

| State | Meaning |
|---|---|
| `UPLOADED` | PDF received, waiting in queue |
| `PROCESSING` | Deterministic pipeline actively running |
| `READY` | Pipeline succeeded; Pages 1–3 available |
| `FAILED` | Pipeline failed; retry available |
| `ASSIGNED` | Interviewer assigned; no draft yet |
| `DRAFT` | At least one generated draft exists |
| `PUBLISHED` | Final report frozen; no further changes |

### Transition Triggers

| Transition | Triggered by |
|---|---|
| UPLOADED → PROCESSING | System (queue processor) |
| PROCESSING → READY | Pipeline success |
| PROCESSING → FAILED | Pipeline failure |
| FAILED → PROCESSING | Admin retries |
| READY → ASSIGNED | Admin assigns interviewer |
| ASSIGNED → DRAFT | Interviewer generates first time |
| DRAFT → DRAFT | Interviewer regenerates |
| DRAFT → PUBLISHED | Interviewer publishes |

> **Current backend gap:** The backend goes directly to `processing` (lowercase) on upload and ends at `complete` or `failed`. States `UPLOADED`, `READY`, `ASSIGNED`, `DRAFT`, `PUBLISHED` do not exist yet. The FAILED → retry path also does not exist yet.

---

## 2. Page Separation Model

| Page | Contains |
|---|---|
| Upload Queue | `UPLOADED`, `PROCESSING`, `FAILED` only |
| Generated Reports | `READY`, `ASSIGNED`, `DRAFT`, `PUBLISHED` only |

When a PDF reaches `READY` → it **leaves** the Upload Queue and appears in Generated Reports.

---

## 3. Admin Frontend

### A. Upload Queue Page

**Purpose:** Entry point for PDF ingestion. Monitor deterministic processing.

**Shows:**
- All PDFs in states: `UPLOADED`, `PROCESSING`, `FAILED`
- File identifier + current state + timestamp

**Actions:**
| Action | Available when |
|---|---|
| Upload new PDF | Always |
| Retry processing | State == `FAILED` only |

**Behavior:**
- Upload → immediately enters `UPLOADED`
- System picks up `UPLOADED` items sequentially → moves to `PROCESSING`
- `READY` items leave this page automatically
- `FAILED` items stay until retried

---

### B. Generated Reports Page

**Purpose:** Track all processed applications. Central lifecycle view. Assignment control.

**Shows:**
- All applications in states: `READY`, `ASSIGNED`, `DRAFT`, `PUBLISHED`
- File/applicant identifier + state + assigned interviewer (if applicable)

**Actions:**
| Action | Available when |
|---|---|
| Assign interviewer | State == `READY` only |
| Reassign interviewer | State == `READY`, `ASSIGNED`, or `DRAFT` |
| View application | Always (READY and beyond) |

**What admin sees when viewing:**

| State | Admin sees |
|---|---|
| READY | Pages 1–3 + raw PDF |
| ASSIGNED | Pages 1–3 + raw PDF |
| DRAFT | Pages 1–3 + raw PDF + status only (no draft) |
| PUBLISHED | Pages 1–5 (full final report) |

> Admin **never** sees drafts. Pages 4–5 are only visible after publish.

**Reassignment during DRAFT:**
- Existing drafts are discarded
- Application resets to `ASSIGNED` for new interviewer
- New interviewer starts fresh

---

### C. Interviewer Manager Page

**Purpose:** Manage interviewer accounts.

**Shows:** All interviewers — name, email, number of active assignments.

**Actions:**
| Action | Notes |
|---|---|
| Create interviewer | Always available |
| Remove interviewer | Forces automatic unassignment |

**Removal behavior:**
- All assigned applications → reset to `READY`
- Any drafts in progress → discarded
- No deadlock; system remains operable

---

### D. Assignment Manager Page

**Purpose:** Global read-only mapping of assignments.

**Shows:**
- Application identifier
- Assigned interviewer
- Current state (`ASSIGNED`, `DRAFT`, `PUBLISHED`)

**Actions:** None. Strictly read-only.

> Assignment only happens from the Generated Reports page.

---

## 4. Interviewer Frontend

### A. Dashboard

**Purpose:** Entry point for all assigned work.

**Shows:**
- All applications assigned to this interviewer
- Identifier + state (`ASSIGNED`, `DRAFT`, `PUBLISHED`)

**Actions:**
- Open application (always available for assigned items)

---

### B. Application Workflow

After opening an application, the interviewer enters a 3-phase workspace.

---

#### Phase 1 — Before Generation (state: `ASSIGNED`)

**Visible:**
- Raw PDF
- Pages 1–3

**Action:**
| Button | Effect |
|---|---|
| **Generate** | Triggers LLM synthesis → creates first draft → state becomes `DRAFT` |

---

#### Phase 2 — Draft State (state: `DRAFT`)

**Visible:**
- Raw PDF
- Pages 1–3
- Pages 4–5 (latest draft)

**Actions:**
| Button | Effect |
|---|---|
| **Regenerate** | Creates new draft (previous draft stored internally, not shown) |
| **Publish** | Finalizes report → state becomes `PUBLISHED` |

**Draft model:**
- Multiple regenerations allowed
- Only the **latest draft** shown in UI
- Previous drafts stored internally for audit only
- Drafts are private to the assigned interviewer
- Drafts do not affect Pages 1–3

---

#### Phase 3 — Published (state: `PUBLISHED`)

**Visible:**
- Pages 1–5 (complete final report)

**Actions:** None. Read-only.

> Pages 4–5 are permanently frozen. No further generation allowed.

---

## 5. Action Constraints Summary

| Action | Allowed when | Blocked when |
|---|---|---|
| Assign | `READY` | Any other state |
| Reassign | `READY`, `ASSIGNED`, `DRAFT` | `PUBLISHED` |
| Generate | `ASSIGNED` | Any other state |
| Regenerate | `DRAFT` | Any other state |
| Publish | `DRAFT` | Any other state |
| Retry | `FAILED` | Any other state |
| View (admin) | `READY` and beyond | `UPLOADED`, `PROCESSING`, `FAILED` |

**Additional constraints:**
- Generation actions (Generate / Regenerate) are **disabled while a generation request is in progress**
- Publish requires an **existing valid draft** (only possible when state == `DRAFT`)
- Reassigning to the **same interviewer** results in no change (no-op)

---

## 6. Visibility Model

### Before Publish

| Role | Sees |
|---|---|
| Admin | Raw PDF, Pages 1–3, status |
| Interviewer | Raw PDF, Pages 1–3, draft workspace (if DRAFT) |

### After Publish

| Role | Sees |
|---|---|
| Admin | Pages 1–5 (full report) |
| Interviewer | Pages 1–5 (full report) |

Neither role can regenerate or modify after publish.

---

## 7. Generate vs Regenerate

Same backend action. Label changes by state:

| State | Button Label | Effect |
|---|---|---|
| `ASSIGNED` | **Generate** | Creates first draft |
| `DRAFT` | **Regenerate** | Creates new draft version |

---

## 8. Key Behavioral Guarantees

1. **Pages 1–3 are immutable** after `READY` — no action can change them
2. **Only the latest draft is shown** — previous versions exist internally only
3. **One published report per application** — publish is a one-way door
4. **Global consistency** — all pages reflect the same state at all times
5. **No soft failures** — pipeline is binary: `READY` or `FAILED`
6. **Clean page separation** — Upload Queue and Generated Reports never overlap
7. **Admin never sees drafts** — only final report after publish
8. **State transitions are atomic** — immediately reflected across all views with no partial states
9. **Applications in `UPLOADED`, `PROCESSING`, or `FAILED` cannot be opened** for viewing by any role

---

## 9. Full System Flow

```text
Admin uploads PDF
→ UPLOADED (waiting in queue)
→ PROCESSING (pipeline running)
→ READY (leaves Upload Queue → enters Generated Reports)

Admin assigns interviewer
→ ASSIGNED

Interviewer generates
→ DRAFT (Pages 4–5 visible to interviewer only)

Interviewer iterates (optional)
→ DRAFT → DRAFT → ...

Interviewer publishes
→ PUBLISHED (Pages 1–5 frozen, visible to both roles)
```
