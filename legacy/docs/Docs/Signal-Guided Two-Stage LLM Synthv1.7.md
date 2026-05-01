# Signal-Guided Two-Stage LLM Synthesis Architecture

## 1. Purpose of the Architecture

The existing system performs a single LLM synthesis step that converts structured application data directly into interviewer themes and questions.

While functional, this approach compresses **interpretation and communication into a single step**, which can lead to:

* generic interview themes
* shallow reasoning about applicant behavior
* weak traceability between evidence and interview prompts

The updated architecture introduces a **two-stage synthesis model** that separates:

```text
analysis (evidence interpretation)
communication (interview preparation)
```

This change enables the system to produce interview guidance that is **explicitly grounded in identifiable applicant signals** derived from canonical application data.

---

# 2. Design Principles

The architecture follows several core principles.

### Deterministic Extraction Remains Authoritative

All factual application data continues to originate from the deterministic extraction pipeline (Agents 1–11). LLM components **do not modify canonical data**.

---

### Interpretation and Presentation Are Separate Tasks

Reasoning about an applicant’s profile and generating interviewer prompts are treated as **distinct stages**.

```text
Interpretation → Identify signals
Presentation → Generate interview guidance
```

This separation improves reasoning depth and reduces prompt instability.

---

### Signals Must Be Evidence-Grounded

All interpreted signals must reference identifiable canonical entities. This ensures that insights remain traceable to the underlying application.

---

### Canonical Data Is Consumed Through Controlled Projections

The canonical model is optimized for deterministic storage, not LLM reasoning.
Before interacting with LLM components, the system produces **curated projections of the canonical representation** that provide structured reasoning context.

These projections reduce noise and token overhead while preserving entity references.

---

# 3. Updated System Pipeline

The updated pipeline introduces new reasoning stages while preserving the existing deterministic extraction foundation.

```text
PDF Application
↓
Deterministic Extraction (Agents 1–11)
↓
Canonical Representation
↓
Deterministic Signal Detection
↓
Canonical Projection (Reasoning Snapshot)
↓
LLM Call 1 — Signal Interpretation
↓
Signal Validation
↓
Signal-Evidence Bundle Construction
↓
LLM Call 2 — Interview Theme & Question Generation
↓
ROS Report Assembly
```

Each stage has a clearly defined responsibility.

---

# 4. Deterministic Signal Layer

Before invoking LLM reasoning, the system derives **deterministic observational signals** from the canonical data.

These signals represent observable patterns such as:

* activity duration
* academic trends
* leadership participation
* subject performance distribution

Deterministic signals do **not represent interpretations**. They provide structured hints that guide the interpretation stage.

Their purpose is to:

* highlight notable patterns in the canonical dataset
* anchor LLM reasoning in measurable observations
* reduce the likelihood of hallucinated inferences

---

# 5. Canonical Projection Layer

The canonical representation contains comprehensive structured data that is optimized for deterministic processing rather than LLM reasoning.

To improve reasoning efficiency, the system generates **controlled projections of the canonical model** before each LLM stage.

These projections:

* curate the relevant portions of canonical data
* remove structural noise and metadata
* preserve entity identifiers for evidence grounding
* provide a structured reasoning context for the LLM

Importantly, the canonical model itself **remains unchanged**.
Projections are read-only views constructed specifically for reasoning tasks.

Different projections may be used for different synthesis stages.

---

# 6. LLM Call 1 — Signal Interpretation Layer

The first LLM stage functions as the system’s **interpretation engine**.

Its role is to analyze the projected canonical context together with deterministic signals in order to identify **interpreted applicant signals**.

These interpreted signals represent higher-level behavioral patterns, such as:

* evidence of iterative problem solving
* self-directed technical exploration
* sustained commitment to activities
* leadership initiative

The output of this stage is a structured collection of interpreted signals that reference supporting canonical entities.

This stage performs **analysis only**.
It does not generate interviewer questions or narrative summaries.

---

# 7. Signal Validation Layer

Before signals can influence interview preparation, they are subjected to deterministic validation.

The validation layer ensures that:

* signals reference valid canonical entities
* signals follow the defined schema
* signals avoid evaluative language or unsupported claims

This stage prevents ungrounded or overly subjective interpretations from propagating through the pipeline.

---

# 8. Signal–Evidence Bundle

After validation, the system constructs a **signal–evidence bundle**.

Each interpreted signal is paired with supporting evidence extracted from the canonical projection. This bundle becomes the primary reasoning input for the second LLM stage.

The signal–evidence structure allows the system to:

* preserve grounding between signals and applicant data
* provide contextual information for question generation
* maintain traceability within the final report

Importantly, the second LLM stage does **not receive the full canonical dataset**.
It receives only the validated signals and their associated evidence context.

---

# 9. LLM Call 2 — Interview Generation Layer

The second LLM stage functions as the system’s **presentation engine**.

Its responsibility is to transform validated signals into interviewer-facing outputs.

Specifically, this stage generates:

* structured interview themes
* grouped interview questions
* prompts designed to explore the applicant’s experiences and motivations

Because the interpretation stage has already identified relevant signals, the second LLM call focuses solely on **communication and interview guidance**, rather than profile analysis.

---

# 10. Relationship to the Canonical Model

The canonical model remains the **source of truth** for all factual application data.

LLM components:

* do not modify canonical records
* do not introduce new factual entities
* operate exclusively on curated projections and signal interpretations

All outputs ultimately reference canonical entities to ensure traceability.

---

# 11. Impact on Existing System Components

Several system components remain unchanged:

* deterministic extraction agents (Agents 1–11)
* canonical data schema
* ROS report structure
* database storage of canonical records

New reasoning components introduced by this architecture include:

* deterministic signal detection
* canonical projection layer
* signal interpretation stage (LLM Call 1)
* signal validation stage
* interview generation stage (LLM Call 2)

These additions enhance the synthesis process without altering the deterministic data foundation.

---

# 12. Expected Benefits

The two-stage architecture provides several improvements over the single-call synthesis model.

### Deeper Applicant Interpretation

Separating interpretation from presentation allows the system to identify meaningful applicant signals before generating interview prompts.

---

### Improved Question Quality

Interview questions become explicitly grounded in signals derived from application evidence.

---

### Stronger Traceability

Signals provide an intermediate reasoning layer that links canonical evidence to interviewer guidance.

---

### Greater Architectural Stability

By isolating reasoning and presentation tasks, the system becomes easier to extend and debug.

---


