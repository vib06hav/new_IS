# AG Interview Standardiser — UI Flow (Screen by Screen)

> **Target-state specification.** This document describes the complete intended UI behavior. Screens 1–9 all depend on backend work that is not yet fully implemented. Specifically: the `UPLOADED` queue state, all screens beyond upload (Generated Reports, Interviewer workflow, Assign, Generate, Publish), and state polling are target behaviors. Only the upload action itself and basic application fetch have a current backend counterpart.

---

## Admin Frontend

---

### Screen 1 — Upload Queue Page

**Default view:**
- List of all PDFs in states: `UPLOADED`, `PROCESSING`, `FAILED`
- If no PDFs yet → empty state: "No uploads yet"
- Upload button always visible

**Per row, based on state:**

| State | Row shows | Actions on row |
|---|---|---|
| `UPLOADED` | Filename, "Waiting" | None |
| `PROCESSING` | Filename, spinner | None (all actions disabled) |
| `FAILED` | Filename, "Failed", error hint | Retry button |

**Upload action:**
- User selects PDF → row immediately appears as `UPLOADED`
- System picks it up → row flips to `PROCESSING` (spinner appears on row)
- On success → row disappears from this page (moved to Generated Reports)
- On failure → row stays, shows `FAILED` + retry option

> **Backend gap:** The current backend processes the full pipeline synchronously inside the upload request. The `UPLOADED` waiting state and sequential queue pickup do not exist yet. The UI should treat this page as target behavior until the backend separates upload receipt from pipeline execution.

**Loading moments:**
- Row-level spinner while `PROCESSING` — no full-page block
- Upload button stays enabled (can queue multiple)
- Retry: row immediately flips back to `PROCESSING` on click

**Error state:**
- If upload itself fails (bad file, server error) → inline error on row or toast notification

---

### Screen 2 — Generated Reports Page

**Default view:**
- List of all applications in: `READY`, `ASSIGNED`, `DRAFT`, `PUBLISHED`
- If none yet → empty state: "No processed applications yet"

**Per row, based on state:**

| State | Row shows | Actions on row |
|---|---|---|
| `READY` | Identifier, "Ready", no interviewer | Assign, View |
| `ASSIGNED` | Identifier, "Assigned", interviewer name | Reassign, View |
| `DRAFT` | Identifier, "Draft", interviewer name | Reassign, View |
| `PUBLISHED` | Identifier, "Published", interviewer name | View |

**Assign action:**
- Opens a modal → dropdown of available interviewers → confirm
- On confirm → row instantly updates to `ASSIGNED` with interviewer name
- Assigning to same interviewer → no-op (nothing changes)

**Reassign during DRAFT:**
- Confirmation dialog warning: "Existing draft will be discarded. Continue?"
- On confirm → application resets to `ASSIGNED` for new interviewer

**View action:**
- Opens application view (see Screen 3)
- Always available for `READY` and beyond

---

### Screen 3 — Admin Application View

**What admin sees:**

| State | Content shown |
|---|---|
| `READY` / `ASSIGNED` | Raw PDF viewer + Pages 1–3 |
| `DRAFT` | Raw PDF viewer + Pages 1–3 + status banner ("Draft in progress") |
| `PUBLISHED` | Pages 1–5 (full final report) |

**No actions** — admin view is read-only at all times.

**Loading moment:**
- If PDF or pages are loading → skeleton placeholder while content loads

---

### Screen 4 — Interviewer Manager Page

**Default view:**
- List of all interviewers (name, email, active assignment count)
- If none → empty state: "No interviewers yet"
- Create button always visible

**Per row:**
- Name, email, assignment count
- Remove button on each row

**Create action:**
- Opens a form/modal → name + email → submit
- On submit → new row appears immediately

**Remove action:**
- If interviewer has active assignments → confirmation dialog: "This interviewer has N active assignments. Removing will unassign all of them and discard any drafts. Continue?"
- On confirm → interviewer removed, their apps reset to `READY`
- If no active assignments → simpler confirmation dialog

---

### Screen 5 — Assignment Manager Page

**Default view:**
- List of all assignments (application identifier, assigned interviewer, state)
- States shown: `ASSIGNED`, `DRAFT`, `PUBLISHED`
- If none → empty state: "No assignments yet"

**No actions.** Pure read-only overview.

**Loading moment:**
- Standard page load spinner until list populates

---

## Interviewer Frontend

---

### Screen 6 — Interviewer Dashboard

**Default view:**
- List of all applications assigned to this interviewer
- If none → empty state: "No applications assigned yet"

**Per row:**

| State | Row shows | Action |
|---|---|---|
| `ASSIGNED` | Identifier, "Not started" | Open |
| `DRAFT` | Identifier, "Draft ready" | Open |
| `PUBLISHED` | Identifier, "Published" | Open |

**Open action:**
- Navigates to application workspace (Screens 7–9)

---

### Screen 7 — Application Workspace: Phase 1 (state: `ASSIGNED`)

**Content visible:**
- Raw PDF viewer (left or top panel)
- Pages 1–3 (structured output)
- Generate button

**Generate button:**
- Enabled by default
- On click → button enters loading state ("Generating…", disabled)
- Pages 4–5 area shows skeleton/spinner
- On success → workspace transitions to Phase 2 (Draft state)
- On failure → error message shown, button re-enabled for retry

**Loading moment:**
- This is the heaviest async moment (LLM call)
- Full Pages 4–5 area blocked with loading indicator
- All other actions (nav away) ideally warn user that generation is in progress

---

### Screen 8 — Application Workspace: Phase 2 (state: `DRAFT`)

**Content visible:**
- Raw PDF viewer
- Pages 1–3 (unchanged, read-only)
- Pages 4–5 (latest draft)
- Regenerate button + Publish button

**Regenerate button:**
- On click → enters loading state ("Regenerating…", disabled)
- Pages 4–5 area re-enters skeleton/spinner state
- Publish button also disabled during regeneration
- On success → Pages 4–5 refresh with new draft content
- On failure → error shown, buttons re-enabled

**Publish button:**
- Enabled only when not generating
- On click → confirmation dialog: "Publish final report? This cannot be undone."
- On confirm → application transitions to `PUBLISHED`, workspace transitions to Phase 3

**Loading moment:**
- Same as generation: full Pages 4–5 area blocked
- Both Regenerate + Publish disabled while in progress

---

### Screen 9 — Application Workspace: Phase 3 (state: `PUBLISHED`)

**Content visible:**
- Pages 1–5 (complete final report, read-only)
- "Published" status banner

**No actions available.**
- Generate / Regenerate / Publish buttons absent or visibly disabled

---

## Global Behaviors

### State refresh / polling
- All list pages (Upload Queue, Generated Reports, Dashboard) reflect live state
- When a state changes, affected rows update without full page reload
- Rows in transition show subtle loading indicator if re-fetching

> **Backend gap:** No polling endpoint or WebSocket exists yet. Live row refresh is a target behavior that requires a status query endpoint (e.g. `GET /applications?status_filter=...`) that the frontend can poll at an interval.

### Navigation guards
- If generation is in progress and interviewer tries to navigate away → warning: "Generation in progress. Are you sure you want to leave?"

### Empty states
- Every list page has a defined empty state message (no blank screens)

### Toasts / notifications
- Upload success/failure → toast
- Assignment → toast
- Publish → toast or success banner

---

## Loading Moments Summary

| Moment | Scope | UI treatment |
|---|---|---|
| PDF row processing | Row-level | Spinner on that row only |
| Retry | Row-level | Row flips to spinner immediately |
| Generate (first time) | Pages 4–5 area | Skeleton + disabled buttons |
| Regenerate | Pages 4–5 area | Skeleton + disabled buttons |
| Page initial load | Full page | Page-level spinner / skeleton list |
| State refresh (polling) | Row-level | Subtle indicator on affected rows |
| PDF / pages content load | Content panel | Skeleton placeholder |
