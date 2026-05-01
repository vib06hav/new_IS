# `system_overview_v1.5.md`

**(Stage 1.5 — Structured MVP with ROS v1 Output Layer)**

---

## 1. System Identity

### 1.1 Purpose

The system processes structured application PDFs and produces a deterministic canonical representation of the applicant’s information. This canonical representation is then used to generate a structured interview preparation report.

The system is not an admissions evaluation engine.
It does not rank, score, normalize, compare, or predict outcomes.

The system produces a structured report artifact governed by:

> **Report Output Specification (ROS v1)** 

ROS v1 is the sole presentation-layer output artifact in Stage 1.5.

---

### 1.2 What The System Is

The system is:

* Deterministic-first
* Canonical-driven
* Single-LLM-bound
* Non-evaluative
* Multi-tenant capable (logically, not infra-separated)
* Synchronous in execution
* Single-service in deployment

The system performs:

1. Deterministic extraction of structured data
2. Canonical representation assembly
3. Deterministic report projection (Pages 1–3 of ROS)
4. Single LLM synthesis for thematic structuring (Pages 4–5 of ROS)
5. Policy validation
6. Persistence of canonical + ROS output

---

### 1.3 What The System Is Not

The system is not:

* An admissions scoring engine
* A ranking engine
* A predictive model
* A grading normalization system
* A multi-LLM orchestration system
* An async job-queue architecture (Stage 1)
* A microservice mesh

The system does not:

* Perform recursive reasoning
* Make multiple LLM calls per application
* Rewrite canonical content for presentation convenience
* Store chain-of-thought reasoning
* Store raw LLM intermediate prompts

---

## 2. High-Level Pipeline Flow

### 2.1 Stage 1 Baseline Flow

```
Upload PDF
    ↓
Deterministic Agents (1–11)
    ↓
Canonical Representation
    ↓
Single LLM Synthesis
    ↓
Policy Guard
    ↓
Return Structured Output
```

---

### 2.2 Stage 1.5 Flow (ROS v1 Integrated)

```
Upload PDF
    ↓
Deterministic Agents (1–11)
    ↓
Canonical Representation
    ↓
Deterministic ROS Projection (Pages 1–3)
    ↓
Single LLM Call (Themes + Question Groups)
    ↓
Policy Guard
    ↓
Assemble Full ROS v1
    ↓
Persist + Return ROS v1
```

---

## 3. Canonical Representation

Canonical structure evolved to version 1.1 to formally support structured fields required by ROS v1 while preserving canonical–presentation separation.

This evolution:

- Preserves collection-based discipline
- Introduces structured `family_background`
- Introduces `schooling_history[]`
- Introduces explicit `activity_type`
- Requires no schema migration
- Does not violate deterministic-first principles

Canonical remains presentation-agnostic.

---

## 4. ROS v1 Output Layer

### 4.1 Definition

ROS v1 is a structured, page-grouped JSON artifact composed of:

1. `report_metadata`
2. `page_1_background_profile`
3. `page_2_academic_and_engagement`
4. `page_3_essays`
5. `page_4_focus_themes`
6. `page_5_question_groups`

Full specification defined in:

> ROS v1 

---

### 4.2 Deterministic vs LLM Boundaries

| ROS Section | Source                                          | Determinism                      |
| ----------- | ----------------------------------------------- | -------------------------------- |
| Page 1      | Canonical projection                            | Deterministic                    |
| Page 2      | Canonical projection                            | Deterministic                    |
| Page 3      | Canonical projection + deterministic highlights | Deterministic                    |
| Page 4      | LLM (single call)                               | Non-evaluative structured themes |
| Page 5      | LLM (single call)                               | Structured question groups       |

The LLM generates only thematic structure and question grouping.

It does not:

* Rewrite essays
* Modify academic records
* Introduce new facts
* Create evaluation commentary

---

## 5. Single LLM Boundary

The system makes exactly one LLM call per application.

This call:

* Receives the canonical representation
* Produces:

  * `themes`
  * `question_groups`
* Returns structured JSON
* Is passed through policy guard
* Is never retried
* Is never chained
* Is never recursively invoked

The single-call invariant is absolute.

---

## 6. Persistence Model

The system persists:

* Canonical representation (`canonical_records`)
* Full ROS v1 JSON artifact (`synthesis_records.synthesis_output`)

No additional tables are introduced.

No schema changes are required for Stage 1.5.

Infrastructure remains unchanged from Stage 1.

---

## 7. Stage Discipline

Stage 1.5 introduces:

* Logical projection layer
* Structured ROS output contract
* LLM schema refinement

Stage 1.5 does not introduce:

* Async processing
* Redis
* MinIO
* Service separation
* Additional containers
* Environment variable changes
* Schema migrations

---

## Constraint Check

| Constraint                              | Status |
| --------------------------------------- | ------ |
| Deterministic-first preserved           | ✅      |
| Single LLM call preserved               | ✅      |
| No evaluation logic introduced          | ✅      |
| Canonical remains collection-based      | ✅      |
| No rigid key paths introduced           | ✅      |
| No async introduced                     | ✅      |
| No infrastructure creep                 | ✅      |
| No additional LLM frameworks introduced | ✅      |

---


