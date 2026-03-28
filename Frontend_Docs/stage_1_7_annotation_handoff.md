# Stage 1.7 Annotation Handoff

## Purpose

This document is the unified handoff for the current Stage 1.7 implementation state after the deterministic review-flow drift fixes and the post-synthesis annotation overlay work.

It is intended to let frontend/UI work continue without needing to rediscover:

- what changed in the backend contract
- what stayed intentionally unchanged
- where annotation data now lives
- what the current frontend rendering layer already supports
- what remains scaffolding versus polished UI

This document should be read as a current-state implementation handoff, not as a fresh product spec.

---

## 1. What We Preserved

The recent work was intentionally additive and low-risk.

The following core structures and flows were preserved:

- deterministic review package persistence remains backend-owned
- `CanonicalRecord.pages_1_3` remains the persisted deterministic Pages 1-3 artifact
- top-level ROS Pages 1-5 shape remains unchanged
- admin upload flow remains unchanged
- assignment and reassignment behavior remain unchanged
- publish flow remains unchanged
- Call 2 contract remains unchanged
- no new database columns or migrations were introduced

Important boundary:

- deterministic Pages 1-3 are still the base review package
- post-synthesis highlighting is not stored inside `pages_1_3`
- highlights are attached only to synthesized draft/published content

---

## 2. What Changed At A High Level

Two implementation tracks are now in place.

### A. Drift-remediation review flow

The repo already had the review-flow correction work in place:

- upload persists canonical, deterministic signals, and Pages 1-3
- admin and interviewer review pages use the deterministic review package instead of canonical JSON as the primary review artifact
- raw source PDF can be opened from the review package UI

### B. New post-synthesis annotation overlay

We added a minimal annotation layer that activates after synthesis completes.

This layer:

- highlights whole Page 2 entities using existing signal `referenced_entity_ids`
- highlights exact Page 3 essay fragments using new signal `supporting_fragment_ids`
- keeps annotation data separate from deterministic review-package data
- gives frontend enough provenance to support hover, badges, borders, underline styles, or future richer interactions

---

## 3. Backend Contract Changes

### 3.1 New additive location

The new annotation payload is attached only inside synthesized draft content:

```json
signal_data.annotations
```

This exists in synthesized outputs such as:

- `latest_draft.content`
- `published_draft.content`
- fake harness final ROS output

It does not modify the deterministic `review_package.pages_1_3` structure.

### 3.2 New additive signal field

Call 1 signal output now supports an optional field:

```json
"supporting_fragment_ids": ["ESS-001:F02", "ESS-001:F03"]
```

This is only for essay-derived evidence.

Themes do not emit fragment IDs directly.
Call 2 does not emit fragment IDs.

### 3.3 New annotation shape

Current annotation shape:

```json
{
  "page_1_entities": {},
  "page_2_entities": {
    "ACA-004": {
      "signal_ids": ["SIG-002"],
      "theme_ids": ["THEME-001"]
    }
  },
  "page_3_fragments": {
    "ESS-001": [
      {
        "fragment_id": "ESS-001:F02",
        "start_char": 120,
        "end_char": 248,
        "signal_ids": ["SIG-001"],
        "theme_ids": ["THEME-001"]
      }
    ]
  }
}
```

Design intent:

- `page_1_entities` is structurally supported but currently expected to be empty
- `page_2_entities` is deterministic and derived from existing entity references
- `page_3_fragments` is derived from validated essay fragment references returned by Call 1

---

## 4. Backend Implementation Details

### 4.1 Deterministic fragment generation

New file:

- [essay_fragments.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/essay_fragments.py)

What it does:

- builds stable essay fragments before Call 1
- prefers paragraph-based fragments
- falls back to sentence-group fragments when paragraph boundaries are unavailable
- computes exact `start_char` and `end_char` from the original stored essay text

Current fragment rules:

- paragraph split when blank-line structure exists
- otherwise sentence grouping
- max 2 sentences per fallback fragment
- fragment IDs use `ESS-###:F##`

### 4.2 Projection builder changes

Updated file:

- [projection_builder.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/projection_builder.py)

What changed:

- Call 1 projection now includes `essay_fragments`
- this is added alongside existing `essay_profile`, `entity_id_map`, and `deterministic_signals`

Result:

- the LLM is asked to choose from a provided fragment list
- the backend no longer needs fuzzy quote matching after generation

### 4.3 Call 1 prompt and schema changes

Updated file:

- [signal_interpreter.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/signal_interpreter.py)

What changed:

- prompt now explicitly instructs the model to use only provided `essay_fragments`
- output schema example now includes `supporting_fragment_ids`
- prompt forbids invented fragment IDs and raw character offsets

### 4.4 Validation changes

Updated file:

- [guard.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/policy/guard.py)

What changed:

- `validate_signals(...)` now accepts optional `essay_fragments`
- `supporting_fragment_ids` must be an array if present
- fragment IDs are deduplicated
- per-signal fragment count is capped at 3
- invented fragment IDs are rejected
- cross-essay mismatches are rejected
- sanitized signals preserve validated `supporting_fragment_ids`

Validation guarantees:

- frontend can trust fragment spans in synthesized output
- backend remains authoritative for what is allowed to be highlighted

### 4.5 Annotation assembly

New file:

- [report_annotations.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/report_annotations.py)

What it does:

- derives `page_2_entities` from signal `referenced_entity_ids`
- derives `page_3_fragments` from validated signal `supporting_fragment_ids`
- attaches signal and theme provenance to each annotation target
- returns the normalized `signal_data.annotations` block

Current derivation logic:

- Page 2 uses entity collections `academic_entries`, `test_entries`, and `activity_entries`
- Page 3 uses resolved essay fragments
- theme linkage is derived from signal-to-theme assignment, not generated independently

### 4.6 Orchestrator integration

Updated file:

- [orchestrator.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/app/agents/orchestrator.py)

What changed:

- gets `essay_fragments` from the Call 1 projection
- passes them into `validate_signals(...)`
- builds `annotations = build_report_annotations(...)`
- adds `signal_data.annotations` to synthesized output

Important:

- deterministic persistence still happens before the LLM boundary
- the annotation layer only appears in synthesis output
- the persisted deterministic review package itself remains unchanged

---

## 5. Frontend Scaffolding Status

### 5.1 Review-package rendering split

Updated file:

- [ReviewPackageSection.tsx](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/frontend/components/ReviewPackageSection.tsx)

What changed:

- still renders the review package from `review_package.pages_1_3`
- now optionally extracts annotations from `annotationSource.signal_data.annotations`
- continues to show Page 1 as JSON
- routes Page 2 and Page 3 into typed renderers

This means:

- the base review package remains the source for review content
- draft/published content is only used as an annotation overlay source

### 5.2 New typed Page 2 and Page 3 components

New file:

- [ReviewPackagePages.tsx](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/frontend/components/ReviewPackagePages.tsx)

Current behavior:

- Page 2:
  - parses review-package sections into typed lists
  - highlights whole entries if their `entity_id` appears in `page_2_entities`
  - shows lightweight provenance text and hover `title`
- Page 3:
  - parses essays from the review package
  - applies inline text highlighting using `start_char` and `end_char`
  - exposes hover `title` with signal/theme IDs

This is scaffolding, not final UI design.

Current visual treatment is intentionally basic:

- blue card tint / border for Page 2 entities
- amber underline/highlight for Page 3 fragments
- title-based hover metadata only

### 5.3 Admin and interviewer page wiring

Updated files:

- [frontend/app/admin/applications/[id]/page.tsx](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/frontend/app/admin/applications/[id]/page.tsx)
- [frontend/app/interviewer/applications/[id]/page.tsx](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/frontend/app/interviewer/applications/[id]/page.tsx)

What changed:

- admin passes `item.published_draft?.content` into `ReviewPackageSection` as `annotationSource`
- interviewer passes `item.latest_draft?.content` into `ReviewPackageSection` as `annotationSource`

Current consequence:

- interviewer sees post-synthesis highlights during draft work
- admin sees post-synthesis highlights only through published content
- pre-synthesis review remains plain deterministic Pages 1-3

That matches current role boundaries and existing draft visibility rules.

---

## 6. Current Data Flow

### 6.1 Deterministic phase

1. Upload PDF
2. Run deterministic extraction
3. Assemble canonical
4. Project ROS Pages 1-3
5. Detect deterministic signals
6. Persist canonical + deterministic signals + Pages 1-3

### 6.2 Synthesis phase

1. Load persisted deterministic state
2. Build Call 1 projection
3. Add `essay_fragments`
4. Run Call 1 for signals and themes
5. Validate `supporting_fragment_ids`
6. Run Call 2 for question groups
7. Assemble ROS
8. Attach `signal_data.annotations`

### 6.3 Frontend overlay phase

1. Render `review_package.pages_1_3`
2. If draft/published `signal_data.annotations` exists:
3. Overlay Page 2 entity highlighting
4. Overlay Page 3 fragment highlighting

This separation is important:

- the review package is still deterministic and stable
- the annotation layer is synthesis-aware and optional

---

## 7. Fake LLM Harness Status

Updated file:

- [stage17_fake_llm_harness.py](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/scripts/stage17_fake_llm_harness.py)

What changed:

- fake harness now builds projection dynamically
- it includes generated `essay_fragments`
- fake Call 1 output now includes `supporting_fragment_ids`
- validation runs against the new fragment-aware rules
- final fake ROS includes `signal_data.annotations`

Useful generated artifacts:

- [01_call_1_projection_input.json](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/stage17_fake_llm_output/01_call_1_projection_input.json)
- [04_call_1_sanitized_output.json](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/stage17_fake_llm_output/04_call_1_sanitized_output.json)
- [09_final_ros.json](C:/Users/vibha/OneDrive/Desktop/AG_InterviewStandardiser/tests/stage17_fake_llm_output/09_final_ros.json)

These are now the easiest references for frontend iteration because they show the end-state shape with:

- `supporting_fragment_ids`
- `signal_data.annotations.page_2_entities`
- `signal_data.annotations.page_3_fragments`

---

## 8. Testing And Verification Completed

Backend and integration checks that were added or updated:

- fragment-generation tests
- fragment-validation acceptance/rejection tests
- report-annotation derivation tests
- orchestrator split test updated for annotations

Verified commands:

```powershell
pytest tests/test_signal_detector.py tests/test_orchestrator_stage17_split.py tests/test_interviewer_api.py -q
```

```powershell
python scripts\stage17_fake_llm_harness.py
```

```powershell
cd frontend
npm run build
```

---

## 9. What Is Scaffolding Vs Finished

### Finished enough to build on

- backend annotation contract
- essay fragment generation
- signal validation for fragment refs
- synthesized annotation attachment
- fake harness support
- frontend overlay plumbing
- typed Page 2 and Page 3 renderers

### Still scaffolding / intentionally basic

- Page 1 remains JSON-only
- Page 2 card styling is placeholder emphasis only
- Page 3 inline highlight styling is placeholder emphasis only
- hover UI uses plain `title` attributes only
- annotation labels are not yet product-polished
- there is no richer side panel, chip system, or interaction model yet

This is deliberate. The backend option surface is now present so the UI can evolve without changing the data contract again.

---

## 10. What Frontend Work Can Safely Assume Next

For the next UI pass, the frontend can safely assume:

- `review_package.pages_1_3` remains the base review artifact
- synthesized annotations are optional
- if present, annotations live at `signal_data.annotations`
- Page 2 highlighting is whole-entity by `entity_id`
- Page 3 highlighting is span-based using exact char offsets
- annotation provenance is available through `signal_ids` and `theme_ids`

That means the next UI iteration can focus on presentation choices such as:

- stronger card design for Page 2
- better inline essay highlighting on Page 3
- hover cards instead of native titles
- badges, legend, chips, or side metadata
- richer cross-linking between Pages 2-5

without changing the backend contract.

---

## 11. Recommended Next Step

The next frontend phase should treat this work as the stable data/scaffolding layer and focus on:

- replacing placeholder visual emphasis with intentional UI treatment
- improving readability of highlighted Page 2 entries
- making Page 3 essay highlighting feel editorial rather than debug-like
- deciding whether hover, click, or passive annotation presentation best fits interviewer workflow

The backend does not need another redesign before that work starts.
