# 📄 `llm_synthesis_contract.md`

**(LLM Behavior & Output Governance Specification)**

---

# Interview Preparation Platform

## LLM Synthesis Contract

---

## 1. Purpose of This Document

This document defines the allowed and prohibited behavior of the LLM synthesis layer.

It governs:

* Input constraints
* Output constraints
* Behavioral restrictions
* Traceability requirements
* Prohibited inference patterns

This contract is binding on any implementation invoking an LLM.

---

## 2. Single Invocation Rule

The system must make exactly one LLM call per processed application.

The LLM:

* Must not be called recursively.
* Must not trigger additional LLM calls.
* Must not perform multi-step reasoning chains.
* Must not perform tool-calling loops.
* Must not invoke external APIs.
* Must not retrieve additional data.

No orchestration frameworks are permitted.

The LLM is a synthesis component only.

---

## 3. Input Boundary

The LLM must receive:

* Canonical representation only.
* Explicit invariant rules.
* Output structure expectations.

The LLM must not receive:

* Raw PDF text.
* Raw extracted blocks.
* Database schema.
* External knowledge.
* Historical applicant data.
* Other applicants’ data.
* Admissions outcomes.

Canonical representation is the sole data source.

---

## 4. Output Scope

The LLM may generate only:

1. Neutral Snapshot
2. Discussion Focus Areas
3. Suggested Interview Questions

No additional sections may be generated.

No scoring fields may be generated.

No ranking fields may be generated.

---

## 5. Non-Evaluative Requirement

The LLM must not:

* Score the applicant.
* Rank the applicant.
* Compare to peers.
* Label strengths or weaknesses.
* Flag concerns.
* Predict admissions likelihood.
* Infer academic quality.
* Infer competitiveness.
* Use evaluative adjectives.
* Use comparative phrasing.
* Use prescriptive admissions advice.

Prohibited examples include but are not limited to:

* “strong academic record”
* “weak extracurricular profile”
* “top-performing student”
* “area of concern”
* “needs improvement”
* “competitive applicant”
* “excellent leadership”
* “outstanding performance”

Neutral structural phrasing only.

---

## 6. No Inference Beyond Explicit Data

The LLM must not:

* Infer personality traits.
* Infer intelligence.
* Infer work ethic.
* Infer impact level.
* Infer academic progression trends.
* Infer causal relationships.
* Infer motivations not explicitly stated.

If information is not explicitly present in canonical representation, it must not be introduced.

---

## 7. Traceability Requirement

Every generated statement must be:

* Directly traceable to canonical data.
* Structurally grounded.
* Derivable from extracted content.

No hallucinated entities.

No fabricated details.

No external enrichment.

---

## 8. Prompt Referencing Rule

The LLM must reference:

* Semantic categories
* Canonical collections

The LLM must not depend on:

* Hardcoded key paths.
* Rigid JSON hierarchies.
* Fixed academic-level assumptions.
* Fixed test-name assumptions.

Prompt design must preserve extensibility.

---

## 9. Neutral Language Constraint

The LLM must use:

* Descriptive phrasing
* Structural language
* Content-based summarization
* Explicitly grounded question framing

The LLM must avoid:

* Normative judgments
* Value-laden adjectives
* Performance labels
* Concern framing
* Prescriptive direction

Language must remain informational and discussion-oriented.

---

## 10. No Data Mutation

The LLM must not:

* Modify canonical values.
* Normalize grades.
* Recalculate scores.
* Merge entries.
* Resolve inconsistencies.
* Override integrity findings.

Canonical data is immutable input.

---

## 11. Output Validation Requirement

All LLM output must be passed through a policy validation layer that:

* Detects evaluative phrasing.
* Detects comparative constructs.
* Detects ranking statements.
* Detects prescriptive language.
* Detects normative performance language.

Invalid output must be:

* Rejected, or
* Sanitized before release.

---

## 12. Stage Invariance

The LLM synthesis contract must remain unchanged across:

* Stage 0 through Stage 6.

Infrastructure changes must not alter LLM behavior rules.

---

## 13. Violation Handling

If LLM output violates any constraint in this document:

* The output must not be delivered to end users.
* The violation must be logged.
* The implementation must be corrected.

Repeated violations indicate prompt misalignment and must be addressed.

---

## 14. Compliance Requirement

Any implementation that:

* Introduces multiple LLM calls
* Introduces evaluation logic
* Introduces inference beyond explicit data
* Introduces ranking language
* Introduces dynamic reasoning orchestration

is non-compliant with this contract.

---

End of Document.

---


