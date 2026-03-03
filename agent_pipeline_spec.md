# 📄 `agent_pipeline_spec.md`

**(Logical Agent Architecture Specification)**

---

# Interview Preparation Platform

## Agent Pipeline Specification (Logical Architecture)

---

## 1. Purpose of This Document

This document defines the logical agent architecture of the system.

It specifies:

* Agent roles
* Responsibilities
* Input and output expectations (conceptual)
* Strict prohibitions
* Non-evaluative constraints
* Canonical representation assembly rules

This document governs logical behavior only.

It does not define:

* Database schema
* Deployment topology
* Microservice boundaries
* Infrastructure components

Any implementation must conform to this specification.

---

## 2. Global Agent Constraints

All agents must comply with the following rules:

1. Deterministic extraction before LLM synthesis.
2. No evaluative inference in any extraction stage.
3. No grade normalization or performance interpretation.
4. No hardcoded academic-level keys.
5. All structured outputs must be collection-based.
6. Every extraction agent must emit a confidence score.
7. Every anomaly must include severity classification.
8. No agent may introduce new facts.
9. Logical agents are not equivalent to microservices.
10. The pipeline execution order must remain fixed.

---

## 3. Logical Pipeline Overview

The agent pipeline consists of 14 logical agents executed in fixed order:

0. Pipeline Orchestrator
1. Layout Block Extractor
2. Section Boundary Detector
3. Personal Information Extractor
4. Academic Records Extractor
5. Standardized Test Extractor
6. Essay Extractor
7. Activity Extractor
8. Cross-Section Entity Detector
9. Timeline Builder
10. Completeness & Integrity Analyzer
11. Canonical Structure Assembler
12. Interview Preparation Generator (LLM)
13. Output Validation Filter

This execution order must not be altered.

---

# LAYER 0 — ORCHESTRATION

---

## AGENT 0 — Pipeline Orchestrator

### Role

Central execution controller.

### Responsibilities

* Accept application input.
* Generate unique job identifier.
* Execute agents in fixed order.
* Handle recoverable errors.
* Abort on critical failures.
* Aggregate agent confidence.
* Ensure canonical_version assignment.
* Produce structured pipeline status.

### Prohibitions

* Must not perform extraction logic.
* Must not modify extracted content.
* Must not introduce inference.

---

# LAYER 1 — STRUCTURAL EXTRACTION (Deterministic Only)

---

## AGENT 1 — Layout Block Extractor

### Input

Raw PDF.

### Responsibilities

* Extract ordered text blocks.
* Preserve page boundaries.
* Preserve layout metadata.
* Preserve structural alignment where possible.
* Detect potential OCR anomalies.

### Prohibitions

* No semantic interpretation.
* No inference of section meaning.

---

## AGENT 2 — Section Boundary Detector

### Input

Ordered block stream.

### Responsibilities

* Identify structural section boundaries.
* Support fuzzy header detection.
* Support formatting-based heuristics.
* Allow unknown sections.
* Assign detection confidence.

### Prohibitions

* No semantic evaluation.
* No assumption of fixed academic level names.
* No hardcoded section rigidity.

---

# LAYER 2 — DOMAIN EXTRACTION (Deterministic Only)

All domain agents operate on section-scoped content.

All must emit:

* structured_data (collection-based)
* confidence_score

No agent may assume rigid schema structure.

---

## AGENT 3 — Personal Information Extractor

### Responsibilities

Extract labeled personal fields:

* Identity fields
* Demographic flags
* Declared preferences

### Rules

* Strict label-based extraction.
* Preserve raw values.
* Normalize yes/no fields only.
* Separate identifiers from profile metadata.

### Prohibitions

* No inference.
* No enrichment.
* No external data lookup.

---

## AGENT 4 — Academic Records Extractor

### Responsibilities

Extract academic entries as a collection.

Each entry must include:

* academic_level (string, not fixed enum)
* board_name
* academic_year
* marking_scheme_raw
* grading_mode (extensible classification)
* score_raw
* predicted_score_raw (if present)
* subject_entries (collection)
* component_tags (if applicable)

### Critical Constraint

Academic records must be stored as collection-based entries.

No fixed keys such as:

* class_9
* class_10
* class_12

### Strict Prohibitions

* No normalization.
* No averaging.
* No trend detection.
* No performance inference.

---

## AGENT 5 — Standardized Test Extractor

### Responsibilities

Extract test entries as collection-based records.

Each entry may include:

* test_name
* total_score
* sectional_scores
* percentiles
* rank
* test_date

Must handle:

* Not attempted
* Awaited results
* Missing subfields

### Prohibitions

* No score comparison.
* No normalization.
* No evaluation.

---

## AGENT 6 — Essay Extractor

### Responsibilities

Extract essays as collection-based entries.

Each entry must include:

* essay_identifier
* raw_text
* word_count
* character_count
* placeholder_flag
* duplication_ratio
* short_response_flag

### Prohibitions

* No quality assessment.
* No sentiment scoring.
* No thematic interpretation.

---

## AGENT 7 — Activity Extractor

### Responsibilities

Extract activities as collection-based entries.

Each entry may include:

* category
* activity_name
* level
* duration
* description_raw
* upload_flag

### Prohibitions

* No importance ranking.
* No impact inference.
* No comparative ordering.

---

## AGENT 8 — Cross-Section Entity Detector

### Responsibilities

Detect repeated entities across:

* Essays
* Activities
* Academic subjects
* Tests

Must:

* Use token filtering
* Avoid stopwords
* Map entity references

### Prohibitions

* No semantic weighting.
* No importance scoring.

---

# LAYER 3 — STRUCTURAL ANALYSIS (Non-Evaluative)

---

## AGENT 9 — Timeline Builder

### Responsibilities

Construct event-based timeline entries.

Each entry must include:

* year
* source_reference
* source_type

Timeline must be event-based, not academic-level-based.

### Prohibitions

* No trend detection.
* No improvement/decline inference.

---

## AGENT 10 — Completeness & Integrity Analyzer

### Responsibilities

Detect structural anomalies:

* Missing sections
* Duplicate essays
* Placeholder responses
* Missing required fields
* Ambiguous grading format

Each anomaly must include:

* anomaly_type
* severity_level
* source_reference

### Prohibitions

* No interpretation beyond structural consistency.
* No evaluation of applicant quality.

---

# LAYER 4 — CANONICAL REPRESENTATION

---

## AGENT 11 — Canonical Structure Assembler

### Responsibilities

Merge extracted collections into a versioned canonical representation.

Must include:

* identifiers (PII separated)
* profile_meta
* academic_entries (collection)
* test_entries (collection)
* essay_entries (collection)
* activity_entries (collection)
* timeline_entries (collection)
* cross_references
* integrity_report
* extraction_confidence_summary
* canonical_version

### Critical Design Constraint

Canonical representation must:

* Be versioned.
* Be extensible.
* Be collection-based.
* Avoid rigid JSON hierarchy.
* Remain transport-level (not storage-bound).

---

# LAYER 5 — SYNTHESIS (Single LLM Boundary)

---

## AGENT 12 — Interview Preparation Generator

### Input

Canonical representation only.

### Responsibilities

Generate:

* Snapshot
* Discussion focus areas
* Suggested questions

### Strict Constraints

* No ranking language.
* No comparative framing.
* No evaluative adjectives.
* No strength/weakness framing.
* No new facts.
* No inference beyond explicit content.
* All statements must be traceable.

Prompt must reference semantic categories, not key paths.

---

# LAYER 6 — POLICY & SAFETY

---

## AGENT 13 — Output Validation Filter

### Responsibilities

Validate LLM output using:

* Pattern-based detection
* Logic-based scanning

Must block or sanitize:

* Evaluative phrasing
* Comparative constructs
* Ranking statements
* Prescriptive advice
* Normative performance language

Rules must be configurable and versioned.

Hardcoded word lists are prohibited.

---

# 4. Architectural Characteristics

The agent pipeline is:

* Deterministic-first
* Collection-based internally
* Non-evaluative
* Confidence-aware
* Severity-aware
* Versioned
* Single-LLM-boundary
* Policy-guarded
* Stage-invariant

---

End of Document.

---


