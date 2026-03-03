# 📄 `canonical_model_philosophy.md`

**(Canonical Representation Governance Specification)**

---

# Interview Preparation Platform

## Canonical Model Philosophy (Schema Governance Specification)

---

## 1. Purpose of This Document

This document defines the governing principles of the canonical representation.

It does not define:

* Exact field names
* Database column names
* JSON key names
* Storage schema

It defines structural philosophy and invariants.

All implementations must comply with this philosophy.

---

## 2. Definition of Canonical Representation

The canonical representation is the internal structured form of an application after deterministic extraction and structural analysis.

It serves as:

* The sole input to LLM synthesis
* The structured source of truth
* The transport-level representation of extracted content
* The basis for traceable output generation

The canonical representation is not equivalent to:

* Database schema
* Persistence model
* API response format
* Storage layout

It is a logical model.

---

## 3. Structural Philosophy

### 3.1 Collection-Based Design

All repeating data structures must be represented as collections.

Examples include (conceptually):

* Academic records
* Standardized tests
* Essays
* Activities
* Timeline entries

The system must not:

* Hardcode academic level keys (e.g., class_9, class_10, class_12).
* Hardcode specific test names as top-level keys.
* Encode structural meaning into rigid nested JSON hierarchies.

All domain-specific data must be stored as extensible collections.

---

### 3.2 No Rigid Key Paths

The canonical model must not rely on fixed key paths such as:

* academics.class_12.score
* tests.sat.total_score
* essays.career_statement

The system must instead use:

* Collection entries
* Semantic identifiers
* Extensible attributes

Synthesis logic must reference semantic categories, not rigid paths.

---

### 3.3 Extensibility Requirement

The canonical model must allow:

* New academic systems
* New test formats
* Additional essay types
* New activity categories
* Additional metadata fields

without structural redesign.

No schema assumption may limit future institution variability.

---

### 3.4 Backward Compatibility Rule

The canonical representation must include a:

* canonical_version identifier

Versioning ensures:

* Future structural additions do not break older records
* Migration can be managed without reprocessing raw PDFs

Backward compatibility must be preserved across versions.

---

## 4. Separation of Concerns

The canonical representation must logically separate:

1. Identifiers (PII)
2. Profile metadata
3. Extracted structured data
4. Integrity findings
5. Cross-references
6. Timeline data
7. Extraction confidence summary
8. Synthesis output (stored separately or logically partitioned)

Personally identifiable information must not be merged with extracted academic or narrative content.

Synthesis output must not overwrite extracted content.

---

## 5. Transport-Level vs Storage-Level Distinction

The canonical representation is a transport-level construct.

It must not:

* Be tightly coupled to database tables
* Reflect relational storage structure
* Embed database constraints into logical design

Database schema may evolve.

Canonical philosophy must remain independent of storage mechanism.

---

## 6. Confidence and Severity Integration

The canonical representation must support:

* Confidence scores for extraction agents
* Severity tagging for integrity anomalies

Confidence must not:

* Alter extracted values
* Suppress structured data

Severity must not:

* Imply evaluation of applicant quality

Confidence and severity are structural metadata only.

---

## 7. No Normalization Rule

The canonical representation must preserve:

* Raw marking schemes
* Raw scores
* Raw predicted values
* Original grading formats

The system must not:

* Normalize grades to percentage
* Convert GPA scales
* Compute trends
* Infer improvement or decline

Raw preservation ensures neutrality.

---

## 8. Traceability Requirement

Every data element in canonical representation must:

* Be traceable to deterministic extraction
* Not be LLM-generated
* Not be inferred
* Not be enriched externally

LLM synthesis operates strictly over canonical data.

---

## 9. Multi-Tenant Compatibility

The canonical model must support:

* Institutional variability
* Header variations
* Field name differences
* Additional optional sections

No institution-specific assumptions may be embedded into the canonical philosophy.

---

## 10. Prohibited Design Patterns

The canonical model must not:

* Hardcode academic levels
* Hardcode test names
* Embed evaluation flags
* Encode ranking indicators
* Collapse collections into singular objects
* Use schema inference at runtime
* Depend on dynamic LLM-based schema expansion

---

## 11. Architectural Invariance

The canonical philosophy must remain unchanged across:

* Stage 0 (Local Core Engine)
* Stage 1 (Structured MVP)
* Stage 2 (Async Processing)
* Stage 3 (Storage Hardening)
* Stage 4 (Service Separation)
* Stage 5 (Security Hardening)
* Stage 6 (Cloud-Ready Deployment)

Infrastructure may change.

The canonical philosophy must not.

---

## 12. Compliance Requirement

Any implementation that:

* Hardcodes academic structure
* Introduces normalization
* Embeds evaluation
* Couples schema tightly to storage
* Violates collection-based design

is non-compliant with this specification.

---

End of Document.

---


