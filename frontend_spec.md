# Frontend Specification (Aligned to Your Structure)

---

# 1. Admin Frontend

You have four distinct pages. We keep them as-is and define their roles clearly.

---

## A. Upload Queue Page

### Purpose

* Entry point for adding PDFs
* Monitor deterministic processing

---

### What it shows

For each uploaded PDF:

* File identifier (name or label)
* Current processing state:

  * PROCESSING
  * READY
  * FAILED
* Timestamp (optional but useful)

---

### Actions available

* Upload new PDF
* Retry processing (only if FAILED)

---

### Behavior

* Upload triggers deterministic pipeline immediately
* Status updates based on processing result
* No assignment allowed here

---

---

## B. Generated Reports Page

### Purpose

* Track all processed applications
* Central view of report lifecycle

---

### What it shows

For each application:

* File / applicant identifier

* Current state:

  * READY (processed, not assigned)
  * ASSIGNED (assigned, no draft yet)
  * DRAFT (generation started, pending publish)
  * PUBLISHED (final report complete)

* Assigned interviewer (if applicable)

---

### Actions available

* Assign interviewer (only if READY)
* View application (always after READY)

---

### Behavior

* This page reflects **end-to-end report progress**
* It updates automatically after:

  * assignment
  * draft creation
  * publish

---

---

## C. Interviewer Manager Page

### Purpose

* Manage interviewer accounts

---

### What it shows

For each interviewer:

* Identity info (name/email)
* Activity info (e.g., number of assigned applications)

---

### Actions available

* Create interviewer
* Remove interviewer

---

### Behavior

* Removing interviewer should be constrained if they have active assignments (system-level rule)

---

---

## D. Assignment Manager Page

### Purpose

* Provide a **global mapping view** of:

  * which interviewer is assigned to which application
  * current report status

---

### What it shows

For each assignment:

* Application identifier
* Assigned interviewer
* Current state:

  * ASSIGNED
  * DRAFT
  * PUBLISHED

---

### Behavior

* Read-only (as you specified static)
* Reflects real-time system state
* Useful for operational overview

---

---

# 2. Interviewer Frontend

You defined a single dashboard + workflow. We keep that structure.

---

## A. Interviewer Dashboard

### Purpose

* Entry point for all assigned work

---

### What it shows

For each assigned application:

* Application identifier
* Current state:

  * ASSIGNED (no draft yet)
  * DRAFT (in progress)
  * PUBLISHED (completed)

---

### Actions available

* Open application

---

---

## B. Application Workflow (after opening)

This is the working interface for one application.

---

## Phase 1 — Before Generation

### What is visible

* Raw PDF
* Pages 1–3 (deterministic output)

---

### Action available

* Generate report (Pages 4–5)

---

---

## Phase 2 — Draft State

Triggered after first generation.

---

### What is visible

* Pages 1–3 (unchanged)
* Pages 4–5 (generated draft)

---

### Actions available

* Regenerate (creates new draft)
* Publish

---

### Behavior

* Multiple regenerations allowed
* Each regeneration produces a new draft
* Only the latest draft is active

---

---

## Phase 3 — Published State

Triggered after publish.

---

### What is visible

* Pages 1–5 (complete report)

---

### Actions available

* None related to generation

---

### Behavior

* Pages 4–5 become immutable
* No further drafts allowed

---

---

# 3. State Synchronization Across Pages

---

## System-wide rule

Application state is the **single source of truth**.

All pages reflect it consistently.

---

## State transitions

```text
PROCESSING → READY → ASSIGNED → DRAFT → PUBLISHED
            ↘ FAILED
```

---

## Effects of state changes

---

### When PROCESSING → READY

* Upload Queue updates
* Generated Reports shows READY

---

### When READY → ASSIGNED

* Generated Reports updates
* Assignment Manager updates
* Interviewer Dashboard gets new item

---

### When ASSIGNED → DRAFT

* Generated Reports shows “pending publish”
* Assignment Manager reflects DRAFT
* Interviewer sees draft workspace

---

### When DRAFT → PUBLISHED

* All pages update:

  * Generated Reports → PUBLISHED
  * Assignment Manager → PUBLISHED
  * Interviewer Dashboard → PUBLISHED

---

# 4. Action Constraints (State-Based)

---

## Assignment

Allowed only when:

```text
state == READY
```

---

## Generate

Allowed only when:

```text
state == ASSIGNED or DRAFT
```

---

## Regenerate

Allowed only when:

```text
state == DRAFT
```

---

## Publish

Allowed only when:

```text
state == DRAFT
```

---

## All generation actions blocked when:

```text
state == PUBLISHED
```

---

# 5. Key Behavioral Guarantees

---

## 1. Deterministic output stability

* Pages 1–3 never change after READY

---

## 2. Draft isolation

* Pages 4–5 drafts do not affect other data

---

## 3. Single final output

* Only one published report per application

---

## 4. Global consistency

* All admin and interviewer pages reflect the same state

---

## 5. Clear lifecycle visibility

* Every application is always in a known state
* Every state implies allowed actions

---

# 6. Final Summary

Your frontend structure is:

---

## Admin

1. Upload Queue Page → ingestion + processing
2. Generated Reports Page → lifecycle tracking + assignment
3. Interviewer Manager → user management
4. Assignment Manager → global mapping view

---

## Interviewer

1. Dashboard → assigned work
2. Application workflow → generate → iterate → publish

---

And the system behavior is:

```text
Upload → Process → Assign → Generate → Iterate → Publish
```

with strict:

* state transitions
* role boundaries
* immutability after publish

