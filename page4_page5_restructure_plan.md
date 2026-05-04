# Page 4 / Page 5 Restructure — Implementation Plan

## What We're Changing

**Page 4** becomes a rich context dossier per focus area (read before the interview).  
**Page 5** becomes a lean line-of-questioning sheet per focus area (used during the interview).

### New Schema

**Page 4 — Focus Area** (`FocusArea`)
| Field | Change | Notes |
|---|---|---|
| `focus_area_id` | Keep | |
| `title` | Keep | |
| `territory` | **Enrich** | Absorbs the narrative richness of P5's `what_happened` + `why_it_matters_here`, consolidated at focus-area level. Not event retelling — interpretive read + evidence grounding. |
| `what_makes_it_worth_time` | Keep | Already adds value, no change needed. |
| `what_to_find_out` | **Remove** | Moves to Page 5 as `line_of_inquiry`. |
| `source_theme_ids` | Keep | |
| `source_signal_ids` | Keep | |

**Page 5 — Question Group** (replaces `OpeningGroup`)
| Field | Change | Notes |
|---|---|---|
| `focus_area_id` | Keep | Links back to P4. |
| `group_label` | **Renamed** from `group_title` | Broad label for the set of questions. |
| `line_of_inquiry` | **New** (was `what_to_find_out` on P4) | Single strategic goal statement for this group. |
| `questions` | **New** (replaces `openings[]`) | Array of 2–4 questions. |
| `questions[].question_id` | **New** | Replaces `opening_id`. |
| `questions[].question` | **New** | Replaces `sample_question`. Just the question text. |
| `source_theme_ids` | Keep (group level) | |
| `source_signal_ids` | Keep (group level) | |

**Removed from Page 5:**  
`hook`, `what_happened`, `why_it_matters_here`, `sample_question`, `opening_id`, per-question `source_signal_ids`

---

## Layers to Touch (in order)

### 1. Backend — LLM Prompts

**File:** `app/agents/interview_synthesizer.py` (Call 2 — generates Page 4)
- Update system prompt: instruct richer `territory` — include interpretive read AND specific evidence grounding from the application. No longer a 1–2 sentence summary.
- Remove `what_to_find_out` from output schema in prompt.
- Remove `what_to_find_out` from the bad/good examples.

**File:** `app/agents/interview_generator.py` (Call 3 — generates Page 5)
- Rewrite system prompt entirely:
  - Remove instructions about `hook`, `what_happened`, `why_it_matters_here`, `sample_question`.
  - Add instructions for `line_of_inquiry` (inherits the strategic goal job) and `questions[]`.
  - Output schema changes: `opening_groups` → keep key name for now for backward compat OR rename to `question_groups`.
  - Prohibit question forms: `"Tell me about"`, `"Walk me through"` etc. still apply.
  - Instruct 2–4 questions per group.

---

### 2. Backend — Policy Guard

**File:** `app/policy/guard.py`

**`_normalize_focus_area_output()` (line ~272):**
- Remove `what_to_find_out` from normalization mapping.
- Keep all other fields.

**`validate_focus_areas()` (line ~851):**
- Remove `what_to_find_out` from `required` fields list (line ~924–932).
- The rest of the validation logic (ID format, source_theme/signal linkage, count 2–3) stays unchanged.

**`_normalize_opening_group_output()` (line ~210):**
- Replace per-opening field normalization:
  - Remove: `hook`, `what_happened`, `why_it_matters_here`, `sample_question` per item.
  - Add: normalize `line_of_inquiry` at the **group** level.
  - Per item: only `question_id` and `question` (use `_first_present` with `["question", "text", "sample_question"]` for backward compat during transition).
- Rename `group_title` → `group_label` in normalization (use `_first_present(["group_label", "group_title", ...])` for compat).

**`validate_opening_groups()` (find in guard.py ~line 1100+):**
- Update required fields per group: remove opening-level fields, add `line_of_inquiry`.
- Update per-item required fields: `question_id`, `question` only.
- Update count check: still 2–4 items per group (same policy, different name — "questions" not "openings").

---

### 3. Backend — Pydantic Schemas

**File:** `app/api/schemas.py`

- **`OpeningCard`** → rename to `QuestionCard`:
  - Remove: `hook`, `what_happened`, `why_it_matters_here`, `line_of_inquiry`, `sample_question`, `source_signal_ids`
  - Add: `question_id: str`, `question: str`

- **`OpeningGroup`** → rename to `QuestionGroup`:
  - Remove: `openings: list[OpeningCard]` → `questions: list[QuestionCard]`
  - Rename: `group_title` → `group_label`
  - Add: `line_of_inquiry: str`

- **`Page5InterviewOpenings`** → rename to `Page5QuestionGroups`:
  - `opening_groups` → `question_groups`

- **`FocusArea`**:
  - Remove: `what_to_find_out`

- **`SynthesisOutput`**:
  - `page_5_interview_openings: Page5InterviewOpenings` → `page_5_question_groups: Page5QuestionGroups`

- **`InterviewWorkspaceOpening`** → rename to `InterviewWorkspaceQuestion`:
  - Remove: `hook`, `what_happened`, `why_it_matters_here`, `sample_question`
  - Keep: `id`, `text` (this is the question text), `source`, `status`, `note`, `order`, `follow_ups`
  - Add: `line_of_inquiry: str = ""` (on the **theme** level, not question level — see below)

- **`InterviewWorkspaceTheme`**:
  - Remove: `unifying_axis`, `opening_group_title` (legacy), `openings` (legacy)
  - Keep: `id`, `source`, `title`, `territory`, `what_makes_it_worth_time`, `interview_direction`, `question_group_title`, `questions`
  - Rename: `interview_direction` → keep this — it already maps to `what_to_find_out` / `line_of_inquiry`
  - `question_group_title` replaces `opening_group_title`

> **Note on backward compat:** `interview_workspace.py` already has dual-path logic (`openings or questions`, `opening_group_title or question_group_title`). Use this pattern to smooth the transition.

---

### 4. Backend — Workspace Seed Builder

**File:** `app/interview_workspace.py`

**`build_workspace_seed()` (line ~106):**
- Update to read from new Page 5 structure: `question_groups` instead of `opening_groups`.
- Map `group_label` → `question_group_title` on the theme.
- Map `line_of_inquiry` → `interview_direction` on the theme.
- Map `questions[]` → `questions` on the theme (using `_normalize_opening` on each item — or a new simpler `_normalize_question` since the shape is much simpler now).
- Remove `what_to_find_out` from Page 4 mapping (it no longer exists).

**`_normalize_opening()` (line ~42):**
- Can be simplified or kept with the old fields blanked for legacy workspaces.
- Add a new `_normalize_question()` helper for the new shape: `{ id, text, source, status, note, order, follow_ups }`.

**`normalize_workspace_content()` (line ~168):**
- Update to handle new field names cleanly.
- Keep backward compat aliases for existing saved workspaces in DB.

---

### 5. Backend — Refinement Context Builder

**File:** `app/interview_refinement.py`

**`_build_question_note_context()` (line ~91):**
- Remove references to `question.hook`, `question.what_happened`, `question.sample_question`.
- Replace with: `question.text` (the actual question), theme's `interview_direction` (line of inquiry), theme's `title`.
- New context lines:
  ```
  Focus area: {theme.title}
  Group label: {theme.question_group_title}
  Line of inquiry: {theme.interview_direction}
  Question: {question.text}
  Question status: {question.status}
  ```

**`_build_follow_up_context()` (line ~120):**
- Same — replace `question.hook` and `question.sample_question` with `question.text`.

**`_build_final_summary_context()` (line ~152):**
- Remove `what_happened`, `line_of_inquiry`, `sample_question` per question.
- Replace with: `question.text` and `question.note`.
- Keep follow-ups unchanged.

> **Refinement modes themselves (`question_note`, `follow_up_note`, `final_summary`) do not change** — only the context strings fed to the LLM change. The custom instruction prompt feature is fully preserved.

---

### 6. Backend — ROS Assembler

**File:** `app/ros/assembler.py` (or wherever `assemble_ros_v1()` lives)
- Update `page_5_interview_openings` key → `page_5_question_groups`.
- Update how it maps Call 3 output into the ROS structure.

---

### 7. Frontend — Pre-Interview Edit (Page 5 surface)

The edit UI per theme card should now expose:

**Per AI-generated group:**
- Edit `group_label` (text field)
- Edit `line_of_inquiry` (text field)  
- List of questions: edit text, add question, remove question

**Custom group:**
- Set `group_label`
- Set `line_of_inquiry`
- Add / edit / remove questions

**Remove from edit UI:**
- Hook editing
- `what_happened` editing
- `why_it_matters_here` editing
- `sample_question` as a separate field (it's just `question` now)

---

### 8. Frontend — Interview Overlay

Per group (by `group_label`):
- Show `line_of_inquiry` as a header/subtitle under the group label
- Per question: note field (unchanged)
- Per group: add follow-up (unchanged — follow-ups stay at question level per current model, or per group — confirm with existing behaviour)

---

### 9. Frontend — Final Report / Postgame Tab

Per group:
- Edit `group_label`
- Edit `line_of_inquiry`
- Per question: edit question text, edit note, refine note (AI) with custom instruction
- Custom groups: same behaviour

> **Refinement** — the AI refine button and custom instruction field are preserved exactly. Only the context passed to the backend changes (handled in step 5).

---

## What Is NOT Changing

- Call 1 (signal interpreter) — untouched
- Policy guard for Call 1 and Call 2 (count rules, ID format rules, language rules) — unchanged except removing `what_to_find_out` from required fields
- The refinement modes API contract — unchanged
- Follow-up structure — unchanged
- `final_summary` refinement — unchanged
- All auth, storage, processing job logic — untouched
- Copilot / report chat — deferred (user's note)

---

## Implementation Order

1. `interview_synthesizer.py` prompt (Call 2) — Page 4 richer territory, remove `what_to_find_out`
2. `interview_generator.py` prompt (Call 3) — new Page 5 shape
3. `app/api/schemas.py` — new Pydantic models
4. `app/policy/guard.py` — normalizers + validators for both calls
5. `app/interview_workspace.py` — seed builder + normalizer
6. `app/interview_refinement.py` — context builders
7. `app/ros/assembler.py` — ROS assembly
8. Run `run_stage_1_8_trace.py` on all 4 passing PDFs to verify end-to-end
9. Frontend edit UI (Page 5 surface)
10. Frontend overlay
11. Frontend postgame / final report

