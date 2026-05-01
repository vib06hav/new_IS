# AG Interview Standardiser — Workflow & State Model

## 1. System Objective

The system processes application PDFs to produce a structured interview report in two stages:

* **Deterministic extraction** → builds factual, structured representation (Pages 1–3)
* **Interviewer-driven synthesis** → generates interview guidance (Pages 4–5)

The system introduces a **human-in-the-loop layer** where interviewers control interpretation before finalization.

---

# 2. Core Design Philosophy

### 1. Separation of responsibilities

* **System (deterministic layer)** → extracts and structures data
* **LLM + interviewer (interpretation layer)** → generates insights and questions
* **Admin (control layer)** → manages ingestion and assignment

---

### 2. Immutable vs Mutable layers

| Layer                 | Nature                     |
| --------------------- | -------------------------- |
| Canonical + Pages 1–3 | Immutable after processing |
| Pages 4–5 (drafts)    | Mutable, iterative         |
| Final report          | Immutable after publish    |

---

### 3. State-driven system

The system is governed by explicit **state transitions**, not implicit flags.

Every application moves through a defined lifecycle.

---

# 3. Application Lifecycle States

```text
UPLOADED
→ PROCESSING
→ READY
→ ASSIGNED
→ DRAFT
→ PUBLISHED
→ FAILED (optional branch)
```

---

## State Definitions

### 1. UPLOADED

* PDF received by system
* No processing completed yet

---

### 2. PROCESSING

* Deterministic pipeline (Agents 1–13) running
* System is extracting structured data

This state is short-lived in synchronous mode but must exist.

---

### 3. READY

* Deterministic processing successful
* Canonical representation created
* Pages 1–3 available

System is now ready for assignment.

---

### 4. ASSIGNED

* Application assigned to an interviewer
* Interviewer gains access

No generation has occurred yet.

---

### 5. DRAFT

* At least one draft of Pages 4–5 exists
* Interviewer can iterate (regenerate)

System is in an **interactive synthesis phase**

---

### 6. PUBLISHED

* Final version of Pages 4–5 selected
* Combined with Pages 1–3
* Full report (Pages 1–5) is frozen

No further modifications allowed.

---

### 7. FAILED

* Deterministic processing failed
* No canonical or Pages 1–3 available

System requires retry before proceeding.

---

# 4. Deterministic Processing Layer

## Purpose

Convert raw PDF into:

* Canonical structured data
* Deterministic signals
* ROS Pages 1–3

---

## Behavior

* Runs automatically after upload
* Executes once per application
* Produces immutable output

---

## Failure Handling

Two categories:

### Hard failure

* Pipeline breaks
* No usable output

→ State becomes `FAILED`

---

### Soft failure

* Missing or imperfect data
* Integrity issues

→ Still transitions to `READY`
→ Issues captured in internal reports

---

## Retry Behavior

* Failed applications can be reprocessed
* Retry does not create a new application
* Same PDF is reused

---

# 5. Interviewer Synthesis Layer

## Purpose

Transform structured data into:

* Themes
* Question groups

This corresponds to Pages 4–5.

---

## Input

* Canonical data
* Deterministic signals
* Entity-linked evidence

---

## Generation Flow

* Triggered manually by interviewer
* Runs interpretation + generation stages
* Produces a **draft**

---

## Draft Model

A draft represents:

* One version of Pages 4–5
* Generated from fixed canonical input

---

## Properties of Drafts

* Multiple drafts allowed
* Each regeneration produces a new version
* Drafts are private to interviewer
* Drafts do not affect Pages 1–3

---

## Iteration Loop

```text
Generate → Review → Regenerate → Repeat
```

* Canonical and signals remain constant
* Only interpretation changes

---

# 6. Publish Phase

## Purpose

Finalize the report.

---

## Behavior

* Interviewer selects latest draft
* System combines:

  * Pages 1–3 (deterministic)
  * Pages 4–5 (selected draft)

---

## Effects

* State transitions to `PUBLISHED`
* Report becomes immutable
* No further drafts allowed

---

## Output

* Full 5-page report (ROS artifact)
* Available to both admin and interviewer

---

# 7. Role-Based Interaction Model

---

## Admin Responsibilities

* Upload PDF
* View Pages 1–3 after processing
* Assign interviewer
* View final report after publish

---

## Admin Restrictions

* Cannot generate drafts
* Cannot modify Pages 4–5
* Cannot publish

---

## Interviewer Responsibilities

* View assigned applications
* Access Pages 1–3 and raw PDF
* Generate drafts (Pages 4–5)
* Iterate on drafts
* Publish final report

---

## Interviewer Restrictions

* Cannot access unassigned applications
* Cannot modify Pages 1–3
* Cannot re-run deterministic pipeline

---

# 8. Visibility Model

---

## Before Publish

### Admin sees:

* Raw PDF
* Pages 1–3
* Status (assigned / not generated)

### Interviewer sees:

* Raw PDF
* Pages 1–3
* Draft workspace (if generated)

---

## After Publish

Both admin and interviewer see:

* Pages 1–5 (final report)

No one can:

* regenerate
* modify output

---

# 9. State-Driven Behavior Rules

---

## Assignment

Allowed only when:

```text
state == READY
```

---

## Generation

Allowed only when:

```text
state == ASSIGNED or DRAFT
```

---

## Publish

Allowed only when:

```text
state == DRAFT
```

---

## Blocked Actions

* No generation after `PUBLISHED`
* No assignment before `READY`
* No publish without draft

---

# 10. Processing vs Interaction Separation

The system operates in two distinct phases:

---

## Phase A — System-driven (no user intervention)

* Upload
* Deterministic extraction
* Data structuring

---

## Phase B — Human-driven

* Draft generation
* Iteration
* Publish

---

This separation ensures:

* reliability of data
* flexibility of interpretation

---

# 11. Key Guarantees

---

## 1. Data integrity

* Canonical data is never modified after extraction

---

## 2. Deterministic consistency

* Pages 1–3 remain stable across all drafts

---

## 3. Controlled interpretation

* All generated content is interviewer-mediated

---

## 4. Traceable reasoning

* Themes and questions are grounded in extracted data

---

## 5. Immutable final output

* Published reports cannot change

---

# 12. System Summary

The system transforms:

```text
Raw PDF
→ Structured evidence (Pages 1–3)
→ Interpreted insights (Pages 4–5)
→ Final interview report (Pages 1–5)
```

with:

* deterministic extraction
* iterative human-supervised synthesis
* strict state-controlled transitions

---

# Bottom line

You’re building a system that is:

* **deterministic at the data layer**
* **interactive at the reasoning layer**
* **state-driven at the workflow layer**
* **immutable at the final output layer**

---

If you want next, the most useful follow-up would be:
→ a **tight UI flow doc (screen-by-screen with states)** so frontend doesn’t drift from this logic
