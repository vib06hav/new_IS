import json

from app.llm.client import generate


def build_signal_interpreter_messages(projection: dict) -> list[dict]:
    """
    Builds the Stage 1.8 Call 1 prompt messages.
    Call 1 is machine infrastructure only: grounded signals, themes, and ID linkages.
    """

    prohibited_terms = [
        "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor",
    ]

    system_prompt = """
You are producing a machine-readable grounding representation for an interview synthesis pipeline.

This output is infrastructure. It will not be read by a human. Do not write for a human reader.
Do not write explanatory prose. Do not write evaluatively. Do not draft questions.
Your only job is to identify grounded signals, group them into themes, and link every claim
to the evidence IDs it came from.

---

INTERNAL ANALYSIS FRAMEWORK - apply these steps silently. Do not write any of this into your output.

You are preparing to help someone have a good conversation with this applicant. That is the only job. Read everything that follows in that spirit.

STEP 1 - Read the essays carefully.
Map what this applicant has actually put on the page about their identity, motivation,
and direction. Note the specific language they use. Note what they chose to emphasize.
Note what they claim to care about.
Do not evaluate anything yet. Your only job at this step is to understand what is present.

STEP 2 - Read the activity profile and academic profile.
The academic profile contains interview-relevant academics from 10TH, 11TH, and 12TH,
including later-year subject detail.
For each thing you notice, ask: if I were genuinely curious about this person — not evaluating them, just trying to understand them — what would I want to know more about? That question applies equally to something strong, something underdeveloped, and something that raises a direction without resolving it.

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
A signal is one specific line of understanding worth exploring in an interview.
It must be grounded in something particular to this applicant.

A valid signal captures one of these three states:
1. Something already strong or notable — a clear achievement, a sustained commitment, a confident self-description — whose internal structure, lived grounding, or connection to the rest of this person's profile is worth understanding more deeply. This is not a gap. It is an invitation to go further into something real.
2. Something whose grounding or depth cannot be concluded from the application alone.
3. Something present but not sufficiently demonstrated - a strong self-description with limited visible practice, a clear direction with no visible process.

State 1 is the primary mode. Signals are not only about what is missing.

For each signal, identify:
- a short label that names something specific to this applicant
- what is specifically present or specifically absent in the application that creates this opening
- the specific thing an interviewer would want to understand more deeply
- which entity IDs, deterministic signal IDs, and fragment IDs ground it

Each signal must be one idea. If it splits into two independent directions, choose
the stronger one or separate them.

STEP 5 - Derive themes.
A theme title should name something you are curious about in this person, not a dimension you are measuring them on. If the title sounds like an analytical category, rewrite it until it sounds like something a thoughtful person would say they wanted to understand better.

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
If a gate is not satisfied, rewrite until it is, then continue.

GATE 1 - Signal exclusivity.
For each signal assigned to this theme: would placing it under a different theme
require rewriting the signal itself?
If yes - it belongs here. If no - redraw the boundary or sharpen the signal.

GATE 2 - Theme independence.
Across all themes: can any two themes be merged without losing anything material?
If no - they are independent. If yes - merge or reframe.

GATE 3 - Coverage.
Does every signal have exactly one theme home?
If no - assign unthemed signals or redraw boundaries until every signal is covered.

---

RULES:

1. Every signal must be grounded in specific content from this application.
   Reference actual things the applicant wrote, specific activities they listed,
   specific scores or patterns. Never write a signal that could apply to any applicant.

2. Cross-section signals are the most valuable kind. Prioritize them.
   A signal that connects the essay to the activity profile is worth more than
   a signal that describes one section in isolation.

3. Produce between 4 and 6 signals. Fewer sharp signals are better than many generic ones.

4. Themes must be applicant-specific. Do not use generic labels like "Academic Performance"
   or "Leadership."

5. Before finalizing each signal, test:
   "Could this signal be written about 100 applicants with similar profiles?"
   If yes, discard or rewrite it.

6. PROHIBITED: Do not imply an admissions decision.
   Do not use: """ + ", ".join(prohibited_terms) + """

7. CRITICAL: Do not include any key not defined in the OUTPUT SCHEMA below.
   Do not create an "analysis", "reasoning", "thinking", or any other extra key.

---

HARD CONSTRAINTS - strictly enforced by a validator after you respond:

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
      "title": "Short label. Must name something specific to this applicant.",
      "core_observation": "One sentence. What is specifically present or specifically absent in this application that creates this opening. No interpretation.",
      "interview_opening": "One sentence. The specific thing worth understanding more deeply - whether an unresolved unknown, something underdeveloped, or the internal structure of something already strong.",
      "referenced_entity_ids": ["Entity IDs from the projection that support this signal"],
      "supporting_det_signal_ids": ["DET signal IDs that sharpen this signal - empty if purely cross-section"],
      "supporting_fragment_ids": ["Essay fragment IDs - empty if not essay-derived"]
    }
  ],
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "Short label. Must name something specific to this applicant.",
      "supporting_signal_ids": ["SIG-001", "SIG-003"]
    }
  ]
}

Signal IDs numbered sequentially from SIG-001.
Theme IDs numbered sequentially from THEME-001.
Each theme must be supported by at least one signal.
Before responding, check three things:
1. Every signal_id is unique and sequential with no duplicates or gaps.
2. Every theme_id is unique and sequential with no duplicates or gaps.
3. Every theme has at least one supporting_signal_id and every signal appears in exactly one theme.
"""

    valid_fragment_ids = [f["fragment_id"] for f in projection.get("essay_fragments", []) if f.get("fragment_id")]
    valid_entity_ids = [e["entity_id"] for e in projection.get("entity_id_map", []) if e.get("entity_id")]

    user_prompt = f"""Analyze the following applicant projection and produce signals and themes.

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
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def interpret_signals(projection: dict) -> str:
    messages = build_signal_interpreter_messages(projection)
    response_text = generate(messages, call_label="call_1")
    return response_text
