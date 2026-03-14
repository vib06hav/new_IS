# `system_overview_v1.7.md`

**(Stage 1.7 — Two-Stage Signal-Guided LLM Synthesis)**

---

## 1. System Identity

### 1.1 What the System Is

The AG_InterviewStandardiser processes structured application PDFs submitted by applicants and produces a structured interview preparation report for use by human interviewers.

The system is:

- **Deterministic-first** — all factual data extraction is performed without LLM involvement
- **Signal-guided** — LLM reasoning is anchored in deterministic observations derived from extracted data
- **Two-call-bounded** — exactly two LLM calls are permitted per application
- **Non-evaluative** — the system standardizes data for interviewers; it does not assess applicants
- **Synchronous** — the entire pipeline executes within a single request lifecycle
- **Single-service** — deployed as a single container without service separation
- **Multi-tenant capable** — logically supports multiple users; not infrastructure-separated

The system produces a **Report Output Specification (ROS v1)** artifact as its sole output. This is a structured five-page JSON document designed for interview preparation.

---

### 1.2 What the System Is Not

The system is not:

- An admissions scoring engine
- A ranking engine
- A predictive model for admissions outcomes
- A grade normalization system
- A multi-LLM orchestration framework
- An async job-queue architecture
- A microservice mesh
- A document search or retrieval system
- A chatbot or interactive reasoning system

The system does not:

- Score, rank, or compare applicants against one another or against any benchmark
- Predict the likelihood of any admissions outcome
- Rewrite or paraphrase canonical applicant content for presentation convenience
- Perform recursive or iterative LLM reasoning
- Store intermediate LLM reasoning or chain-of-thought artifacts
- Retry failed LLM calls or fall back to alternative synthesis paths
- Make more than two LLM calls per application under any circumstances

---

## 2. Key Definitions

The following terms are used throughout this document.

**Canonical Representation** — The authoritative, structured, versioned (v1.1) output of the deterministic extraction pipeline. Contains all extracted applicant data in collection-based form. Stored as JSONB in `canonical_records`. Never modified by any downstream component.

**ROS v1** — Report Output Specification version 1. The five-page structured JSON artifact produced by the pipeline for each application. The sole output artifact of the system.

**Deterministic Component** — Any pipeline stage that produces the same output for the same input without LLM involvement. Every stage except LLM Call 1 and LLM Call 2 is deterministic.

**LLM Call** — A single invocation of the language model API. Exactly two are permitted per application.

**Deterministic Signal** — An observable, rule-derived pattern identified from canonical data without LLM involvement. Examples: a subject appearing as top-scoring across multiple academic levels, a leadership role entry being present, an activity spanning more than three years.

**Interpreted Signal** — A higher-level behavioral inference produced by LLM Call 1. Grounded in deterministic signals and canonical data. Must reference valid canonical entity IDs. Must not contain evaluative language.

**Signal–Evidence Bundle** — A structured artifact pairing each validated interpreted signal with its supporting canonical evidence. The sole input to LLM Call 2.

**Entity ID** — A stable formatted identifier assigned to each canonical entry by the ROS projector. Format: `PREFIX-###` (e.g. `ACA-001`, `ACT-003`, `ESS-002`). The mechanism by which LLM components reference canonical entries.

**Policy Guard** — The deterministic validation module that enforces prohibited language rules and entity ID reference validity. Invoked after both LLM calls.

---

## 3. Full Pipeline Flow

The pipeline executes as a single synchronous pass from PDF upload to ROS v1 persistence. Every stage completes before the next begins.

```
PDF Upload
    ↓
Agent 0 — Orchestrator
    ↓
Agent 1  — Layout Block Extractor
Agent 2  — Section Boundary Detector
Agent 3  — Personal Information Extractor
Agent 4  — Academic Records Extractor
Agent 5  — Standardized Test Extractor
Agent 6  — Essay Extractor
Agent 7  — Activity Extractor
Agent 8  — Cross-Section Entity Detector
Agent 9  — Timeline Builder
Agent 10 — Completeness and Integrity Analyzer
Agent 11 — Canonical Assembler
    ↓
Canonical Representation v1.1
    ↓
ROS Projector — Deterministic Projection (Pages 1–3) + Entity ID Assignment
    ↓
Agent 12 — Deterministic Signal Detection
    ↓
Agent 13 — Canonical Projection Construction
    ↓
Agent 14 — LLM Call 1 (Signal Interpretation)
    ↓
Policy Guard — Signal Validation (Call 1 invocation)
    ↓
Agent 15 — Signal–Evidence Bundle Construction
    ↓
Agent 16 — LLM Call 2 (Interview Generation)
    ↓
Policy Guard — Output Validation (Call 2 invocation)
    ↓
ROS Assembler — Merge Pages 1–3 + Pages 4–5
    ↓
Persist Canonical Record + ROS v1 Artifact
    ↓
Return ROS v1
```

---

## 4. Stage Responsibilities

| Stage | Agent | Type | Responsibility |
|---|---|---|---|
| Orchestrator | Agent 0 | Deterministic | Controls pipeline flow; manages data handoff between all stages |
| Layout Extraction | Agent 1 | Deterministic | Extracts raw text blocks and page metadata from PDF |
| Section Detection | Agent 2 | Deterministic | Identifies logical section boundaries (Academics, Essays, Activities, etc.) |
| Personal Extraction | Agent 3 | Deterministic | Extracts personal identifiers and family background |
| Academic Extraction | Agent 4 | Deterministic | Extracts academic records, grades, and subject-level performance |
| Test Extraction | Agent 5 | Deterministic | Extracts standardized test scores and sectional breakdowns |
| Essay Extraction | Agent 6 | Deterministic | Extracts essay text and response metadata |
| Activity Extraction | Agent 7 | Deterministic | Extracts and categorizes activity entries by type |
| Cross-Section Detection | Agent 8 | Deterministic | Identifies entities appearing across multiple sections |
| Timeline Building | Agent 9 | Deterministic | Normalizes dates and constructs chronological event sequence |
| Integrity Analysis | Agent 10 | Deterministic | Detects structural anomalies and data inconsistencies |
| Canonical Assembly | Agent 11 | Deterministic | Consolidates all agent outputs into the final Canonical Representation v1.1 |
| ROS Projection | ROS Projector | Deterministic | Maps canonical data to ROS Pages 1–3; assigns all entity IDs |
| Signal Detection | Agent 12 | Deterministic | Derives observable deterministic signals from canonical data |
| Projection Construction | Agent 13 | Deterministic | Constructs the cleaned canonical projection for LLM Call 1 |
| Signal Interpretation | Agent 14 | LLM — Call 1 | Analyzes projection and signals; produces interpreted signal collection |
| Signal Validation | Policy Guard | Deterministic | Validates Call 1 output — schema, entity IDs, language |
| Bundle Construction | Agent 15 | Deterministic | Pairs validated signals with canonical evidence; produces signal–evidence bundle |
| Interview Generation | Agent 16 | LLM — Call 2 | Transforms signal–evidence bundle into themes and question groups |
| Output Validation | Policy Guard | Deterministic | Validates Call 2 output — schema, entity IDs, language |
| ROS Assembly | ROS Assembler | Deterministic | Merges deterministic Pages 1–3 with LLM-generated Pages 4–5 |

The LLM boundary is exactly two stages: Agent 14 and Agent 16. Every other stage is deterministic. The Policy Guard is a validation module invoked by the orchestrator at two pipeline points — after Agent 14 and after Agent 16 — and lives in `app/policy/guard.py` rather than `app/agents/`.

---

## 5. Canonical Representation

### 5.1 What It Is

The canonical representation is the internal source of truth for all applicant data. It is produced by Agent 11 as the consolidated output of the entire deterministic extraction pipeline and stored in the `canonical_records` table as a JSONB document.

The canonical representation is:

- **Collection-based** — all data stored as arrays of entries, not as fixed key paths
- **Presentation-agnostic** — structured for storage and deterministic processing, not for any output format
- **Versioned** — currently at v1.1
- **Non-evaluative** — contains extracted facts only, no assessments or inferences
- **Immutable downstream** — no component after Agent 11 modifies it

### 5.2 What It Contains

The canonical representation contains the following collections:

- `identifiers` — applicant name, date of birth, preferred major, family background
- `academic_entries[]` — academic records per grade level with subject-level scores
- `schooling_history[]` — school and board per level
- `test_entries[]` — standardized test results with sectional breakdowns
- `essay_entries[]` — essay prompts and full response text
- `activity_entries[]` — extracurricular, co-curricular, and leadership activities
- `timeline_entries[]` — chronological event sequence derived from other collections
- `cross_references` — entity tokens appearing across multiple sections
- `integrity_report` — structural anomaly flags from Agent 10
- `extraction_confidence` — per-agent confidence scores

### 5.3 What Does Not Happen to It

No downstream stage modifies the canonical representation. The ROS projector reads it. The signal detection layer reads it. The projection construction layer reads it. The bundle construction layer reads it. None of these stages write to it. The canonical record stored after Agent 11 completes is identical to the canonical record present when the pipeline finishes.

---

## 6. Signal Architecture

### 6.1 Why Signals Exist

The pipeline separates LLM reasoning into two bounded stages — interpretation and generation — rather than compressing both into a single call.

The motivation is structural. A single LLM call asked to simultaneously analyze an applicant's profile and produce interview questions tends to produce shallow, generic output. Interpretation and communication are distinct cognitive tasks. Separating them produces interview guidance that is explicitly grounded in identifiable applicant patterns rather than in surface-level summarization of the canonical data.

### 6.2 Deterministic Signals

Before any LLM involvement, Agent 12 analyzes the canonical representation and derives deterministic signals — structured observations about measurable patterns in the data.

Examples:
- An activity entry with a duration value spanning more than three years
- A subject appearing as the highest-scoring entry across multiple academic levels
- A leadership role entry being present in the activity collection
- Multiple activity entries sharing a domain keyword

Deterministic signals are not interpretations. They are structured factual observations. They exist to anchor LLM Call 1 in measurable canonical data rather than leaving it to reason from the full document without guidance.

### 6.3 Interpreted Signals

LLM Call 1 receives the canonical projection and the deterministic signal collection. It produces a structured collection of interpreted signals — higher-level behavioral inferences such as:

- Sustained commitment to a technical domain across multiple activity types
- Evidence of iterative community engagement with progressively larger scope
- Self-directed exploration beyond formal curriculum

Each interpreted signal must reference the canonical entity IDs that support it. No interpreted signal may introduce facts not present in the canonical data. No interpreted signal may contain evaluative language.

### 6.4 Signal–Evidence Bundle

After signal validation, Agent 15 constructs the signal–evidence bundle: each validated interpreted signal paired with the canonical evidence entries it references. This bundle is the sole input to LLM Call 2.

LLM Call 2 never sees the full canonical representation. It sees only what the validated signals identify as relevant, paired with the supporting evidence. This constraint ensures that interview generation is grounded in the interpretation layer's reasoning, not in unguided access to the full applicant record.

---

## 7. ROS v1 Output Layer

### 7.1 Structure

ROS v1 is a five-page structured JSON artifact. Each page has a defined schema and a defined source.

| Page | Title | Source | Type |
|---|---|---|---|
| Page 1 | Background Profile | Canonical projection via ROS Projector | Deterministic |
| Page 2 | Academic and Engagement Profile | Canonical projection via ROS Projector | Deterministic |
| Page 3 | Essays | Canonical projection via ROS Projector | Deterministic |
| Page 4 | Focus Themes | LLM Call 2 output (validated) | Signal-guided synthesis |
| Page 5 | Question Groups | LLM Call 2 output (validated) | Signal-guided synthesis |

Pages 1–3 are produced entirely without LLM involvement. They are deterministic projections of canonical data assigned stable entity IDs by the ROS projector.

Pages 4–5 are produced by LLM Call 2 and reflect interview themes and question groups derived from the validated signal–evidence bundle. They carry entity ID references back to the canonical entries that support each theme, providing a traceable link from interview guidance to source applicant data.

### 7.2 What LLM Synthesis Does Not Do

LLM synthesis — at either call — does not:

- Rewrite, paraphrase, or summarize essay content
- Modify academic records or test scores
- Introduce facts not present in the canonical representation
- Assign scores, rankings, or comparative assessments
- Produce admissions commentary of any kind
- Reference entity IDs not explicitly provided to it

### 7.3 Assembly

ROS Pages 1–3 and Pages 4–5 are produced through entirely separate paths. Pages 1–3 are ready before the signal pipeline begins. Pages 4–5 are produced at the end of the signal pipeline after two validation stages. The ROS Assembler merges them into the final five-page artifact only after both paths complete successfully.

If either LLM call fails validation, Pages 4–5 are not produced and no ROS artifact is assembled. The pipeline fails and is logged.

---

## 8. LLM Contact Surface

The system makes exactly two LLM calls per application. This boundary is absolute.

### 8.1 LLM Call 1 — Signal Interpretation

- **Input:** Canonical projection + deterministic signal collection + entity ID map
- **Output:** Structured collection of interpreted signals
- **Permitted:** Behavioral inference grounded in canonical evidence
- **Prohibited:** Interview questions, thematic groupings, evaluative language, new facts, invented entity IDs

### 8.2 LLM Call 2 — Interview Generation

- **Input:** Validated signal–evidence bundle + entity ID map
- **Output:** Themes (`page_4_focus_themes`) and question groups (`page_5_question_groups`)
- **Permitted:** Structured interview themes and exploratory questions grounded in signals
- **Prohibited:** Evaluative language, new facts, invented entity IDs, rewritten essay content, admissions commentary

### 8.3 What Neither Call May Do

- Retry on failure
- Trigger an additional LLM call
- Feed output back into itself
- Receive content that has not passed through a validation stage
- Access content from prior applications

The following terms must not appear in any LLM-generated content at either call. The Policy Guard enforces this list at both validation points:
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

The complete call contracts including full enforcement rules are defined in `llm_synthesis_contract_v1.7.md`.

---

## 9. Persistence Model

The system persists two artifacts per application run:

| Table | Content | Format |
|---|---|---|
| `canonical_records` | The complete Canonical Representation v1.1 produced by Agent 11 | JSONB |
| `synthesis_records` | The complete ROS v1 artifact produced by the ROS Assembler | JSONB (`synthesis_output` column) |

Interpreted signals are pipeline-ephemeral by default. They are not stored in a dedicated column or table. If signal data is required for auditability, it may be embedded as a structured key within `synthesis_records.synthesis_output` alongside the ROS artifact. This requires no schema change. This decision must be made explicitly before Stage 1.7 goes to production.

The remaining two tables — `users` and `applications` — handle user identity and application tracking respectively. Their structure is unchanged in Stage 1.7.

No new tables, columns, or schema migrations are introduced in Stage 1.7.

---

## 10. Infrastructure

The system is deployed as a single Docker container. The infrastructure topology is unchanged from prior stages.

- Single service, single container
- No Redis, no Celery, no job queues
- No additional containers or services
- No microservice decomposition
- No event-driven architecture
- FastAPI application layer with PostgreSQL backend

All Stage 1.7 additions are implemented within the existing application layer. No new environment variables are required.

---

## 11. What Stage 1.7 Introduces

Stage 1.7 introduces the two-stage signal-guided synthesis architecture. All additions are logical-layer only.

**New pipeline stages:**
- Deterministic signal detection (Agent 12)
- Canonical projection construction (Agent 13)
- LLM Call 1 — Signal interpretation (Agent 14)
- Signal validation — Call 1 invocation of Policy Guard
- Signal–evidence bundle construction (Agent 15)
- LLM Call 2 — Interview generation (Agent 16)
- Output validation — Call 2 invocation of Policy Guard

**New pipeline artifacts (all ephemeral):**
- Deterministic signal collection
- Canonical projection
- Interpreted signal collection
- Signal–evidence bundle

**Unchanged:**
- Agents 1–11 and their behavior
- Canonical representation schema (v1.1)
- ROS v1 output schema (all five pages)
- Database tables and schema
- Infrastructure and Docker topology
- API routes and response contracts

---

## 12. Constraint Check

| Constraint | Status |
|---|---|
| Deterministic-first preserved — Agents 1–11 use no LLM | ✅ |
| Exactly two bounded LLM calls per application | ✅ |
| Call 2 receives only validated signal–evidence bundle | ✅ |
| Sequential execution — Call 1 validated before Call 2 invoked | ✅ |
| No fallback, no retry on LLM failure | ✅ |
| Signal validation mandatory and non-bypassable | ✅ |
| Canonical–presentation separation enforced | ✅ |
| Canonical representation immutable downstream | ✅ |
| Canonical projections are read-only and pipeline-ephemeral | ✅ |
| Synchronous execution — no async or deferred stages | ✅ |
| Infrastructure freeze — no topology changes | ✅ |
| Database stability — no schema migrations, no new tables | ✅ |
| No evaluation logic in any pipeline component | ✅ |
| No recursive reasoning — no LLM output fed back into LLM | ✅ |
| ROS v1 output schema unchanged | ✅ |

---

*System Overview Version: 1.7 | Stage: 1.7 — Two-Stage Signal-Guided LLM Synthesis | Governing Document: `architecture_lock_v1.7.md`*