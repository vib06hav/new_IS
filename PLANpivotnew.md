# Stage 1.8.1 Implementation Plan: Shift Call 3 From Questions to Interview Openings

## Summary

Rework Call 3 and its downstream consumers so the main interviewer-facing artifact is an `opening card`, not a generated question string.

- Call 1 stays the machine-truth layer.
- Call 2 stays the Page 4 `focus_areas` layer.
- Call 3 changes from `question_groups` to `opening_groups`.
- Page 5, the workspace, overlay, postgame, refinement, and chat all pivot to openings as the canonical editable/tracked unit.
- `sample_question` is required on every opening card, but it is explicitly secondary support rather than the main artifact.
- User-facing labeling switches to **Interview Openings**.
- Internal workspace contracts also rename from `questions` to `openings`; this is not a semantic wrapper.

## Key Changes

### 1. Call 3 contract and validation
- Replace `question_groups[]` with `opening_groups[]`, one per `focus_area_id`.
- Replace `questions: string[]` with `openings[]`, where each opening contains:
  - `opening_id`
  - `hook`
  - `what_happened`
  - `why_it_matters_here`
  - `line_of_inquiry`
  - `sample_question`
  - `source_signal_ids`
- Keep `focus_area_id`, `group_title`, `source_theme_ids`, and group-level `source_signal_ids`.
- Update the Call 3 prompt so it generates prep-friendly opening cards first and only then sample phrasing.
- Update validation to require:
  - exactly one group per `focus_area_id`
  - 2-4 openings per group
  - non-empty `hook`, `what_happened`, `why_it_matters_here`, `line_of_inquiry`, and `sample_question`
  - valid source IDs and focus-area linkage
- Remove question-count and question-form assumptions from the canonical contract; move bad/generic wording checks to `sample_question`.

### 2. Backend report, schema, and orchestration
- Update API/report schemas so Page 5 becomes `page_5_interview_openings` or keeps the page key but stores `opening_groups[]` as the canonical payload.
- Keep Page 4 unchanged structurally as `focus_areas[]`.
- Update orchestration to:
  - build a Call 3 bundle optimized for openings rather than questions
  - validate `opening_groups`
  - assemble final report Page 5 from openings
- Update report assembly, trace runner outputs, and any serialization helpers so all Stage 1.8 artifacts record `opening_groups` instead of `question_groups`.

### 3. Workspace, overlay, postgame, and refinement
- Change workspace content so the tracked generated unit becomes `openings[]`, not `questions[]`.
- Rename workspace models accordingly:
  - `InterviewWorkspaceQuestion` -> opening card model
  - `question_group_title` -> opening group title
  - `questions` -> `openings`
- Statuses, notes, and follow-ups attach to the opening card, not to the sample question.
- Preserve follow-ups as interviewer-authored follow-up prompts attached to each opening.
- Update workspace seed creation so Call 3 openings become editable cards under each focus area.
- Update refinement context generation so note refinement uses opening context:
  - focus area title
  - opening hook
  - what happened
  - line of inquiry
  - sample question
- Update overlay/postgame summaries and totals so they count openings/follow-ups rather than questions/follow-ups while preserving current status taxonomy unless explicitly changed later.

### 4. Frontend and report/chat behavior
- Page 5 report view changes from “Questions” to **Interview Openings**.
- Render each opening card with:
  - hook
  - what happened
  - why it matters here
  - line of inquiry
  - sample question
- Update the pre-interview editor so generated cards are edited as openings, with optional editing of `sample_question`.
- Update overlay so the live runner is centered on the opening card and uses `sample_question` as support text, not the headline.
- Update postgame/final report so outcomes and notes are grouped by focus area and opening card.
- Update report chat context and copy so Page 5 is described and retrieved as interview openings rather than question groups, while keeping Call 1 grounding available for deep drill-down.

## Public Interfaces / Type Changes

- Backend schema:
  - add `OpeningCard`
  - add `OpeningGroup`
  - replace `Page5QuestionGroups` with a Page 5 openings model
- Frontend types:
  - rename question-based Page 5 and workspace types to opening-based equivalents
  - workspace content uses `themes[]` only if needed as the outer compatibility container; nested generated items become `openings[]`
- Refinement API:
  - rename/expand note-target semantics from question/follow-up to opening/follow-up
  - keep `final_summary` mode unchanged

## Test Plan

- Call 3 generation:
  - each focus area yields one valid opening group
  - each group yields 2-4 openings with required fields and required `sample_question`
  - output remains specific without overloading technical detail into `what_happened`
- Assembly and schemas:
  - final report serializes Page 5 as opening groups
  - trace runner captures Call 3 inputs/outputs in the new shape
- Workspace:
  - seed produces editable opening cards with statuses, notes, and follow-ups
  - save/load/draft restore preserve opening IDs and follow-up IDs
- Overlay and postgame:
  - opening cards can be marked satisfactory/mixed/unsatisfactory/unasked
  - custom openings and custom follow-ups still work
  - final report aggregates opening outcomes correctly
- Chat and report UI:
  - Page 5 copy, anchors, and sources point to Interview Openings
  - report chat can answer “what should I ask about” style queries using opening cards
- Regression:
  - Page 4 remains stable
  - Call 1 grounding and annotations stay intact
  - existing PDFs still complete end-to-end after the contract migration

## Assumptions and Defaults

- `sample_question` is required on every opening card.
- User-facing Page 5 label becomes **Interview Openings** immediately.
- Internal workspace contracts rename to openings rather than keeping `questions[]` as a hidden compatibility layer.
- Statuses, notes, and follow-ups attach to openings, not to sample questions.
- Existing status vocabulary (`unasked`, `satisfactory`, `mixed`, `unsatisfactory`) remains unchanged for this migration.
- Follow-ups remain supported as interviewer-authored prompts attached to an opening card.
