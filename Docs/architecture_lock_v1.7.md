# `architecture_lock_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis — Architectural Invariants)**

---

## 1. Purpose of This Document

This document defines the non-negotiable architectural invariants of the AG_InterviewStandardiser system as of Stage 1.7.

An architectural invariant is a rule that cannot be violated, relaxed, or worked around within this stage. Any proposed change that requires violating an invariant does not belong to Stage 1.7. It must be deferred to a future stage boundary decision.

These invariants exist to:

- Prevent scope drift during implementation
- Prevent architectural creep across stage boundaries
- Preserve infrastructure stability
- Preserve the deterministic-first discipline of the extraction pipeline
- Preserve a bounded, auditable LLM contact surface
- Preserve synchronous, traceable pipeline execution
- Prevent the system from becoming evaluative

This document is a constraint document. It does not describe how the system works in detail — it defines the rules that all other system components must conform to. Detailed component behavior is governed by `signal_architecture_spec_v1.7.md`, `agent_pipeline_spec_v1.7.md`, `llm_synthesis_contract_v1.7.md`, and related documents.

---

## 2. System Context

### 2.1 What the System Is

The AG_InterviewStandardiser processes structured application PDFs submitted by applicants and produces a **Report Output Specification (ROS v1)** artifact for use by human interviewers. The ROS artifact contains five pages of structured interview preparation content.

The system standardizes applicant data into a structured, consistent format. It does not evaluate applicants. It does not predict admissions outcomes. It does not rank or score applicants relative to one another or against any benchmark.

### 2.2 Pipeline Summary

The system pipeline executes in a single synchronous pass:

```
PDF Upload
    ↓
Agent 0 — Orchestrator
    ↓
Agents 1–11 — Deterministic Extraction
    ↓
Canonical Representation (v1.1)
    ↓
Deterministic ROS Projection (Pages 1–3)
    ↓
Deterministic Signal Detection
    ↓
Canonical Projection Construction
    ↓
LLM Call 1 — Signal Interpretation
    ↓
Signal Validation
    ↓
Signal–Evidence Bundle Construction
    ↓
LLM Call 2 — Interview Generation
    ↓
Output Validation
    ↓
ROS Assembly
    ↓
Persist Canonical + ROS v1
```

### 2.3 Key Definitions

**Canonical Representation** — The authoritative, structured, versioned (v1.1) output of Agents 1–11. Contains all extracted applicant data in collection-based form. Stored as JSONB in `canonical_records`. Never modified by any downstream component.

**LLM Call** — A single invocation of the language model API. The system permits exactly two LLM calls per application. Call 1 performs signal interpretation. Call 2 performs interview generation.

**Deterministic Component** — Any pipeline stage that produces the same output for the same input without LLM involvement. All stages except LLM Call 1 and LLM Call 2 are deterministic.

**Policy Guard** — The deterministic validation module (`policy/guard.py`) that enforces prohibited language rules and entity ID reference validity. Invoked after both LLM calls.

**ROS v1** — The final five-page output artifact. Pages 1–3 are produced deterministically. Pages 4–5 are produced by LLM Call 2 and validated before inclusion.

---

## 3. Core Architectural Invariants

### 3.1 Deterministic-First Extraction

Agents 1 through 11 are strictly deterministic. They extract structured data from the application PDF without any LLM involvement.

These agents must:

- Perform structured data extraction only
- Avoid interpretation of applicant data
- Avoid ranking or ordering by inferred significance
- Avoid scoring or grading applicant attributes
- Avoid normalization that introduces judgment
- Avoid inference beyond what is structurally present in the PDF
- Never invoke an LLM at any point

No part of the deterministic extraction pipeline may depend on LLM output. The canonical representation produced by Agent 11 must be entirely derivable from the PDF alone, without any language model involvement.

This invariant is absolute. It cannot be relaxed for any agent in the range 1–11 for any reason within Stage 1.7.

---

### 3.2 Exactly Two Bounded LLM Calls Per Application

The system permits exactly two LLM calls per application. No more, no fewer.

**LLM Call 1 — Signal Interpretation:**
- Receives the canonical projection and deterministic signal collection
- Produces interpreted signals only
- Does not generate interview questions, themes, or narrative summaries
- Does not receive raw canonical JSONB

**LLM Call 2 — Interview Generation:**
- Receives the validated signal-evidence bundle only
- Produces ROS Pages 4–5 content (themes and question groups)
- Does not receive the canonical projection
- Does not receive raw Call 1 output

No additional LLM calls are permitted for any purpose, including:

- Refinement of Call 1 or Call 2 output
- Correction of failed output
- Summarization of canonical content
- Validation of any kind
- Highlight generation
- Any reasoning task not explicitly assigned to Call 1 or Call 2

The two-call boundary is absolute. It cannot be extended within Stage 1.7.

---

### 3.3 Call Independence

LLM Call 2 receives only the validated signal-evidence bundle. It does not receive:

- The full canonical representation
- The raw canonical projection passed to Call 1
- The unvalidated output of Call 1
- Confidence scores or extraction metadata
- Any content from prior applications

The signal-evidence bundle is the sole input channel from Call 1's reasoning into Call 2. This bundle contains only validated interpreted signals paired with their supporting canonical evidence. Nothing that has not passed through the signal validation layer may reach Call 2.

---

### 3.4 Sequential Call Execution

LLM Call 1 must complete, and its output must pass signal validation, before LLM Call 2 is invoked.

There is no parallel execution of the two LLM calls. There is no mechanism by which Call 2 can begin before Call 1 validation is confirmed successful. The pipeline is strictly sequential at every stage.

---

### 3.5 No Fallback and No Retry

If either LLM call fails — whether due to validation failure, malformed output, or API error — the pipeline aborts for that application.

- No corrective LLM call is triggered
- No retry of the failed call is attempted
- There is no fallback to any prior synthesis model
- The application is marked as failed with a logged reason
- No partial ROS artifact is produced

The absence of retry and fallback logic is intentional. It ensures that every ROS artifact that is produced has passed through the full validated pipeline. A partial or unvalidated output is not acceptable.

---

### 3.6 Signal Validation is Mandatory and Non-Bypassable

The output of LLM Call 1 must pass deterministic signal validation before any downstream step proceeds. Signal validation verifies:

- The response is valid JSON conforming to the interpreted signal schema
- All referenced entity IDs exist in the entity ID map provided to Call 1
- All referenced deterministic signal IDs exist in the signal collection provided to Call 1
- No prohibited language appears in any signal title or description
- All signal IDs follow the required format and are unique

No partial acceptance of signals is permitted. If any signal in the collection fails validation, the entire collection is rejected and the pipeline aborts.

Signal validation cannot be disabled, skipped, or deferred for any application.

---

### 3.7 Canonical–Presentation Separation

The canonical representation is the internal structural truth of the system. The ROS v1 artifact is a derived presentation output. These two layers must remain strictly separated.

The canonical representation must not:

- Embed page groupings derived from ROS structure
- Embed theme or question groupings
- Store fields whose purpose is to satisfy a presentation layout
- Be reshaped or restructured to match ROS page requirements

The ROS projection and synthesis layers must not:

- Modify any field in the canonical representation
- Collapse or merge canonical collections
- Rewrite canonical text values
- Introduce new fields into the canonical representation
- Store intermediate reasoning artifacts in canonical records

Canonical projections are read-only views. They do not modify the canonical representation. The canonical record stored in `canonical_records` after Agent 11 completes is identical to the canonical record present when ROS assembly completes.

---

### 3.8 Synchronous Execution Model

The pipeline executes within a single synchronous request lifecycle. All stages from PDF ingestion to ROS persistence execute within the same synchronous process.

The system does not use:

- Background workers
- Job queues of any kind
- Redis
- Celery or equivalent task queue frameworks
- Task schedulers
- Deferred or asynchronous execution models
- Event-driven pipeline orchestration

Every stage completes before the next begins. The pipeline has no deferred steps. A caller that submits a PDF receives the completed ROS artifact (or a failure response) within the same request.

---

### 3.9 Infrastructure Freeze

The infrastructure topology is frozen for Stage 1.7. No infrastructure changes are introduced.

Specifically:

- Docker topology remains unchanged
- All existing services remain unchanged
- No additional containers are introduced
- No service separation or decomposition occurs
- No microservice architecture is introduced
- No event-driven infrastructure is introduced
- No new environment variables are required for Stage 1.7 functionality

All Stage 1.7 additions are implemented within the existing application layer. Infrastructure changes of any kind belong to a future stage.

---

### 3.10 Database Stability

No database schema changes are introduced in Stage 1.7.

- No new tables
- No new columns on existing tables
- No new indexes beyond those already defined
- No schema migrations
- No new relational joins

The four existing tables — `users`, `applications`, `canonical_records`, `synthesis_records` — remain structurally unchanged.

Interpreted signals are pipeline-ephemeral by default. If signal data is required for auditability or debugging, it may be embedded as a structured key within the existing `synthesis_records.synthesis_output` JSONB field alongside the ROS artifact. This requires no schema change. The decision to include or exclude signal data in `synthesis_output` must be made explicitly before Stage 1.7 goes to production and must not be left ambiguous.

---

### 3.11 No Evaluation Logic

The system must not evaluate applicants in any form.

The system must not:

- Assign scores to applicants or their attributes
- Rank applicants against one another
- Rank applicants against any benchmark or standard
- Predict admissions outcomes or likelihood
- Assess strengths or weaknesses
- Compare applicants to one another
- Compute competitiveness metrics
- Normalize grades in a way that implies relative standing

This prohibition applies to all system components — deterministic and LLM. The policy guard enforces a prohibited language list against all LLM-generated content. The following terms must not appear in any LLM-generated content at either Call 1 or Call 2. This list is enforced by the Policy Guard at both validation stages:
"Strength"
"Weakness"
"Outstanding"
"Exceptional"
"Deficiency"
"Below average"
"Underperformance"
"High potential"
"Top candidate"
"Risk factor"
"Admit"
"Reject"
"Likelihood"
"Impressive"
"Concerning"
"Excellent"
"Poor"
"Weak"
"Strong"
"Competitive"
"Uncompetitive"

The authoritative definition of this list including enforcement rules is in `llm_synthesis_contract_v1.7.md` Section 5.

No change to prompt design, projection content, or system configuration may introduce evaluative reasoning into any pipeline stage.

---

### 3.12 No Recursive Reasoning

The system must not engage in recursive or iterative LLM reasoning.

Specifically:

- LLM Call 1 output must not be fed back into LLM Call 1
- LLM Call 2 output must not be fed back into LLM Call 2 or into LLM Call 1
- No LLM output may be used as a prompt input to any LLM call
- No iterative refinement loop involving an LLM is permitted
- No intermediate LLM reasoning is stored and reused across calls

The only permissible data flow from Call 1 to Call 2 is through the validated signal-evidence bundle, constructed deterministically by the bundle construction step. This is a structured data handoff, not a reasoning chain.

---

### 3.13 Canonical Projection Immutability

Canonical projections are read-only, pipeline-ephemeral views. They are constructed from the canonical representation for a specific LLM reasoning task and discarded after that task completes.

A canonical projection:

- Does not modify the canonical representation in any way
- Is not stored in any database table or column
- Cannot be used as input to a future pipeline run
- Cannot be retrieved or inspected after the pipeline run completes

The canonical record in `canonical_records` is identical before and after projection construction.

---

### 3.14 ROS Output Schema Stability

The ROS v1 output schema — all five pages — is unchanged in Stage 1.7.

Stage 1.7 changes how Pages 4–5 are produced (two-stage signal-guided synthesis replaces single-call synthesis). It does not change what Pages 4–5 contain or how they are structured.

The ROS v1 five-page output schema is unchanged in Stage 1.7. The complete schema is defined in `ROS_v1.7.md`.

---

## 4. What Stage 1.7 Introduces

Stage 1.7 introduces the following additions to the existing system. All additions are logical-layer only.

**New pipeline stages:**
- Deterministic signal detection (Agent 12)
- Canonical projection construction (Agent 13)
- LLM Call 1 — Signal interpretation (Agent 14)
- Signal validation — Call 1 invocation of Policy Guard
- Signal-evidence bundle construction (Agent 15)
- LLM Call 2 — Interview generation (Agent 16)
- Output validation — Call 2 invocation of Policy Guard

**New artifacts (all pipeline-ephemeral):**
- Deterministic signal collection
- Canonical projection (Call 1 context)
- Interpreted signal collection
- Signal-evidence bundle

**No infrastructure changes. No schema changes. No new tables. No new API routes. No async execution.**

---

## 5. What Stage 1.7 Does Not Introduce

The following are explicitly out of scope for Stage 1.7. Any proposal to introduce them within this stage violates the architecture lock.

- A third LLM call of any kind
- Retry logic for failed LLM calls
- Fallback synthesis paths
- Async or deferred pipeline execution
- New database tables or columns
- Infrastructure changes of any kind
- New Docker services or containers
- Changes to the ROS v1 output schema
- Changes to the canonical representation schema
- Changes to Agents 1–11
- Evaluation logic of any kind
- Applicant comparison or ranking logic

---

## 6. Enforcement Rule

If any proposed implementation change within Stage 1.7 requires:

- More than two LLM calls per application
- Retry or fallback on LLM failure
- Async or deferred execution
- A database schema migration
- A new table or column
- An infrastructure change
- Breaking the canonical–presentation separation
- Modifying canonical data in any downstream stage
- Introducing evaluative language or logic

Then that change does not belong to Stage 1.7. It must be deferred to a future stage boundary decision and must not be implemented under the Stage 1.7 lock.

---

## 7. Invariant Check

| Invariant | Description | Status |
|---|---|---|
| 3.1 | Deterministic-first extraction — Agents 1–11 use no LLM | ✅ |
| 3.2 | Exactly two bounded LLM calls per application | ✅ |
| 3.3 | Call 2 receives only validated signal-evidence bundle | ✅ |
| 3.4 | Sequential call execution — Call 1 validated before Call 2 invoked | ✅ |
| 3.5 | No fallback, no retry on LLM failure | ✅ |
| 3.6 | Signal validation mandatory and non-bypassable | ✅ |
| 3.7 | Canonical–presentation separation enforced | ✅ |
| 3.8 | Synchronous execution model — no async or deferred execution | ✅ |
| 3.9 | Infrastructure freeze — no topology changes | ✅ |
| 3.10 | Database stability — no schema migrations, no new tables | ✅ |
| 3.11 | No evaluation logic in any pipeline component | ✅ |
| 3.12 | No recursive reasoning — no LLM output fed back into LLM | ✅ |
| 3.13 | Canonical projection immutability — projections are ephemeral and read-only | ✅ |
| 3.14 | ROS output schema unchanged | ✅ |

---

*Architecture Lock Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis*