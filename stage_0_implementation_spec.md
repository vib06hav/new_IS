# 📄 `stage_0_implementation_spec.md`

**(Stage 0 — Local Core Engine Implementation Specification)**

---

# Stage 0 — Local Core Engine

## Implementation Specification

---

## 1. Purpose of Stage 0

Stage 0 exists to validate the core logical engine:

* Deterministic extraction
* Canonical representation assembly
* Single LLM synthesis
* Policy validation
* Basic authentication
* Local persistence

Stage 0 is not production-ready.

Stage 0 is an architectural proof stage.

Only minimal infrastructure is permitted.

---

## 2. Architectural Scope of Stage 0

Stage 0 must implement:

* Single FastAPI application
* Synchronous processing
* Local file storage
* Simple relational database
* JWT-based authentication
* Deterministic agent pipeline
* Canonical representation model
* Single LLM client wrapper
* Policy guard module

Stage 0 must not implement:

* Async job queues
* Redis
* Background workers
* Object storage
* Multiple services
* Reverse proxy
* HTTPS enforcement
* Audit logging
* Multi-region support
* Cloud infrastructure

---

## 3. System Structure (Single Service Only)

Stage 0 must be implemented as a single FastAPI service.

No service separation is allowed.

Conceptual project structure:

```
app/
  main.py
  config.py
  database.py
  auth/
  agents/
  canonical/
  llm/
  policy/
  models/
```

This structure is conceptual.

Exact naming may be defined during implementation.

All agents must remain internal Python modules.

---

## 4. API Contract (Stage 0)

### 4.1 Authentication Endpoints

* POST /register
* POST /login

JWT-based authentication required.

Passwords must be hashed using bcrypt.

Roles must include at minimum:

* admin
* interviewer

---

### 4.2 Application Processing Endpoint

* POST /applications/upload

Behavior:

* Accept PDF upload.
* Save file locally.
* Run full deterministic pipeline synchronously.
* Build canonical representation.
* Call LLM synthesis once.
* Run policy validation.
* Store canonical + synthesis output.
* Return final interviewer report in response.

No asynchronous job handling.

No job polling endpoints.

---

### 4.3 Retrieval Endpoint

* GET /applications/{id}

Returns:

* Stored synthesis output
* Not raw canonical unless explicitly required

---

## 5. Database Requirements (Minimal)

Stage 0 database must include:

### users

* id
* email
* password_hash
* role
* created_at

### applications

* id
* uploaded_by
* file_path
* created_at

### canonical_records

* id
* application_id
* canonical_version
* canonical_data (JSON)
* created_at

### synthesis_records

* id
* application_id
* synthesis_output (JSON or text)
* created_at

No job table required in Stage 0.

---

## 6. Canonical Representation Requirements

The canonical model must:

* Follow canonical_model_philosophy.md
* Use collection-based structures
* Include canonical_version
* Separate identifiers logically
* Not embed synthesis inside extraction fields

Pydantic models must reflect philosophy, not rigid schema assumptions.

---

## 7. Deterministic Agent Implementation

All agents must:

* Be implemented as synchronous Python functions.
* Accept structured input.
* Return structured output.
* Include confidence score.
* Avoid inference or evaluation.

Pipeline must execute in fixed order defined in agent_pipeline_spec.md.

No concurrency.

No async execution.

---

## 8. LLM Integration

LLM must be called through a single wrapper function.

The wrapper must:

* Accept canonical representation only.
* Inject invariant rules.
* Enforce llm_synthesis_contract.md.
* Return structured synthesis result.

No chaining.
No secondary calls.
No tool-calling.

---

## 9. Policy Guard

Policy validation must:

* Run after LLM synthesis.
* Scan for prohibited patterns.
* Reject or sanitize non-compliant output.
* Log violations.

Stage 0 may use simple pattern matching.

Policy guard configuration may be defined inline for Stage 0, provided it remains externalized as a clearly isolated configuration module and not embedded as implicit logic within agent code.

---

## 10. File Storage (Stage 0 Only)

PDF files must be stored:

* On local disk.
* Within a defined upload directory.

No object storage.
No external file services.

---

## 11. Configuration Requirements

Environment variables must include:

* DATABASE_URL
* JWT_SECRET
* LLM_ENDPOINT
* LLM_MODEL_NAME
* UPLOAD_DIRECTORY

No secret managers required at this stage.

---

## 12. Explicitly Out of Scope for Stage 0

The following are strictly prohibited:

* Redis
* Background workers
* Celery
* RQ
* Kafka
* MinIO
* S3
* NGINX
* HTTPS enforcement
* Kubernetes
* Multi-container orchestration
* Distributed microservices
* Audit logs
* Refresh tokens
* Role hierarchy expansion
* Multi-tenant configuration profiles
* Encryption beyond password hashing

Any introduction of the above violates Stage 0 scope.

---

## 13. Compliance Requirement

Implementation must:

* Comply with system_overview.md
* Comply with architecture_lock.md
* Comply with agent_pipeline_spec.md
* Comply with canonical_model_philosophy.md
* Comply with llm_synthesis_contract.md

If any conflict arises, architecture_lock.md prevails.

---

End of Document.

---

