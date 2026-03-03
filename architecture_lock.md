# 📄 `architecture_lock.md`

**(LLM Compliance & Enforcement Document)**

---

# Architecture Lock

## Non-Negotiable Implementation Constraints

---

## 1. Purpose of This Document

This document defines strict architectural constraints that must not be violated.

Any LLM generating:

* Code
* Schema
* Infrastructure layout
* Folder structure
* Service definitions
* API design

must comply with all rules defined here.

If a proposed implementation conflicts with this document, this document takes precedence.

---

## 2. Logical Architecture Is Frozen

The following architectural characteristics are permanently locked:

1. Deterministic-first processing
2. Single LLM synthesis boundary
3. Canonical representation as sole LLM input
4. Non-evaluative system design
5. Collection-based internal representation
6. Versioned canonical model
7. Stage-based infrastructure evolution
8. Logical pipeline invariance across stages

No implementation may alter these properties.

---

## 3. LLM Usage Restrictions

The system must:

* Make exactly one LLM call per application.
* Use LLM only for synthesis.
* Provide only canonical structured data to the LLM.

The system must not:

* Use multiple LLM calls.
* Use recursive reasoning.
* Use self-reflection loops.
* Use tool-calling chains.
* Use dynamic reasoning graphs.
* Use LangChain.
* Use LangGraph.
* Use AutoGen.
* Use CrewAI.
* Use Semantic Kernel.
* Introduce additional agent frameworks.

LLM orchestration frameworks are prohibited.

---

## 4. Deterministic Extraction Enforcement

All structural processing must be deterministic.

LLM must not:

* Parse PDFs.
* Detect sections.
* Extract structured fields.
* Infer missing data.
* Normalize grades.
* Compute academic trends.
* Perform cross-application comparison.

All extraction must be implemented in deterministic Python logic.

---

## 5. Canonical Model Constraints

The canonical representation must:

* Be collection-based.
* Avoid rigid key paths such as:

  * academics.class_12
  * tests.sat
* Avoid fixed academic-level keys.
* Support extensibility.
* Include canonical_version.
* Separate identifiers (PII) from extracted data.

The canonical model must not:

* Hardcode academic year keys.
* Hardcode test names.
* Collapse collections into fixed structures.
* Mix PII with extracted content.
* Embed synthesis output inside extracted data.

---

## 6. Evaluation Prohibition

The system must not implement:

* Applicant scoring.
* Ranking logic.
* Strength/weakness labeling.
* Concern detection.
* Grade normalization.
* Predictive admissions modeling.
* Comparative analysis.
* Performance inference.

LLM output must remain neutral and traceable.

---

## 7. Service Boundary Restrictions

Before Stage 4:

* The system must not be split into multiple microservices.
* All logical agents must remain internal modules.
* No premature service separation is allowed.
* No Kubernetes.
* No service mesh.
* No distributed architecture.

After Stage 4:

* Service separation must follow predefined boundaries.
* Agents remain internal modules.
* Agents are not individual microservices.

---

## 8. Stage Discipline Enforcement

Infrastructure evolves in stages.

The system must not:

* Introduce Redis before Stage 2.
* Introduce object storage before Stage 3.
* Introduce service separation before Stage 4.
* Introduce security hardening beyond stage definition.
* Introduce cloud infrastructure before Stage 6.

Stage migration must not alter logical pipeline.

---

## 9. Schema Governance Rules

LLM-generated implementation must:

* Define database tables explicitly.
* Use JSON fields only where appropriate.
* Maintain canonical_version tracking.
* Avoid over-normalization of academic records.

LLM must not:

* Invent additional canonical layers.
* Introduce dynamic schema inference.
* Add unnecessary abstraction layers.

---

## 10. Prompt Discipline

LLM implementation must:

* Reference canonical categories, not rigid key paths.
* Avoid hardcoded assumptions about academic structure.
* Preserve extensibility.
* Avoid hidden global state.
* Avoid implicit inference logic.

---

## 11. Security Baseline (Stage-Aware)

Even in early stages:

* JWT must be used for authentication.
* Passwords must be hashed.
* Role-based access control must exist.

LLM must not:

* Introduce third-party auth providers.
* Introduce SaaS auth services.
* Introduce unnecessary security frameworks.

Security evolves by stage only.

---

## 12. Architectural Change Protocol

If an implementation requires violating any rule in this document:

* The change must be explicitly flagged.
* The architectural implication must be described.
* Approval must be given before proceeding.

Silent deviations are not permitted.

---

## 13. Enforcement Statement

This document supersedes:

* Optimization suggestions
* Framework recommendations
* Alternative architecture proposals
* LLM-generated “improvements”

If conflict exists between convenience and this document, this document prevails.

---

End of Document.

---


