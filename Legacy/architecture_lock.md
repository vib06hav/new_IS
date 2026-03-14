# `architecture_lock.md`

**(Stage 1.5 — ROS v1 Integrated, Architectural Invariants Preserved)**

---

# 1. Purpose

This document defines non-negotiable architectural invariants.

These constraints exist to:

* Prevent scope drift
* Prevent architectural creep
* Prevent infra instability
* Preserve deterministic-first discipline
* Preserve single-LLM boundary
* Preserve synchronous execution model

Stage 1.5 integrates ROS v1 as a presentation-layer contract.

Stage 1.5 does not relax any architectural invariants defined in Stage 1.

---

# 2. Core Architectural Invariants

## 2.1 Deterministic-First

Agents 1–11 remain strictly deterministic.

They must:

* Perform structured extraction only
* Avoid interpretation
* Avoid ranking
* Avoid scoring
* Avoid normalization
* Avoid inference
* Avoid LLM invocation

No part of deterministic extraction may depend on LLM output.

This invariant remains absolute.

---

## 2.2 Single LLM Call

Exactly one LLM call per application.

This call:

* Occurs after canonical assembly
* Generates only thematic structure (ROS Page 4–5)
* Does not rewrite canonical content
* Does not trigger recursive calls
* Is not retried
* Has no fallback model

No additional LLM calls are permitted for:

* Refinement
* Summarization
* Correction
* Validation
* Highlight generation

Single-call invariant remains absolute in Stage 1.5.

---

## 2.3 Canonical–Presentation Separation

Canonical representation is internal structural truth.

ROS v1 is a derived presentation artifact.

Canonical must not:

* Embed page grouping
* Embed theme grouping
* Embed question grouping
* Be reshaped to satisfy UI layout

ROS projection must not:

* Mutate canonical
* Collapse canonical collections
* Rewrite canonical text
* Introduce new canonical fields

Separation of canonical and ROS layers is mandatory.

---

## 2.4 Synchronous Execution Model

The system remains fully synchronous.

No:

* Background workers
* Job queues
* Redis
* Celery
* Task schedulers
* Deferred execution models

Stage 1.5 does not introduce async behavior.

---

## 2.5 Infrastructure Freeze

Stage 1 infrastructure remains unchanged:

* Docker topology unchanged
* Services unchanged
* No additional containers
* No service separation
* No microservices
* No event-driven architecture

Environment configuration remains unchanged.

No new environment variables introduced for Stage 1.5.

---

## 2.6 Database Stability

No schema migrations introduced.

No new tables.

No new columns.

No new relational joins.

`canonical_records` and `synthesis_records` remain JSONB-backed.

ROS v1 replaces the internal structure of `synthesis_output` only.

Schema remains stable.

---

## 2.7 No Evaluation Logic

System must not:

* Score applicants
* Rank applicants
* Predict outcomes
* Assess strengths or weaknesses
* Compare applicants
* Normalize grades
* Compute competitiveness metrics

The LLM must not introduce evaluative language.

This remains enforced through:

* Prompt constraints
* Policy guard validation

---

## 2.8 No Recursive Reasoning

The system must not:

* Chain LLM outputs
* Feed LLM outputs back into LLM
* Perform iterative refinement
* Store intermediate reasoning

All reasoning is bounded to a single LLM invocation.

---

## 3. Stage 1.5 Additions (Logical Only)

Stage 1.5 introduces:

* Deterministic ROS projection layer (Pages 1–3)
* Structured LLM thematic output (Pages 4–5)
* Entity ID anchoring
* Reference validation enforcement

Stage 1.5 does not introduce:

* Async execution
* Additional LLM calls
* Infrastructure change
* Database schema change
* New services

All additions are logical-layer only.

---

# 4. Enforcement Rules

If any proposed change requires:

* Additional LLM calls
* Async execution
* Schema migration
* New tables
* New services
* Breaking canonical–presentation separation

Then that change belongs to a later stage.

It must not be introduced in Stage 1.5.

---

# 5. Stage 1.5 Invariant Check

| Invariant                         | Status |
| --------------------------------- | ------ |
| Deterministic-first preserved     | ✅      |
| Single LLM call preserved         | ✅      |
| Canonical separate from ROS       | ✅      |
| No async introduced               | ✅      |
| No infra change introduced        | ✅      |
| No schema migration required      | ✅      |
| No evaluation logic introduced    | ✅      |
| No recursive reasoning introduced | ✅      |

---
