# Question Regeneration, Ratings, and Vector Corpus Design

## Purpose

Add a lightweight pre-build generation workflow that lets:

- admins rate themes and questions before assignment
- interviewers rate themes and questions after assignment but before `Build Interview Plan`
- both roles regenerate generated questions only
- both roles cycle through recent generated question versions inline in the page view

This feature also creates a long-lived corpus of generated themes/questions and feedback that can be indexed in a vector database for future retrieval-assisted regeneration.

## Scope Lock

### In Scope

- theme rating only
- question rating only for generated question versions
- question regeneration only for generated questions
- question version history with inline previous/next controls
- pre-build lock boundary
- vector indexing of generated artifacts and feedback metadata
- applicant-grounded plus corpus-assisted question regeneration

### Out of Scope

- theme regeneration
- regeneration after `Build Interview Plan`
- regeneration in live interview
- regeneration in postgame
- using vector search over raw applicant PDFs as the primary retrieval corpus
- complex cross-theme or cross-question-set version branching

## Product Rules

### Ownership

- Before assignment:
  - admin can rate themes
  - admin can rate generated questions
  - admin can regenerate generated questions
- After assignment and before build:
  - admin is read-only for this feature
  - assigned interviewer can rate themes
  - assigned interviewer can rate generated questions
  - assigned interviewer can regenerate generated questions
- After `Build Interview Plan`:
  - rating and regeneration are locked
  - only existing edit/polish flows remain

### Lock Boundary

`Build Interview Plan` is the hard transition point.

Before this action:
- page-view cards expose rating/regeneration controls

After this action:
- no further regeneration
- no further theme/question rating for this feature
- interviewer moves into workspace editing only

### Generation Rules

- Only generated questions may be regenerated.
- Regeneration creates a new generated version.
- Existing versions are preserved.
- One question has one active generated version at a time.
- The UI shows the latest 5 generated versions for cycling.
- Themes remain structurally stable and do not version-regenerate.

### Rating Rules

- Themes may receive a 1 to 5 star rating.
- Generated question versions may receive a 1 to 5 star rating.
- Manual edits are not rateable by this feature.
- Ratings are feedback on generated quality, not on later human polishing.

## UX Design

## Surfaces

### Admin

Directly on Page 4 and Page 5 cards in the application page view:

- Page 4 theme cards:
  - star rating control
- Page 5 question cards:
  - star rating control
  - regenerate button
  - previous/next version arrows
  - version indicator such as `2 / 5`

Visibility:
- shown only while the application is unassigned
- hidden or disabled once assigned

### Interviewer

Directly on the pre-build page-view cards before workspace creation:

- theme cards:
  - star rating control
- question cards:
  - star rating control
  - regenerate button
  - previous/next version arrows
  - version indicator

Visibility:
- shown only after assignment
- shown only before `Build Interview Plan`

### Build Confirmation Modal

When interviewer clicks `Build Interview Plan`, show a blocking confirmation:

- this action locks question regeneration
- from this point onward, only editing and polishing will be available
- generated question history remains visible only as part of the chosen pre-build state

Recommended actions:
- `Cancel`
- `Build And Lock Regeneration`

## Interaction Model

### Theme Card

- stable theme text
- 1 to 5 stars
- optional tooltip: `Rate how useful this focus area is`

### Question Card

- current active generated question text
- 1 to 5 stars for the active generated version
- `Regenerate`
- `Previous` and `Next` arrows
- small metadata row:
  - `Generated`
  - `Version 3 of 5`
  - optional role badge like `Admin-generated` or `Interviewer-generated`

### Regenerate Behavior

On click:
- create a new version based on current application context
- retrieve similar historical generated/rated examples from vector corpus
- set the new version active
- append it to the question version chain
- if more than 5 visible versions exist, UI still only cycles the most recent 5

## Technical Model

## Source Of Truth

Recommended architecture:

- Postgres is the source of truth
- vector database is a retrieval index and corpus mirror

Reason:
- easier permission enforcement
- easier transactional consistency
- easier version history and lock-state management
- vector DB can be rebuilt if needed

## Existing Model Touchpoints

Current repo seams already relevant:

- `app/models/final_report.py`
- `app/models/interview_workspace.py`
- `app/api/applications.py`
- `app/api/interviewer.py`
- `app/interview_workspace.py`
- `frontend/app/admin/applications/[id]/page.tsx`
- interviewer pre-build review surface before workspace creation
- `frontend/components/ReviewPackageSection.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/types.ts`

The new feature should attach to report-derived Page 4/Page 5 entities before workspace creation, not to post-build workspace notes.

## Proposed Database Entities

### 1. `theme_feedback`

Purpose:
- store rating feedback for a generated theme card

Suggested fields:

- `id`
- `application_id`
- `focus_area_id`
- `surface_role` (`admin`, `interviewer`)
- `surface_phase` (`pre_assignment`, `post_assignment_prebuild`)
- `rated_by_user_id`
- `rating` (`1..5`)
- `created_at`
- `updated_at`

Constraints:

- one active rating per `application_id + focus_area_id + rated_by_user_id`
- update overwrites prior rating by the same user for the same theme

### 2. `question_generation_threads`

Purpose:
- stable identity for a question card across its generated versions

Suggested fields:

- `id`
- `application_id`
- `focus_area_id`
- `question_group_id` or nullable `question_group_label_snapshot`
- `base_question_id`
- `current_active_version_id`
- `is_locked_after_build`
- `created_at`
- `updated_at`

Meaning:
- one thread represents one visible question slot/card
- versions hang off this thread

### 3. `question_generated_versions`

Purpose:
- store each generated question variant

Suggested fields:

- `id`
- `thread_id`
- `application_id`
- `focus_area_id`
- `base_question_id`
- `version_index`
- `question_text`
- `generation_source` (`system_initial`, `admin_regenerate`, `interviewer_regenerate`)
- `generated_by_user_id` nullable for initial system generation
- `parent_version_id` nullable
- `is_active`
- `is_visible_in_recent_cycle`
- `created_at`

Recommended snapshots for traceability:

- `theme_title_snapshot`
- `theme_direction_snapshot`
- `question_group_label_snapshot`
- `application_context_snapshot` as compact JSON
- `retrieval_context_snapshot` as compact JSON

### 4. `question_version_feedback`

Purpose:
- store rating on generated question versions

Suggested fields:

- `id`
- `question_version_id`
- `application_id`
- `rated_by_user_id`
- `surface_role`
- `surface_phase`
- `rating` (`1..5`)
- `created_at`
- `updated_at`

Constraints:

- one rating per user per generated version

### 5. `vector_corpus_queue` or equivalent async indexing log

Purpose:
- reliably mirror generated artifacts into vector storage

Suggested fields:

- `id`
- `entity_type` (`theme_feedback`, `question_generated_version`)
- `entity_id`
- `operation` (`upsert`, `delete`)
- `status` (`queued`, `processing`, `completed`, `failed`)
- `last_error`
- `created_at`
- `updated_at`

This can reuse an existing processing job pattern if preferred.

## Vector Database Design

## Corpus Philosophy

The vector DB is not the primary store of applicant source material.

It is a corpus of:

- generated theme outputs
- generated question outputs
- ratings
- role metadata
- limited context snapshots

This lets the system retrieve examples like:

- highly rated questions for similar focus areas
- poorly rated questions to avoid repeating patterns
- similar themes and lines of inquiry

## Recommended Vector Documents

### Theme Document

Store:

- `application_id`
- `focus_area_id`
- `theme_title`
- `theme_direction`
- `territory`
- `what_makes_it_worth_time`
- aggregated rating metadata
- actor role metadata

### Question Version Document

Store:

- `question_version_id`
- `thread_id`
- `application_id`
- `focus_area_id`
- `theme_title_snapshot`
- `theme_direction_snapshot`
- `question_text`
- `version_index`
- `generation_source`
- generated/rated metadata
- star rating aggregates
- compact application-context summary

## Retrieval Strategy For Regeneration

When regenerating a question:

1. Build the applicant-grounded context from current application review and parent theme.
2. Query vector DB for similar prior generated questions using:
   - theme title
   - theme direction
   - current question text
   - optional applicant-profile tags
3. Prefer:
   - high-rated examples
   - recent examples
   - examples from similar themes
4. Optionally include some low-rated examples as negative guidance.

## Regeneration Prompt Contract

Inputs:

- current application review context
- parent theme title
- parent theme interview direction
- current active question text
- retrieved similar generated question examples
- retrieved low-rated anti-pattern examples if used

Prompt constraints:

- stay grounded in the current applicant and current theme
- preserve the purpose of the focus area
- produce one improved interview question
- avoid duplicating current sibling questions if possible
- do not change the theme itself

Output:

- one new generated question string

## API Design

## New Read Endpoints

### `GET /applications/{application_id}/prebuild-feedback`

Returns:

- theme ratings
- question thread summaries
- active question version
- recent version list for each question
- lock state
- current actor permissions

Purpose:
- hydrate page-view controls with one request

## New Mutation Endpoints

### `POST /applications/{application_id}/themes/{focus_area_id}/rating`

Body:

- `rating`

Rules:

- allowed only pre-build
- admin only before assignment
- interviewer only after assignment

### `POST /applications/{application_id}/questions/{thread_id}/versions/{version_id}/rating`

Body:

- `rating`

Rules:

- version must be generated
- allowed only pre-build

### `POST /applications/{application_id}/questions/{thread_id}/regenerate`

Body:

- optional `instruction` if desired later

Behavior:

- validate actor permissions
- validate pre-build lock
- retrieve application context
- retrieve vector corpus examples
- generate new question
- create new version
- set it active
- trim visible recent cycle to 5
- enqueue vector indexing

### `POST /applications/{application_id}/questions/{thread_id}/activate-version`

Body:

- `version_id`

Behavior:

- sets selected recent version active
- no generation call
- pre-build only

## Lock-State Endpoint Extension

Current build/create workspace flow should expose whether regeneration is still allowed.

Recommended field additions in existing detail responses:

- `prebuild_generation_locked: boolean`
- `prebuild_generation_lock_reason: string | null`

## Permissions

## Authorization Matrix

### Admin

- unassigned application:
  - rate themes: yes
  - rate questions: yes
  - regenerate questions: yes
  - activate question version: yes
- assigned application:
  - all above: no

### Interviewer

- before assignment:
  - all above: no
- assigned and pre-build:
  - rate themes: yes
  - rate questions: yes
  - regenerate questions: yes
  - activate question version: yes
- post-build:
  - all above: no

## State Transition Design

### Current Application Lifecycle

Important current states:

- `READY`
- `ASSIGNED`
- workspace not yet created
- workspace created / build initiated
- `launched`
- `postgame`
- `completed`

### New Feature Gate

Feature should be enabled when:

- application is `READY` and unassigned for admin
- application is `ASSIGNED` and no workspace exists yet for interviewer

Feature should lock when:

- interview workspace is created from `Build Interview Plan`

If the current implementation creates a workspace before the explicit build click, introduce a dedicated boolean such as:

- `prebuild_generation_locked_at`

Recommended behavior:

- lock exactly when the interviewer confirms `Build Interview Plan`
- not merely on passive page view

## Frontend Design Notes

## Type Additions

Add types for:

- `ThemeRating`
- `QuestionVersion`
- `QuestionThread`
- `PrebuildFeedbackState`
- `GenerationLockState`

## Component Changes

### Review Page Rendering

Where Page 4/Page 5 cards render, add:

- inline theme star component
- inline question star component
- regenerate button on generated questions
- version arrows
- version counter

### Visibility Rules

Hide all controls when:

- actor lacks ownership
- question is not generated
- build lock is active

Disable with explanation tooltip when useful, rather than silently hiding, if the product wants clarity.

### Build Modal

When interviewer triggers build:

- confirmation text should explain regeneration lock
- this modal should be the last checkpoint before entering workspace-only editing mode

## Migration Strategy

## Initial Backfill

Existing generated Page 5 questions likely come only from final report content today.

Recommended migration path:

1. Create question threads for existing generated Page 5 questions.
2. Create one initial generated version per existing generated question with:
   - `generation_source = system_initial`
   - `version_index = 1`
   - `is_active = true`
3. Seed no ratings initially.

Themes can be rate-enabled without a separate version model.

## Version Retention

Backend may store all generated versions.
UI only cycles the most recent 5.

This gives:

- clean UI
- fuller future corpus for retrieval

## Risks And Edge Cases

## 1. Workspace Creation Timing

Risk:
- current code may create workspace before the user mentally considers the build step final

Mitigation:
- ensure the actual lock happens only on explicit build confirmation
- if workspace creation currently happens too early, separate `workspace draft existence` from `generation locked`

## 2. Existing Question Identity Drift

Risk:
- Page 5 questions may not currently have stable thread IDs across renders

Mitigation:
- introduce durable thread IDs during backfill and for new generated reports

## 3. Rating Ambiguity

Risk:
- users may expect ratings to apply to edited/manual text

Mitigation:
- show rating controls only on generated-tag cards and versions
- label clearly as `Rate this generated question`

## 4. Retrieval Quality

Risk:
- early corpus may be sparse or noisy

Mitigation:
- always keep applicant/theme grounding primary
- treat vector retrieval as assistive, not authoritative
- fall back gracefully when retrieval is weak

## 5. Surface Duplication

Risk:
- admin page view and interviewer pre-build page view may implement the same controls twice

Mitigation:
- create reusable page-card controls shared across both surfaces

## 6. Concurrent Version Changes

Risk:
- user rapidly regenerates or switches versions

Mitigation:
- serialize per-question regenerate actions
- disable regenerate while a generation request is in flight
- always return the authoritative active version from backend

## 7. Assignment Boundary Race

Risk:
- admin begins action while assignment changes ownership

Mitigation:
- backend enforces ownership at mutation time
- frontend refreshes permission snapshot after assign/reassign

## Testing Strategy

## Backend

- permission tests for admin/interviewer ownership
- lock-state tests for pre/post build
- regenerate creates new question version
- active version switching works
- only generated versions accept ratings
- theme ratings persist and update
- vector queue entries are created

## Frontend

- admin sees controls only pre-assignment
- interviewer sees controls only post-assignment pre-build
- build modal warns about lock
- regenerate updates active question text
- version arrows cycle through recent 5
- rating updates active generated version/theme

## Retrieval / Integration

- regeneration works with empty vector corpus
- regeneration works with retrieved examples
- low-rated examples do not break generation flow

## Implementation Order

1. Add database schema for threads, versions, and ratings.
2. Add lock-state fields and permission helpers.
3. Backfill existing Page 5 generated questions into threads and initial versions.
4. Add prebuild feedback read endpoint.
5. Add theme rating endpoint.
6. Add question version rating endpoint.
7. Add question regenerate endpoint.
8. Add activate-version endpoint.
9. Add vector indexing pipeline for generated artifacts.
10. Add admin page-view controls.
11. Add interviewer pre-build controls.
12. Add build confirmation modal and lock behavior.
13. Add focused tests.

## Recommended Non-Goals For First Release

- freeform user instructions on regenerate
- theme regeneration
- multi-question batch regeneration
- retrieval analytics UI
- exposing more than 5 versions in the first-pass interface

## Release Definition

First release is successful when:

- theme cards can be rated inline pre-build
- generated question cards can be rated and regenerated inline pre-build
- question version arrows work for the latest 5 versions
- admin/interviewer ownership rules are enforced correctly
- `Build Interview Plan` permanently locks further regeneration
- generated question history and ratings are persisted
- generated artifacts are mirrored into vector storage for future retrieval
