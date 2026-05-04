# Stage 1.8 Call Contract Guide

## Purpose

This document defines the intended contract for the three-call interview synthesis system after the next product shift.

The central idea is:

- Call 1 stays the machine-truth layer.
- Call 2 stays the interviewer synthesis layer.
- Call 3 stops being a generator of exact interview questions and becomes a generator of interview openings.

The interviewer should primarily read:

- Page 4 focus areas from Call 2
- Page 5 interview openings from Call 3

The interviewer should not be expected to read raw Call 1 structure.

---

## Core Design Principle

The product should optimize for fast interviewer prep, not for the elegance of a generated question.

A good output should let a busy interviewer quickly understand:

- what this part of the application is really about
- what specific moment or example in the file is worth exploring
- what they are trying to learn if they ask about it

That means the main editable unit should be a prep card or interview opening, not a rigid line of question text.

---

## Call Roles

## Call 1: Grounding Pass

Audience:
- backend infrastructure
- validators
- copilot retrieval
- annotations and highlighting

Role:
- produce the machine-readable substrate
- ground themes and signals in real source references
- preserve traceability and linkage

This call is not interviewer-facing.

It should answer:
- what concrete openings exist in the application?
- what source entities, fragments, and deterministic signals support them?
- how are those openings grouped into machine themes?

## Call 2: Interviewer Synthesis

Audience:
- interviewer
- Page 4 report view
- prep context for Call 3

Role:
- translate Call 1 structure into plain-language focus areas
- define the high-level interview territory
- explain why each area is worth spending time on
- clarify what still needs to be understood from the applicant's perspective

This is the interviewer-facing summary layer.

It should answer:
- what is this area really about?
- why is it worth interview time?
- what are we still trying to understand?

## Call 3: Interview Openings

Audience:
- interviewer
- pre-interview editor
- overlay / live interview runner
- post-interview notes attachment points

Role:
- turn each focus area into a small set of usable interview openings
- surface concrete hooks from the file
- explain what happened in plain language
- show why the opening matters
- suggest a line of inquiry
- optionally provide a natural sample question

This is not primarily a question-writing call.

It should answer:
- what concrete thing in the file gives me a way into this focus area?
- why is this opening useful?
- what am I trying to learn if I ask about it?

---

## Target Output Contracts

## Call 1 Contract

Call 1 should remain machine-oriented.

### Signals

- `signal_id: str`
  - Stable machine identifier.
- `title: str`
  - Short signal label.
- `core_observation: str`
  - One sentence describing what is specifically present or absent in the file.
  - This is not a human-facing interpretation.
- `interview_opening: str`
  - One sentence describing the specific thing that is worth understanding more deeply.
  - This is still grounding language, not interviewer copy.
- `referenced_entity_ids: list[str]`
  - Entity links for highlighting and retrieval.
- `supporting_fragment_ids: list[str]`
  - Essay fragment support where relevant.
- `supporting_det_signal_ids: list[str]`
  - Deterministic signal support where relevant.

### Themes

- `theme_id: str`
  - Stable machine identifier.
- `title: str`
  - Short machine grouping label.
- `supporting_signal_ids: list[str]`
  - Signal membership.

Call 1 should not be required to produce interviewer-readable copy.

## Call 2 Contract

Call 2 produces `focus_areas`.

### Focus Area Object

- `focus_area_id: str`
  - Stable identifier for downstream grouping.
- `title: str`
  - Plain-language title.
  - Should sound like a real phrase, not a rubric category.
- `territory: str`
  - One to two sentences.
  - What this area is actually about for this specific applicant.
- `what_makes_it_worth_time: str`
  - One sentence.
  - What specific thing in the file makes this worth exploring.
- `what_to_find_out: str`
  - One sentence.
  - What the interviewer still needs to understand from the applicant's perspective.
  - This should orient the interviewer, not instruct them.
- `source_theme_ids: list[str]`
  - Traceability back to Call 1 themes.
- `source_signal_ids: list[str]`
  - Traceability back to Call 1 signals.

### Call 2 Rules

- Produce 2 to 3 focus areas.
- Focus areas may merge multiple Call 1 themes when that improves readability.
- Every Call 1 theme must appear in at least one `source_theme_ids` list.
- Focus areas should be scannable in under two minutes.
- Focus areas should not contain framework language.
- Focus areas should not drift into exact question wording.

## Call 3 Contract

Call 3 produces one `opening_group` per `focus_area_id`.

The group remains the main downstream container because it maps cleanly to:

- Page 5 sections
- workspace sections
- overlay sections
- post-interview note groupings

### Opening Group Object

- `focus_area_id: str`
  - Must match a real Call 2 focus area.
- `group_title: str`
  - Short scannable label for the set of openings.
- `openings: list[OpeningCard]`
  - Usually 2 to 4 cards per focus area.
- `source_theme_ids: list[str]`
  - Traceability back to Call 1 themes.
- `source_signal_ids: list[str]`
  - Traceability back to Call 1 signals.

### Opening Card Object

- `opening_id: str`
  - Stable item identifier for editing, overlay, and note attachment.
- `hook: str`
  - Short concrete handle from the file.
  - Example: `Water-tank alarm project`
  - Not a full sentence question.
- `what_happened: str`
  - One or two sentences.
  - Plain-language summary of the concrete moment, example, project, decision, or pivot.
  - Should be understandable even if the interviewer has not just reread the essay.
- `why_it_matters_here: str`
  - One sentence.
  - Why this opening is useful inside this focus area.
- `line_of_inquiry: str`
  - One sentence.
  - What this opening helps the interviewer understand.
  - This should be investigative, not conclusive.
- `sample_question: str`
  - Optional but recommended.
  - One natural way to ask into this opening.
  - This is supporting material, not the main artifact.
- `source_signal_ids: list[str]`
  - Traceability to grounded source material.

### Call 3 Rules

- Produce exactly one group per `focus_area_id`.
- Produce 2 to 4 openings per group.
- Every opening must be concretely anchored in the file.
- The card should be useful even if the interviewer ignores `sample_question`.
- `sample_question` should feel natural and light, not hyper-specific for its own sake.
- The main product value is the opening card, not the exact wording of the sample question.

---

## What Each Field Is For

## Call 2

- `title`
  - Gives the interviewer a memorable name for the territory.
- `territory`
  - Gives the interviewer the big-picture read.
- `what_makes_it_worth_time`
  - Tells the interviewer why this area deserves attention.
- `what_to_find_out`
  - Frames the unresolved understanding goal.

## Call 3

- `hook`
  - Gives the interviewer a quick concrete handle from the file.
- `what_happened`
  - Makes the hook intelligible without needing the interviewer to recall technical details.
- `why_it_matters_here`
  - Connects the concrete moment back to the focus area.
- `line_of_inquiry`
  - Tells the interviewer what this opening could reveal.
- `sample_question`
  - Helps if the interviewer wants help phrasing it, but should not be the main thing they rely on.

---

## Good and Bad Shapes

## Bad Call 3 Shape

- Over-optimized exact question
- Assumes the interviewer remembers small file details
- Pushes immediately into the model's deepest interpretation

Example:

`In your water tank alarm project, you moved from a metal-strip circuit to a buoyancy-based displacement switch; what triggered that specific shift when the first prototype proved unreliable?`

Why it fails:

- Too much precision for quick prep.
- Assumes the interviewer remembers circuit details.
- Makes the question itself carry too much load.
- Gives the interviewer a line to decode rather than a conversation opening to use.

## Better Call 3 Shape

### Hook
- `Water-tank alarm project`

### What happened
- `The applicant built an alarm, ran into reliability problems in the first version, and changed the mechanism rather than keep patching the original setup.`

### Why it matters here
- `This gives a concrete way to understand how the applicant responds when a technical idea stops working.`

### Line of inquiry
- `Whether the applicant mainly solves problems by tinkering until something works, or whether they can also explain why the change made sense.`

### Sample question
- `When that first version stopped feeling reliable, how did you decide the next step needed a real design change instead of another small fix?`

Why it works:

- The interviewer can understand the opening quickly.
- The important part is clear even without rereading the file.
- The line of inquiry is preserved.
- The optional question still exists, but it is no longer the whole product.

---

## Writing Rules

## Call 1 Writing Rules

- Be precise.
- Be grounded.
- Do not write for a human prep reader.
- Do not overinterpret.
- Surface openings, not conclusions.

## Call 2 Writing Rules

- Sound like a thoughtful colleague briefing another interviewer.
- Stay high-level and orienting.
- Be specific to the applicant.
- Avoid framework and committee language.
- Do not turn focus areas into disguised questions.
- Do not write `what_to_find_out` as interviewer instructions.

## Call 3 Writing Rules

- Make the opening card understandable on its own.
- Prefer plain-language summaries over fine-grained technical restatements.
- Preserve the useful insight, but do not overload the interviewer with detail.
- Make `line_of_inquiry` hypothesis-driven, not conclusion-driven.
- Treat `sample_question` as optional support, not the main artifact.
- Avoid exactness that depends on the interviewer remembering the essay line by line.

---

## Downstream Product Usage

## Page 4

Page 4 should render Call 2 `focus_areas`.

Primary user value:

- understand the main interview territories
- know why they matter
- know what is still unresolved

## Page 5

Page 5 should render Call 3 `opening_groups`.

Primary user value:

- see concrete ways into each focus area
- quickly understand what happened in the file
- choose which openings feel most useful

## Pre-Interview Editor

The editor should move from editing `questions` to editing `opening cards`.

The main editable unit becomes:

- keep/remove opening
- rewrite hook
- rewrite `what_happened`
- rewrite `line_of_inquiry`
- optionally rewrite `sample_question`

## Overlay / Live Interview Runner

The overlay should surface:

- focus area title
- opening hook
- what happened
- line of inquiry
- optional sample question

This gives the interviewer both structure and flexibility.

## Post-Interview Notes

Notes should attach to:

- `opening_id`

This is better than attaching only to a brittle question string, because the note is really about a conversation opening or territory, not about exact wording.

## Report Chat / Copilot

Chat should continue to use:

- Call 2 focus areas for human-readable synthesis
- Call 3 openings for conversational entry points
- Call 1 signal data for deep grounding, linking, and traceability

---

## Recommended Canonical Contract

### Page 4

Use:

- `focus_areas[]`

### Page 5

Use:

- `opening_groups[]`

Where each `opening_group` contains:

- `focus_area_id`
- `group_title`
- `openings[]`
- `source_theme_ids`
- `source_signal_ids`

Where each `opening` contains:

- `opening_id`
- `hook`
- `what_happened`
- `why_it_matters_here`
- `line_of_inquiry`
- `sample_question`
- `source_signal_ids`

---

## Why This Contract Is The Best Tradeoff

It is a real product pivot because:

- Call 3 is no longer pretending to hand the interviewer final lines to recite.
- The main artifact becomes a prep card, not a brittle question string.

It is still operationally practical because:

- grouping by `focus_area_id` stays intact
- the editor can still work on grouped items
- the overlay can still step through grouped items
- notes can still attach to stable item IDs
- chat and annotations still retain grounding through Call 1 and source IDs

This is the cleanest way to improve interviewer usability without rewriting the whole app around a new workflow model.

---

## Open Implementation Decisions

- Whether `sample_question` should be required or optional.
- Whether Page 5 should still use the label `Questions` during migration or switch immediately to `Interview Openings`.
- Whether the workspace should preserve legacy `questions[]` naming internally for compatibility or move directly to `openings[]`.
- Whether some opening cards should support interviewer-authored follow-up prompts as a first-class field.
