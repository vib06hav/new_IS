# 📄 `stage_1_scope_lock.md`

**(Stage 1 — Structured MVP Boundary Enforcement)**

---

# Stage 1 Scope Lock

## Structured MVP — Infrastructure Formalization Only

---

## 1. Purpose

This document defines the strict implementation boundary for **Stage 1 (Structured MVP)**.

Stage 1 exists to:

* Formalize persistence using PostgreSQL.
* Introduce containerization via Docker.
* Harden authentication implementation.
* Stabilize configuration handling.
* Introduce minimal structured logging.

Stage 1 does **not** modify logical architecture.

Stage 1 does **not** evolve system behavior.

Stage 1 is an infrastructure formalization stage.

If any implementation alters logical pipeline behavior, Stage 1 scope is violated.

---

## 2. Architectural Invariance (Non-Negotiable)

All architectural characteristics defined in:

* `architecture_lock.md`
* `system_overview.md`
* `agent_pipeline_spec.md`
* `canonical_model_philosophy.md`
* `llm_synthesis_contract.md`

remain fully binding.

Stage 1 must preserve:

1. Deterministic-first processing.
2. Single LLM synthesis boundary.
3. Canonical representation as sole LLM input.
4. Non-evaluative system design.
5. Collection-based canonical structure.
6. Versioned canonical model.
7. Fixed agent execution order.
8. Stage-based infrastructure evolution discipline.

No deviations are permitted.

---

## 3. What Stage 1 Is Allowed to Introduce

Stage 1 may introduce only the following changes:

### 3.1 Database Formalization

* Replace SQLite (if used) with PostgreSQL.
* Introduce explicit schema migration tooling (e.g., Alembic).
* Use JSONB for canonical storage.
* Formalize table constraints and indexes.

No schema inference is permitted.

Canonical structure philosophy must remain unchanged.

No additional logical tables beyond those defined in Stage 0 Finalization Document may be introduced.

---

### 3.2 Containerization

* Introduce Dockerfile.
* Introduce docker-compose.yml.
* Define containers for:

  * API service
  * PostgreSQL database

No additional infrastructure containers are permitted.

---

### 3.3 Authentication Hardening

* Ensure bcrypt password hashing.
* Ensure JWT-based authentication.
* Ensure role-based access control.

No third-party auth providers.
No OAuth.
No SaaS identity services.

---

### 3.4 Configuration Formalization

* Define required environment variables.
* Externalize configuration.
* Remove hardcoded values.

No secret manager.
No cloud configuration system.

---

### 3.5 Basic Structured Logging

* Introduce minimal logging.
* Log:

  * Application creation
  * Pipeline start
  * Pipeline completion
  * Pipeline failure
  * LLM invocation start/end
  * Policy validation result

Logging must not:

* Introduce observability stacks.
* Introduce distributed tracing.
* Introduce monitoring systems.

Logs may be stdout-based.

---

## 4. Explicit Prohibitions (Still Not Allowed in Stage 1)

The following remain strictly prohibited:

### 4.1 Async Processing

* No Redis.
* No background workers.
* No RQ.
* No Celery.
* No Kafka.
* No job queue.
* No polling model.
* No job status endpoint.

Processing remains synchronous.

---

### 4.2 Storage Hardening

* No MinIO.
* No S3.
* No object storage.
* No file encryption layer.

PDFs remain locally stored.

---

### 4.3 Service Separation

* No microservices.
* No service-to-service communication.
* No LLM service isolation.
* No worker container separation.

All logical agents remain internal modules within a single API container.

---

### 4.4 LLM Behavior Expansion

Stage 1 must not:

* Introduce additional LLM calls.
* Introduce retries.
* Introduce reflection loops.
* Introduce orchestration frameworks.
* Modify prompt philosophy.
* Modify output structure.

LLM invocation remains exactly as defined in Stage 0.

---

### 4.5 Canonical Model Alteration

Stage 1 must not:

* Introduce fixed academic-level keys.
* Introduce normalization.
* Collapse collections.
* Embed evaluation flags.
* Merge PII into extracted data.
* Modify canonical_version semantics.

The canonical model remains identical to Stage 0.

---

### 4.6 Evaluation Introduction

Stage 1 must not introduce:

* Applicant scoring.
* Ranking.
* Concern detection.
* Strength/weakness framing.
* Trend analysis.
* Predictive modeling.

All non-evaluative constraints remain binding.

---

## 5. Database Schema Governance

Stage 1 may formalize schema details but must:

* Preserve canonical_data as collection-based JSON.
* Preserve separation between:

  * applications
  * canonical_records
  * synthesis_records
* Preserve canonical_version tracking.
* Preserve one-to-one relationship between application and canonical record.

Schema formalization must not restructure canonical logic.

---

## 6. Pipeline Execution Model

The logical pipeline defined in `agent_pipeline_spec.md` remains unchanged.

Execution model remains:

```
upload → deterministic agents → canonical assembly → single LLM call → policy validation → store → return
```

Execution remains synchronous within request lifecycle.

No background execution model is introduced.

---

## 7. Stage Transition Discipline

If implementation requires:

* Async job handling
* Queue introduction
* File storage change
* Service separation
* LLM behavior change
* Canonical restructuring

Then Stage 1 must be considered complete and migration to Stage 2 must be explicitly initiated.

Silent scope expansion is prohibited.

---

## 8. Compliance Requirement

Any implementation produced under Stage 1 must:

* Remain compliant with `architecture_lock.md`
* Remain compliant with `system_overview.md`
* Remain compliant with `agent_pipeline_spec.md`
* Remain compliant with `canonical_model_philosophy.md`
* Remain compliant with `llm_synthesis_contract.md`

If conflict arises, `architecture_lock.md` prevails.

---

## 9. Enforcement Statement

Stage 1 is:

* Infrastructure formalization.
* Stability hardening.
* Configuration clarity.
* Persistence strengthening.

Stage 1 is not:

* Architectural redesign.
* Logic expansion.
* Scalability engineering.
* Async transformation.
* Service separation.
* Production security hardening.

Any deviation from this boundary invalidates Stage 1 scope.

---

End of Document.

---

