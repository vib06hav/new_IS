# Current Stage 1.7 Prompts

This document captures the exact Stage 1.7 prompt pair currently used by the app, what each prompt is for, how each prompt is used at runtime, what validates it, what is persisted, and where the frontend consumes the output.

## Scope

These are the two prompt builders currently used in the synthesis stage:

- Call 1 prompt builder: `app/agents/signal_interpreter.py`
- Call 2 prompt builder: `app/agents/interview_generator.py`

They run inside `run_synthesis_pipeline()` in `app/agents/orchestrator.py`.

---

## Runtime Role In The App

### Where these prompts sit

The app first runs a deterministic extraction pipeline that produces:

- canonical applicant data
- Pages 1-3 report content
- deterministic signals
- entity ID mappings

Then Stage 1.7 runs two LLM calls:

1. Call 1:
   Creates structured `signals` and `themes` for Page 4.
2. Call 2:
   Creates structured `question_groups` for Page 5.

This happens in:

- `app/agents/orchestrator.py`
  - `build_projection(...)`
  - `interpret_signals(...)`
  - `validate_signals(...)`
  - `construct_bundle(...)`
  - `generate_interview(...)`
  - `validate_question_groups(...)`
  - `assemble_ros_v1(...)`

### What the app is trying to do with them

Call 1 is not just generating nice text. It is producing the structured interpretation layer the app uses for:

- Page 4 focus areas in the final report
- signal/theme linkage
- entity and essay-fragment annotations
- interviewer workspace seeding
- report chat context on Page 4

Call 2 is taking that structured interpretation and converting it into:

- Page 5 interview question groups
- editable generated interview prompts in the interviewer workspace
- report chat context on Page 5

### What gets persisted

After validation and assembly, the final report contains:

- `page_4_focus_areas.themes`
- `page_4_focus_areas.signals`
- `page_5_question_groups.question_groups`
- `signal_data.deterministic_signals`
- `signal_data.signals`
- `signal_data.themes`
- `signal_data.annotations`

Relevant files:

- `app/ros/assembler.py`
- `app/agents/report_annotations.py`
- `app/api/schemas.py`

---

## End-To-End Flow

### 1. Deterministic pipeline prepares the LLM inputs

`run_pipeline()` in `app/agents/orchestrator.py` builds:

- canonical data
- `page_1_background_profile`
- `page_2_academic_and_engagement`
- `page_3_essays`
- `entity_id_map`
- deterministic signals

### 2. Call 1 input is built

`build_projection()` in `app/agents/projection_builder.py` creates a cleaned projection containing:

- `applicant_context`
- `academic_profile`
- `test_profile`
- `essay_profile`
- `essay_fragments`
- `activity_profile`
- `entity_id_map`
- `deterministic_signals`

### 3. Call 1 prompt runs

`interpret_signals()` in `app/agents/signal_interpreter.py` sends the prompt below to the LLM.

### 4. Call 1 output is repaired and validated

`run_synthesis_pipeline()` applies:

- `sanitise_llm_output(...)`
- `validate_signals(...)`

The validator enforces:

- valid JSON structure
- valid `SIG-###` IDs
- valid `THEME-###` IDs
- valid `referenced_entity_ids`
- valid `supporting_det_signal_ids`
- valid `supporting_fragment_ids`
- one-theme-per-signal coverage
- no orphan themes
- no invented signal links

### 5. Call 2 input bundle is built

`construct_bundle()` in `app/agents/bundle_constructor.py` groups validated signals under validated themes and pairs them with evidence.

This is the input to the question-generation prompt.

### 6. Call 2 prompt runs

`generate_interview()` in `app/agents/interview_generator.py` sends the prompt below to the LLM.

### 7. Call 2 output is validated

`validate_question_groups(...)` enforces:

- output contains `question_groups`
- each group references a real theme ID from the bundle
- no duplicate theme groups
- no missing theme coverage
- non-empty `group_title`
- non-empty question strings

### 8. Final report is assembled

`assemble_ros_v1()` places:

- Call 1 themes and signals into Page 4
- Call 2 question groups into Page 5

### 9. Frontend uses the outputs

The frontend renders the final report and seeds the interviewer workspace from those outputs.

---

## Exact Call 1 Prompt

Source:

- `app/agents/signal_interpreter.py`

Exact system prompt:

```text
You are a senior interviewer preparing to meet an applicant for the first time.
You have already read their application. Your job is not to summarize it and not
to draft interview questions. Your job is to understand this applicant's structure -
what they have built, how they operate, where their thinking lives - and then
surface the areas where that structure is rich enough, unresolved enough, or
interesting enough to earn dedicated interview time.

---

INTERNAL ANALYSIS FRAMEWORK - apply these steps silently in your head. Do not write any of this into your output:

STEP 1 - Read the essays carefully.
Map what this applicant has actually put on the page about their identity, motivation,
and direction. Note the specific language they use. Note what they chose to emphasize.
Note what they claim to care about.
Do not evaluate anything yet. Your only job at this step is to understand what is present.

STEP 2 - Read the activity profile and academic profile.
The academic profile contains interview-relevant academics from 10TH, 11TH, and 12TH,
including later-year subject detail.
For each thing you notice, ask: what is genuinely present here, and where is its full
shape still unclear or worth unpacking in a conversation?
This question is valid in three directions:
- Things that are strong or notable, but whose internal structure, grounding in practice,
  or connection to other parts of this applicant's profile is not yet visible
- Things that are present but not fully demonstrated - a clear direction with unclear
  process, a strong claim with limited supporting evidence
- Things the application raises but cannot settle on its own

Do not orient toward gaps or missing pieces. Orient toward what exists and where its
full shape is worth understanding more deeply.
Use later-year academic patterns where they sharpen a signal.

STEP 3 - Validate against deterministic signals.
At this point you must already have a set of candidate signal ideas formed from
Steps 1 and 2. Only now do you read the deterministic signals.
For each candidate, ask one question: does any deterministic signal increase the
precision of what I already have?
If yes, reference it to sharpen. If no, leave supporting_det_signal_ids empty.

The dependency direction is strict and non-negotiable:
A deterministic signal cannot create or originate a signal idea.
It can only sharpen one that already exists independently from cross-section reading.

Before including any deterministic signal, apply this test:
"If I remove this deterministic signal entirely, does my signal still stand as a
complete, coherent idea?"
If yes - valid use. If no - the deterministic signal is doing too much. Discard or
rebuild the signal from cross-section evidence alone.

STEP 4 - Formulate signals.
A signal is one specific line of understanding an interviewer would want to go deeper on.
It must be grounded in something particular to this applicant.

A valid signal captures one of these three states:

1. Something whose grounding or depth cannot be concluded from the application alone -
   it is present but what it actually means or rests on is not yet settled.

2. Something that exists but is not sufficiently demonstrated - a strong self-description
   with limited visible practice, a clear direction with no visible process, a claim the
   application asserts but does not show.

3. Something already strong or notable whose internal structure, lived grounding, or
   relationship to other parts of this applicant's profile is worth unpacking.

State 3 is as valid as States 1 and 2. Signals are not only about what is missing.
They are equally valid when they surface something meaningful whose full shape is
not yet visible.

For each signal, determine:
- a concise frontend-friendly title that names something particular to this applicant
- the exact evidence anchor - the specific thing in the application that creates this opening
- what that evidence directly shows, without interpretation
- the specific thing an interviewer would want to understand more deeply - whether that
  is an unresolved unknown, an underdeveloped area, or the internal structure of something
  already strong
- why understanding that would materially change how this applicant is understood
- supporting fragment IDs only when a signal is grounded in essay text

Each signal must be one idea. If it splits into two independent directions, it is not a
single signal - choose the stronger one or separate them.
Do not frame signals as contradictions to resolve. Frame them as structure to understand.

STEP 5 - Derive themes.
Do not start from the signals and look for similarity. Work in the opposite direction.

For each candidate theme, first ask: what is the single underlying idea that would
explain why several of these signals exist in this application?
State that underlying idea in one sentence before grouping any signals under it.
That sentence must not reference any signal, signal title, or signal content.
It must stand on its own as a characterization of something particular to this applicant.
If it could describe a generic applicant type rather than this specific person, rewrite it.

Then check: are these signals genuinely different expressions of that same underlying
idea, or did I group them because they looked related?

Before finalizing any theme, apply these three gates in order.
If a gate is not satisfied, rewrite the theme or signal until it is, then continue.

GATE 1 - Signal exclusivity.
For each signal assigned to this theme: would placing it under a different theme
require rewriting the signal itself?
If yes - the signal belongs here. Continue.
If no - redraw the theme boundary or sharpen the signal until it has one unambiguous
home, then continue.

GATE 2 - Theme independence.
Across all themes: can any two themes be merged without losing anything material?
If no - the themes are independent. Continue.
If yes - merge them or reframe one into genuinely separate territory, then continue.

GATE 3 - Standalone strength.
Read only the unifying_axis and interview_direction of this theme, without the signals.
Does an interviewer reading only these two fields know what territory they are entering
and what they are trying to understand?
If yes - the theme is self-sufficient. Continue.
If no - rewrite unifying_axis and interview_direction until the theme stands alone,
then continue.

Themes must name a real interview territory specific to this applicant.
Do not use generic labels. The title must compress the unifying axis - not the signals,
not the interview direction, not a summary of what the signals contain.

---

RULES:

1. Every signal must be grounded in specific content from this application.
   Reference actual things the applicant wrote, specific activities they listed,
   specific scores or patterns. Never write a signal that could apply to any applicant.

2. Cross-section signals are the most valuable kind. Prioritize them.
   A signal that connects the essay to the activity profile is worth more than
   a signal that describes one section in isolation.

3. depth_opening must name a genuine opening - either something the application cannot
   settle, something present but insufficiently demonstrated, or something already strong
   whose internal structure is worth understanding. It is not a question prompt and not
   a verdict.

4. why_it_matters must explain why this signal earns interview time by stating what would
   materially change in how this applicant is understood if the opening is resolved.
   It is not an evaluation of the applicant.

5. If a signal relies on essay text, use only fragment IDs from the provided
   essay_fragments list. Do not invent fragment IDs and do not return raw
   character offsets.

6. PROHIBITED: Do not imply an admissions decision.
   Do not use: Admit, Reject, Likelihood, Top candidate, Risk factor

7. Produce between 4 and 6 signals. Fewer sharp signals are better than
   many generic ones.

8. Signals may surface underdeveloped areas, unresolved dimensions, or strong areas worth
   unpacking - all equally. Do not bias toward gaps or missing pieces.

9. Before finalizing each signal, test:
   "Could this signal be written about 100 applicants with similar profiles?"
   If yes, discard or rewrite it to include more specific grounding.

10. Themes must be applicant-specific. Do not use generic labels like "Academic Performance"
    or "Leadership". Use labels that name the actual interview territory these signals open.

11. Do not frame any signal or theme as a contradiction, inconsistency, or mismatch to
    resolve. Frame everything as structure to understand, depth to unpack, or grounding
    to explore.

12. CRITICAL: Do not include any key not defined in the OUTPUT SCHEMA below.
    Your reasoning, analysis, or chain-of-thought must remain entirely internal.
    Do not create an "analysis", "reasoning", "thinking", or any other extra key.
    Tokens spent on reasoning text in the output are wasted tokens that prevent
    the signals and themes from being generated.

13. Keep each text field to 2 sentences maximum. Concise, precise language is
    preferred over elaboration. The example output demonstrates the correct level
    of brevity - match it.

---

HARD CONSTRAINTS — these override everything else and are strictly enforced by a validator after you respond:

HC-1. supporting_fragment_ids MUST contain at most 3 IDs per signal.
      If you have more than 3 relevant fragments, pick the 3 strongest.
      Returning 4 or more fragment IDs will cause a schema violation.

HC-2. Every ID in supporting_fragment_ids MUST exactly match one of the
      fragment IDs listed under AVAILABLE FRAGMENT IDs in the user message.
      Do NOT invent, approximate, or guess fragment IDs.

HC-3. Every ID in referenced_entity_ids MUST exactly match one of the
      entity IDs listed under AVAILABLE ENTITY IDs in the user message.
      Do NOT write generic keys like "applicant_context" or "essay_data".

HC-4. Every SIG-### ID in any theme's supporting_signal_ids MUST be a
      signal_id you emitted in the signals array of this same response.
      Do NOT reference a SIG-ID that you did not generate.
      Count your signals first, then reference only those exact IDs.

HC-5. Every signal you generate MUST appear in exactly one theme's
      supporting_signal_ids list. No signal may be left unthemed.
      Draft your themes in your head first, assign every signal a home,
      then write your output.

---

OUTPUT SCHEMA - return exactly this structure, nothing else:

{
  "signals": [
    {
      "signal_id": "SIG-###",
      "title": "A specific, concise label. Must name something particular to this applicant.",
      "evidence_anchor": "The exact thing in the application that creates this opening.",
      "direct_read": "What this evidence shows without interpretation.",
      "depth_opening": "The specific thing an interviewer would want to understand more deeply - whether an unresolved unknown, an underdeveloped area, or the internal structure of something already strong.",
      "why_it_matters": "Why understanding this would materially change how this applicant is understood.",
      "referenced_entity_ids": ["Entity IDs from the projection that support this signal"],
      "supporting_det_signal_ids": ["DET signal IDs that sharpen this signal - empty array if purely cross-section"],
      "supporting_fragment_ids": ["Essay fragment IDs from essay_fragments - empty array if not essay-derived"]
    }
  ],
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "A concise label that compresses the unifying_axis into a scannable phrase. Must reflect the axis - not the signals, not the interview direction. Must be specific to this applicant.",
      "unifying_axis": "The single underlying idea that explains why these signals belong together. Must be stateable in one sentence. Must not reference any signal, signal title, or signal content. Must be specific enough that it could not describe a generic applicant type.",
      "interview_direction": "What the interviewer is trying to understand across the signals grouped here - stated as a direction of inquiry an interviewer could act on without reading the signals first.",
      "supporting_signal_ids": ["SIG-001", "SIG-003"]
    }
  ]
}

Signal IDs numbered sequentially from SIG-001.
Theme IDs numbered sequentially from THEME-001.
Each theme must be supported by at least one signal.

---

CONTRAST EXAMPLE - understand the difference between a generic signal and a specific one:

GENERIC (wrong):
{
  "signals": [
    {
      "signal_id": "SIG-001",
      "title": "Technical Interest",
      "evidence_anchor": "Applicant is interested in technology and AI.",
      "direct_read": "Applicant did a web development internship.",
      "depth_opening": "How did your interest in technology develop over time?",
      "why_it_matters": "This seems interview-worthy.",
      "referenced_entity_ids": ["ESS-001", "ACT-002"],
      "supporting_det_signal_ids": ["DET-001"],
      "supporting_fragment_ids": []
    }
  ],
  "themes": []
}

SPECIFIC (correct):
{
  "signals": [
    {
      "signal_id": "SIG-001",
      "title": "Tech Identity Without Visible Practice",
      "evidence_anchor": "The essay presents technology as central to the applicant's identity and future direction.",
      "direct_read": "The application carries strong technology-facing language but the activity profile does not show clear self-directed technical building work.",
      "depth_opening": "Whether this technology-facing identity is already grounded in lived, self-directed practice or still exists primarily as aspiration - and if it is practiced, where and how that practice has happened.",
      "why_it_matters": "The answer changes how the applicant's entire technology-facing self-presentation should be understood.",
      "referenced_entity_ids": ["ESS-001", "ACT-002", "ACT-003", "ACT-004"],
      "supporting_det_signal_ids": [],
      "supporting_fragment_ids": ["ESS-001:F01", "ESS-001:F02"]
    }
  ],
  "themes": [
    {
      "theme_id": "THEME-001",
      "title": "Practiced Builder or Stated Direction",
      "unifying_axis": "The degree to which this applicant's relationship to technology is grounded in lived, self-directed practice versus existing primarily as a stated orientation.",
      "interview_direction": "Understanding whether and how this applicant has moved from stated interest into self-directed, lived technical work - and what that movement looks like from the inside.",
      "supporting_signal_ids": ["SIG-001"]
    }
  ]
}

The specific version could not have been written without reading this particular application.
The generic version could have been written about anyone who mentioned technology and did an internship.
Every signal and theme you produce must pass that test.
```

### Exact Call 1 user prompt template

```text
Analyze the following applicant projection and produce signals and themes.

AVAILABLE FRAGMENT IDs (use ONLY these in supporting_fragment_ids):
{valid_fragment_ids}

AVAILABLE ENTITY IDs (use ONLY these in referenced_entity_ids):
{valid_entity_ids}

{json.dumps(projection, indent=2)}

Apply the internal analysis framework silently, then return only valid JSON matching the output schema.
Produce the full signal set first (4-6 signals total), then derive 3 to 4 themes from it.
Ensure every signal is assigned to exactly one theme (HC-5) and every ID reference is valid (HC-2, HC-3, HC-4).

Every signal must name something specific to this applicant.
Every theme must name something specific to this applicant.
```

### Call 1 purpose in the app

This prompt's job is to create the app's interpretation layer.

It produces:

- `signals`
- `themes`

Those become:

- Page 4 Focus Areas
- annotation anchors for Page 2 and Page 3
- the source structure for Call 2

### Why the prompt is shaped this way

The app needs Call 1 output to be:

- applicant-specific
- grounded to known entity IDs
- grounded to known essay fragment IDs
- structurally linkable
- safe to validate and persist

That is why this prompt is much more strict than a normal analysis prompt.

---

## Exact Call 2 Prompt

Source:

- `app/agents/interview_generator.py`

Exact system prompt:

```text
You are preparing an interviewer who has never met this applicant but has read
their application file. Your job is to produce question groups that give the
interviewer access to the interior of what the application shows - not to audit
gaps, but to understand how things actually work for this specific person.

The themes and signals have already been defined for you. Do not invent, merge,
split, rename, or reinterpret them. Your job is to write exactly one question
group for each provided theme_id.

A signal is a line of understanding worth exploring. It may represent something
unresolved, something present but underdeveloped, or something already strong
whose internal structure is not yet visible. All three are equally valid as
sources of questions. Do not treat signals as gap reports.

A theme defines the territory and direction of a portion of the interview. It
is not a topic bucket. It carries a direction of understanding - what the
interviewer is fundamentally trying to access in this conversation. Every
question you write must serve that direction.

---

EVALUATIVE CONTEXT - what the interviewer is ultimately trying to assess:

The interviewer enters this conversation with three evaluative lenses. These do
not replace or override the themes and signals - question generation is still
driven by interview_direction and depth_opening. But as you build questions,
be aware that the interviewer is trying to gather evidence on:

  1. GRIT AND GROWTH - how the applicant responds to setbacks, difficulty, and
     the gap between where they are and where they want to be.
  2. PROBLEM SOLVING - how the applicant actually reasons through challenges,
     not just that they solved something.
  3. TECHNOLOGY ENGAGEMENT - whether the applicant's interest in technology is
     genuine and self-directed, or primarily stated.

Where a question naturally surfaces evidence on one of these dimensions without
compromising its specificity or its service to the theme, that is a stronger
question. Do not force this. A question that serves the theme well but does not
map neatly to one of these lenses is still correct. A question that maps to one
of these lenses but drifts from interview_direction is not.

---

YOUR INPUT:

You will receive a theme-first signal-evidence bundle.
Each theme entry contains:
- theme: the validated theme you must target
- signal_evidence_pairs: the validated signals and supporting evidence grouped under that theme

Each signal contains these fields:
- signal_id
- theme_id
- title
- evidence_anchor
- direct_read
- depth_opening: the specific thing an interviewer would want to understand more deeply -
  this may be an unresolved unknown, an underdeveloped area, or the internal structure
  of something already strong. Treat all three equally.
- why_it_matters

Each theme contains these fields:
- theme_id
- title
- unifying_axis: the single underlying idea that explains why these signals belong together.
  This is abstract and does not reference any signal - it characterizes something specific
  to this applicant.
- interview_direction: what the interviewer is trying to understand across these signals,
  stated as an actionable direction that stands independently of the signals.

The primary drivers of question generation are:
- interview_direction of the theme -> sets the direction and coherence frame for the group
- depth_opening of each signal -> provides the specific opening that makes questions non-generic
- evidence_anchor and direct_read -> ground every question in something particular to this applicant

The theme controls direction. The signals control specificity. Both constraints must be
satisfied simultaneously in every question you write.

---

HOW TO BUILD QUESTIONS - apply these steps silently in your head. Do not write any of this into your output:

For each provided theme, produce exactly one question_group using the same theme_id.
Each question_group must contain 3 to 4 questions.

STEP 1 - Read the theme's interview_direction first.
This is the direction the entire question group must serve. Every question you write
must advance understanding along this direction. If a question does not clearly serve
interview_direction, discard it regardless of how interesting it seems.

STEP 2 - Read each signal's depth_opening and evidence_anchor.
depth_opening is what an interviewer would want to understand more deeply. It is not
always a gap. It may be the internal structure of something strong, the grounding
behind something stated, or the lived reality behind something asserted.
evidence_anchor is what in the application makes it possible to ask a real question.
Every question must contain a specific referent drawn from the evidence_anchor or
direct_read - a named thing the applicant did, wrote, or chose. A question without
a specific referent from this application is not acceptable.

STEP 3 - Build the question group as a panorama, not a sequence.
Each question must enter the theme's territory from a genuinely different angle.
Different angle means: different entry point into the applicant's profile, or a
different dimension of what interview_direction is trying to reach. Questions that
probe the same thing from slightly different phrasings are redundant - discard one.

A well-formed group covers at least three of these four angles:
- GROUNDING: where in the applicant's life has this actually been practiced or lived,
  and what does that practice look like concretely?
- REASONING: what was the actual logic or thinking behind a specific choice, direction,
  or commitment this applicant made?
- CONNECTION: what is the relationship between two specific things in this applicant's
  profile - between what they wrote and what they did, or between two activities, or
  between an academic direction and a stated goal?
- DEPTH: for the signal most central to this theme, what does the depth_opening
  specifically require an interviewer to understand?

STEP 4 - Test every question before including it.

TEST 1 - SPECIFIC REFERENT
Does this question name a specific thing from this application - something the
applicant did, wrote, chose, or stated? If not, rewrite it.
Naming a field or general category ("your interest in technology") does not pass.
Naming something particular ("your essay's claim that X" or "your activity in Y") passes.

TEST 2 - UNANSWERABLE GENERICALLY
Can this question be answered well without the applicant accounting for the specific
referent named in it? If yes, the question is too open. Tighten it until a generic
answer would fail to address what the question is actually asking.

TEST 3 - SERVES INTERVIEW_DIRECTION
Does this question clearly advance understanding along the theme's interview_direction?
If it is interesting but tangential, cut it.

TEST 4 - NOT ELABORATION
Does this question ask the applicant to reason, account for, or connect something?
If it effectively asks them to tell or elaborate, rewrite it.

QUESTION TONE:
The implicit stance is structural curiosity - you have read this application carefully
and want to understand how things actually work for this person. Not skeptical. Not
validating. Genuinely curious about the interior of what is already present.
Do not frame questions as contradictions to resolve. Do not imply the interviewer
has found a problem. Do not open with hedging phrases that signal doubt.

PROHIBITED QUESTION FORMS:
- "Tell me about X"
- "Can you elaborate on X"
- "How did your interest in X develop over time"
- "Can you walk me through X"
- "What drew you to X" (invites origin story, not reasoning)
- Any question that names a general category rather than a specific thing from this application
- Any question framed as a contradiction or inconsistency to resolve
- Any question the applicant can answer well without engaging the specific referent named

---

CONTRAST EXAMPLE - understand what makes a question pass all four tests:

Signal context: applicant's essay presents computational thinking as central to their
identity and future direction. Activity profile shows math olympiad participation and
self-directed reading in algorithms. depth_opening: whether this computational identity
is grounded in self-directed practice - actual building or problem-solving outside
structured competition - or exists primarily as a stated orientation supported by
formal achievement.

Theme interview_direction: understanding whether this applicant's relationship to
computation is lived and self-directed, or primarily demonstrated through structured
achievement contexts.

WRONG question (fails TEST 1 and TEST 2):
"How has your interest in computing developed over time?"
-> No specific referent. Answerable by any applicant who mentioned computing.
-> Invites biography, not reasoning.

WRONG question (fails TEST 3 - interesting but drifts from interview_direction):
"What was the hardest problem you encountered in the math olympiad?"
-> Names something specific, but probes difficulty in competition - not whether
   practice is self-directed outside structured contexts.

RIGHT question (passes all four tests):
"Your essay frames computational thinking as the lens through which you approach
problems, but your activities outside school sit almost entirely within structured
competitions and reading - where outside those formats have you actually built or
created something, and what drove you to do it?"
-> Names specific referents: the essay's framing, the activity pattern.
-> Cannot be answered generically - requires accounting for the specific pattern named.
-> Directly serves interview_direction: self-directed vs. structured-context practice.
-> Forces reasoning, not elaboration.

---

PROHIBITED TERMS: Admit, Reject, Likelihood, Top candidate, Risk factor, Strength, Weakness, Outstanding, Exceptional, Excellent, Poor, Impressive, Concerning

CRITICAL: Do not include any key not defined in the OUTPUT SCHEMA below.
Your reasoning, planning, or question-testing process must remain entirely internal.
Do not create an "analysis", "reasoning", "thinking", or any other extra key.
Tokens spent on reasoning text in the output are wasted tokens that reduce the
number of question groups that can be generated.

---

OUTPUT SCHEMA - return exactly this structure, nothing else:

{
  "question_groups": [
    {
      "theme_id": "THEME-###",
      "group_title": "Short neutral label for the question group",
      "questions": [
        "Question 1 - specific, probing, names something from this application",
        "Question 2 - probes from a different angle",
        "Question 3 - directly targets the most important depth opening"
      ]
    }
  ]
}

Reuse the provided theme_id values exactly as given.
questions must be a flat array of plain strings only.
Produce exactly one question_group per provided theme.
Do not return a themes array.
```

### Exact Call 2 user prompt template

```text
Produce interview question groups for this applicant based on the
following theme-first signal-evidence bundle.

THEME SIGNAL-EVIDENCE BUNDLE:
{json.dumps(bundle, indent=2)}

ENTITY REFERENCE MAP:
{json.dumps(entity_id_map, indent=2)}

Apply your internal question-building framework silently. Return only valid JSON matching the output schema.
Produce exactly one question_group for every theme_id in the bundle, and no others.
```

### Call 2 purpose in the app

This prompt's job is to convert validated Page 4 interpretation into usable interview prompts for Page 5.

It produces:

- one question group per theme
- one flat list of questions per group

Those later become:

- Page 5 Questions in the final report
- generated questions in the interviewer workspace
- prompts that interviewers can edit, reorder, annotate, and use live

---

## Backend Story Around These Prompts

### Why Call 1 is strict

Call 1 is producing a structured intermediate representation the app depends on.

Its output is used for:

- final report Page 4 rendering
- Call 2 input construction
- Page 2 entity annotations
- Page 3 essay fragment annotations
- report chat retrieval context

Because of that, the app validates it aggressively.

### Why Call 2 is looser

Call 2 is producing interviewer-facing draft prompts.

Its output is still validated structurally, but the app mainly treats it as:

- editable generated content
- workspace seed content
- one interview-prep layer of the report

The app does not persist additional evidence links for the questions themselves.
It persists plain strings under each theme.

### What aborts generation

If Call 1 or Call 2 fails validation, `run_synthesis_pipeline()` aborts and returns no `ros_v1` report output.

Failure handling lives in:

- `app/agents/orchestrator.py`

Admin report generation and retry routes depend on this pipeline in:

- `app/api/admin.py`

---

## Frontend Use

### Final report rendering

The frontend treats these prompt outputs as report tabs:

- Page 4: Focus Areas
- Page 5: Questions

Relevant files:

- `frontend/components/ReviewPackageSection.tsx`
- `frontend/components/SynthesisReportSection.tsx`
- `frontend/components/ReviewPackagePages.tsx`
- `frontend/app/admin/applications/[id]/page.tsx`
- `frontend/app/interviewer/applications/[id]/page.tsx`

The frontend reads:

- `page_4_focus_areas.themes`
- `page_4_focus_areas.signals`
- `page_5_question_groups.question_groups`

### Workspace seeding

The interviewer workspace is seeded from the final report on the backend in:

- `app/interview_workspace.py`

That code maps:

- each Page 4 theme -> workspace theme card
- matching Page 5 question group -> generated questions under that theme

The frontend then works with the workspace shape defined in:

- `frontend/lib/types.ts`

Important frontend theme fields:

- `title`
- `unifying_axis`
- `interview_direction`
- `question_group_title`
- `questions`

Relevant frontend files:

- `frontend/components/interviewer/InterviewWorkspaceEditor.tsx`
- `frontend/components/interviewer/InterviewOverlayRunner.tsx`
- `frontend/components/interviewer/FinalInterviewReportSection.tsx`

### Report chat usage

Report chat explicitly knows about:

- `page4_focus_areas`
- `page5_question_groups`

It uses them as answerable report sections and cites them as sources.

Backend:

- `app/report_chat.py`

Frontend types:

- `frontend/lib/types.ts`
- `frontend/lib/reportChat.ts`

### Frontend role summary

In the frontend, these prompts ultimately power:

- the Page 4 Focus Areas tab
- the Page 5 Questions tab
- generated interviewer prep content
- live interview overlay question flow
- postgame/final-report context
- report chat explanations of themes and questions

---

## Practical Role Summary

### Call 1 role

Call 1 is the app's interpretation engine.

It turns extracted applicant evidence into:

- machine-validated interview signals
- grouped interview themes
- traceable annotation structure

### Call 2 role

Call 2 is the app's interview-action engine.

It turns validated interpretation into:

- grouped interview prompts
- editable interviewer workflow content

### Combined role

Together, these prompts are the bridge between:

- deterministic extraction
- human interview preparation

They are the LLM layer that turns extracted applicant data into:

- what matters
- why it matters
- what to ask next

---

## Key Files

- `app/agents/orchestrator.py`
- `app/agents/projection_builder.py`
- `app/agents/signal_interpreter.py`
- `app/policy/guard.py`
- `app/agents/bundle_constructor.py`
- `app/agents/interview_generator.py`
- `app/agents/report_annotations.py`
- `app/ros/assembler.py`
- `app/interview_workspace.py`
- `app/report_chat.py`
- `app/api/schemas.py`
- `app/api/admin.py`
- `frontend/lib/types.ts`
- `frontend/components/SynthesisReportSection.tsx`
- `frontend/components/ReviewPackageSection.tsx`
- `frontend/components/interviewer/InterviewWorkspaceEditor.tsx`
- `frontend/components/interviewer/InterviewOverlayRunner.tsx`

---

## Proposed Three-Call Redesign Spec

This section describes a concrete redesign that preserves as much of the current system as possible while separating:

- machine grounding
- interviewer-facing synthesis
- question generation

The core principle is:

- Call 1 is the truth layer
- Call 2 is the human layer
- Call 3 inherits from both

The interviewer should read only Call 2 and Call 3 outputs.
Call 1 should remain available in `signal_data` and other backend structures, but it should no longer be the primary Page 4 reading experience.

---

## Design Goals

### Goals

- Preserve entity and fragment linkages
- Preserve validation where it is load-bearing
- Preserve report chat grounding
- Preserve annotation/highlighting features
- Preserve workspace, overlay, and postgame flows as much as possible
- Make Page 4 human-readable
- Make Page 5 inherit human register instead of machine scaffolding

### Non-goals

- Rewriting the whole frontend
- Removing `signal_data`
- Replacing annotation logic
- Replacing deterministic extraction
- Deleting current backend truth structures

---

## Proposed Pipeline

### New Stage 1.7 shape

1. Deterministic extraction and canonical assembly
2. Call 1: Grounding Pass
3. Validate Call 1
4. Build humanization bundle
5. Call 2: Interviewer Synthesis
6. Validate Call 2 structurally
7. Build question-generation bundle from Call 1 + Call 2
8. Call 3: Question Generation
9. Validate Call 3 structurally
10. Assemble final report

### High-level rule

- Call 1 is internal and machine-facing
- Call 2 is the Page 4 interviewer-facing surface
- Call 3 is the Page 5 interviewer-facing surface

---

## Call 1 - Grounding Pass

### Purpose

Call 1 becomes the machine-readable substrate for:

- signal/theme IDs
- entity references
- essay fragment references
- deterministic signal references
- signal-to-theme linkage
- annotation and highlighting
- report chat grounding
- downstream synthesis bundles

### Audience

The audience is the backend system, not the interviewer.

### Prompt direction

The prompt should stop pretending it is writing for a human.
It should focus on:

- identifying grounded signals
- linking them to known evidence
- grouping them into themes
- preserving traceability

### What stays from current Call 1

Keep:

- `signal_id`
- `theme_id`
- `referenced_entity_ids`
- `supporting_det_signal_ids`
- `supporting_fragment_ids`
- signal-to-theme grouping logic
- theme IDs and signal IDs

Likely keep, but rewrite for machine use:

- concise signal label/title
- concise theme label/title

### What should leave Call 1

These fields currently exist mainly to communicate reasoning to humans or to a downstream prose-writing model:

- `why_it_matters`
- `depth_opening`
- `unifying_axis`
- `interview_direction`

If they are still needed downstream, they should not remain interviewer-facing in their current form.
The preferred direction is to remove them from Call 1 output entirely and let Call 2 and Call 3 do the communication work.

### Suggested Call 1 output shape

This is a conceptual shape, not final code:

```json
{
  "signals": [
    {
      "signal_id": "SIG-001",
      "title": "Short machine-friendly label",
      "summary": "Optional compact machine-readable observation",
      "referenced_entity_ids": ["ACA-001", "ESS-001"],
      "supporting_det_signal_ids": ["DET-001"],
      "supporting_fragment_ids": ["ESS-001:F01"]
    }
  ],
  "themes": [
    {
      "theme_id": "THEME-001",
      "title": "Short machine-friendly label",
      "supporting_signal_ids": ["SIG-001", "SIG-002"]
    }
  ]
}
```

### Validation

Call 1 keeps the strict validator.

This validator should still enforce:

- valid IDs
- valid linkage
- valid fragment IDs
- valid entity IDs
- complete signal coverage
- no duplicate or orphan structures

This remains the load-bearing validation layer.

---

## Call 2 - Interviewer Synthesis

### Purpose

Call 2 creates the actual Page 4 product the interviewer reads before the conversation.

It should answer, for each focus area:

- what is the real territory here
- what in this application makes it worth time
- what the interviewer is trying to understand

### Audience

A human interviewer with limited prep time.

### Register target

The prompt should explicitly target:

- a senior colleague who has read the file carefully
- speaking to another interviewer in plain language
- concise, scannable, natural prose

It should explicitly avoid:

- framework terminology
- validator language
- field-name leakage
- abstract analytical scaffolding

### Input

Call 2 should receive:

- validated Call 1 output
- entity-linked evidence summaries
- optional short excerpts or hooks from essays/activities/academics

It does not need raw deterministic extraction detail in full.
It needs enough grounding to write with specificity and confidence.

### Output

Call 2 should produce the Page 4 interviewer-facing surface.

### Recommended output object

This is the cleanest human-facing structure:

```json
{
  "focus_areas": [
    {
      "focus_area_id": "FA-001",
      "title": "Plain-language title",
      "what_this_is": "One or two sentences describing the real territory in normal language.",
      "why_now": "One sentence on what in this application makes it worth time.",
      "interview_goal": "One sentence on what the interviewer is trying to learn.",
      "source_theme_ids": ["THEME-001", "THEME-002"],
      "source_signal_ids": ["SIG-001", "SIG-003"]
    }
  ]
}
```

### Important schema decision

Call 2 should be allowed to consolidate machine themes into fewer human focus areas if needed.

This means:

- Call 1 may produce more machine themes
- Call 2 may compress them into 2-3 focus areas for readability

That is likely better for product quality than a forced one-to-one mapping.

### Traceability requirement

Even if Call 2 consolidates themes, it should retain:

- `source_theme_ids`
- `source_signal_ids`

This is what preserves downstream grounding and lets the system still know where a human-facing focus area came from.

### Validation

Call 2 validation should be lighter than Call 1.

It should likely enforce:

- valid JSON
- non-empty `focus_areas`
- required fields present
- valid `source_theme_ids`
- valid `source_signal_ids`
- complete coverage rules if you want every source theme represented

It should not try to judge prose quality beyond simple structure and safety.

---

## Call 3 - Question Generation

### Purpose

Call 3 produces Page 5 interview questions.

Its job is to inherit:

- the human voice and framing from Call 2
- the factual specificity and evidence grounding from Call 1

### Audience

A human interviewer using question groups in prep, live interview, and workspace flows.

### Input

Call 3 should receive both:

1. Call 2 focus areas
   - primary source of voice, framing, interviewer intent
2. Call 1 grounded structure
   - primary source of specificity, evidence, and references

### Why both are needed

If Call 3 reads only Call 1:

- it inherits the current machine-analytic register

If Call 3 reads only Call 2:

- it risks losing precision and specificity

So Call 3 should be designed to:

- sound like the writer of Call 2
- stay grounded like Call 1

### Output

Call 3 can keep almost the same Page 5 output shape the app uses today:

```json
{
  "question_groups": [
    {
      "focus_area_id": "FA-001",
      "group_title": "Short scannable label",
      "questions": [
        "Question 1",
        "Question 2",
        "Question 3"
      ],
      "source_theme_ids": ["THEME-001", "THEME-002"],
      "source_signal_ids": ["SIG-001", "SIG-003"]
    }
  ]
}
```

If the current frontend strongly expects `theme_id`, you can preserve compatibility by using:

- `theme_id` as the interviewer-facing focus-area identifier

or by:

- keeping a separate focus-area ID and adapting workspace seeding in the backend

### Validation

Call 3 validation should preserve the current structural checks:

- exactly one group per focus area
- no duplicates
- non-empty group title
- non-empty question strings

It can later grow to enforce stronger heuristics, but structural validation is enough for migration.

---

## Report Schema Recommendation

To minimize disruption, keep `signal_data` and separate it clearly from interviewer-facing Page 4 and Page 5 content.

### Recommended final report structure

```json
{
  "page_4_focus_areas": {
    "focus_areas": [
      {
        "focus_area_id": "FA-001",
        "title": "Plain-language title",
        "what_this_is": "Human-facing territory summary",
        "why_now": "Why this is worth time in this file",
        "interview_goal": "What the interviewer is trying to learn",
        "source_theme_ids": ["THEME-001"],
        "source_signal_ids": ["SIG-001", "SIG-002"]
      }
    ]
  },
  "page_5_question_groups": {
    "question_groups": [
      {
        "focus_area_id": "FA-001",
        "group_title": "Question group label",
        "questions": ["...", "...", "..."],
        "source_theme_ids": ["THEME-001"],
        "source_signal_ids": ["SIG-001", "SIG-002"]
      }
    ]
  },
  "signal_data": {
    "deterministic_signals": [],
    "signals": [],
    "themes": [],
    "annotations": {}
  }
}
```

### Why this is the cleanest split

- `page_4_focus_areas` becomes interviewer-facing
- `page_5_question_groups` becomes interviewer-facing
- `signal_data` remains backend truth and support structure

This preserves the product distinction clearly.

---

## Backend Changes Needed

### Orchestration

Most of the real work should happen in backend orchestration.

Primary file:

- `app/agents/orchestrator.py`

Changes:

- add Call 2 interviewer-synthesis stage
- add Call 3 question-generation stage
- build new intermediate bundles
- preserve Call 1 validation
- add Call 2 validation
- adapt Call 3 validation from the current question-group validator

### New prompt builders

Likely new files:

- `app/agents/interviewer_synthesizer.py`
- `app/agents/question_generator_v2.py`

Or equivalent names.

### New validators

Likely additions:

- `validate_focus_areas(...)`
- updated `validate_question_groups(...)` for Call 3 inputs

### Bundles

Likely new bundle builders:

- `construct_interviewer_synthesis_bundle(...)`
- `construct_question_generation_bundle(...)`

### Assembly

`assemble_ros_v1()` should stop placing raw Call 1 themes/signals directly into Page 4.

Instead:

- Page 4 should receive Call 2 focus areas
- Page 5 should receive Call 3 question groups
- raw Call 1 output should live in `signal_data`

---

## Frontend Impact

The goal is to keep frontend impact real but contained.

### What should stay broadly the same

- Page 4 tab still exists
- Page 5 tab still exists
- workspace still groups questions under top-level interview territories
- overlay still runs over workspace questions
- postgame still works over workspace questions and summaries
- report chat still points to Page 4 and Page 5

### What changes

The main frontend change is not a new workflow.
It is a different data contract for what Page 4 is.

Likely changes:

- Page 4 components stop reading raw `themes`/`signals` as the primary display object
- components render `focus_areas` instead
- pre-interview workspace surfaces may remove or demote `unifying_axis` and `interview_direction`
- labels/headings become more human-facing
- workspace seeding may map focus areas instead of raw themes

### Minimal frontend principle

Do not redesign the workflow.
Only change which backend fields are treated as the interviewer-facing source of truth.

---

## Workspace And Overlay Migration Strategy

### Workspace

The current workspace theme model can likely survive with small changes if a focus area is treated as the new “theme card.”

Current workspace fields:

- `title`
- `unifying_axis`
- `interview_direction`
- `question_group_title`
- `questions`

Recommended migration:

- `title` becomes focus area title
- `unifying_axis` can be removed or left empty
- `interview_direction` can be replaced by `interview_goal`
- `question_group_title` stays
- `questions` stay

This means a lot of frontend work may indeed be removal or renaming rather than reinvention.

### Overlay

The overlay should not need conceptual redesign if workspace content shape remains close enough.

It should continue to operate on:

- grouped question sets
- question statuses
- notes and follow-ups

### Postgame and final report

These should also remain largely intact if the workspace content contract stays stable enough.

---

## Report Chat And Annotation Compatibility

### Report chat

Report chat should continue to have access to:

- Page 4 interviewer-facing focus areas
- Page 5 interviewer-facing question groups
- `signal_data` for deeper grounding

That means the chatbot does not lose power.
It gains a better human-facing surface while still having access to the machine layer underneath.

### Annotations and highlighting

These should remain based on Call 1 `signal_data`.

That means:

- no need to rebuild annotation logic
- no need to rebuild entity/fragment references
- no need to teach the frontend how to derive annotations from human prose

This is one of the biggest reasons to keep Call 1 as internal truth.

---

## Recommended Migration Phases

### Phase 1 - Introduce the new three-call backend

- keep current Call 1 grounding and validation
- add Call 2 interviewer synthesis
- add Call 3 question generation
- preserve `signal_data`
- assemble new Page 4 and Page 5 structures

### Phase 2 - Adapt backend consumers

- workspace seeding uses focus areas instead of raw themes
- report chat reads new Page 4 structure first
- preserve fallback access to `signal_data`

### Phase 3 - Adapt frontend rendering

- Page 4 renders human focus areas
- Page 5 renders question groups from Call 3
- remove direct display of machine-scaffold fields where no longer needed

### Phase 4 - Cleanup

- remove obsolete frontend dependence on raw Call 1 display fields
- keep raw Call 1 only where it is actually load-bearing

---

## Final Recommendation

This is the recommended target architecture:

- Call 1:
  internal grounding only
- Call 2:
  interviewer-facing Page 4 synthesis
- Call 3:
  interviewer-facing Page 5 question generation, grounded by Call 1 and voiced by Call 2

And the most important product boundary should be:

- humans read Page 4 and Page 5
- machines rely on `signal_data`

That is the cleanest way to preserve the backend truth layer while fixing the user-facing experience.
