import json

from app.llm.client import generate


def build_interview_messages(bundle: dict, entity_id_map: list) -> list[dict]:
    """
    Builds the Stage 1.7 Call 2 prompt messages.
    Instructs the LLM to generate interview question groups grounded
    in pre-defined themes and validated signals.
    """

    prohibited_terms = [
        "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor",
        "Strength", "Weakness", "Outstanding", "Exceptional", "Excellent",
        "Poor", "Impressive", "Concerning"
    ]

    system_prompt = """
You are preparing an interviewer who has never met this applicant but has read
their application file. Your job is to produce question groups that will help
the interviewer have a genuinely revealing conversation.

The interviewer has three specific goals for this interview:
  1. GRIT AND GROWTH - understanding how the applicant responds to setbacks,
     difficulty, and the gap between where they are and where they want to be.
  2. PROBLEM SOLVING - understanding how the applicant actually reasons through
     challenges, not just that they solved something.
  3. TECHNOLOGY ENGAGEMENT - understanding whether the applicant's interest in
     technology is genuine and self-directed, or primarily stated.

The themes have already been defined for you. Do not invent, merge, split,
rename, or reinterpret them. Your job is to write exactly one question group
for each provided theme_id.

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
- what_remains_open
- why_it_matters

Each theme contains these fields:
- theme_id
- title
- framing
- what_this_theme_must_resolve

The most important inputs are:
- what_remains_open: the unresolved thing the application cannot answer by itself
- why_it_matters: why that unresolved point would materially change understanding
- what_this_theme_must_resolve: the coherence frame for the whole question group

---

HOW TO BUILD QUESTIONS:

For each provided theme, produce exactly one question_group using the same
theme_id. Each question_group must contain 3 to 4 questions. At least one
question must directly address the what_remains_open of a signal in that theme.
The others should probe the same territory from different angles while staying
coherent with what_this_theme_must_resolve.

A question is only acceptable if it meets both of these tests:
  TEST 1 - Could this question only be asked about this specific applicant?
           If the same question could be asked of any applicant in this field,
           it fails. Rewrite it to name something specific.
  TEST 2 - Does this question probe reasoning or motivation rather than asking
           for elaboration? Questions of the form "tell me more about X" or
           "can you elaborate on X" fail. Questions that ask why a specific
           choice was made, how the applicant thought through a specific
           situation, or what the relationship is between two specific things
           they did pass.

PROHIBITED QUESTION FORMS:
- "Tell me about X"
- "Can you elaborate on X"
- "How did your interest in X develop over time"
- "Can you walk me through X"
- Any question that does not name something specific from this application

---

CONTRAST EXAMPLE - understand the difference:

Signal context: applicant's essay emphasizes excitement about solving real-world
problems through technology, but activity profile shows piano, yoga, olympiads,
and reading - no tech projects or internships.
What remains open: whether the applicant's technology-facing identity is already
grounded in self-directed technical practice or is still primarily aspirational.

WRONG question:
"How has your interest in technology developed over time?"

RIGHT question:
"Your essay describes excitement about designing solutions that create meaningful
impact, but your activities outside school are piano, yoga, and reading - where
in your life have you actually built or created something technical, even
informally, and what happened?"

The right question could not have been asked without reading this specific
application. It names the specific tension. It does not ask for elaboration -
it forces the applicant to account for a gap.

---

PROHIBITED TERMS: """ + ", ".join(prohibited_terms) + """

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
        "Question 3 - directly targets what remains open"
      ]
    }
  ]
}

Reuse the provided theme_id values exactly as given.
questions must be a flat array of plain strings only.
Produce exactly one question_group per provided theme.
Do not return a themes array.
"""

    user_prompt = f"""
Produce interview question groups for this applicant based on the
following theme-first signal-evidence bundle.

THEME SIGNAL-EVIDENCE BUNDLE:
{json.dumps(bundle, indent=2)}

ENTITY REFERENCE MAP:
{json.dumps(entity_id_map, indent=2)}

Before writing any question, re-read the what_remains_open field of each signal
and the what_this_theme_must_resolve field of each theme.
Those are the core of what the interviewer needs to understand.
Every question must pass both tests: specific to this applicant, and probing
reasoning rather than requesting elaboration.
Return exactly valid JSON matching the output schema.
Before returning, check that you produced exactly one question_group for every
theme_id supplied in the bundle, and no others.
If any question could be asked of any applicant, rewrite it to name something
specific from this bundle.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def generate_interview(bundle: dict, entity_id_map: list) -> str:
    """
    Agent 16: Interview generator (LLM Call 2).
    Makes exactly one LLM call to produce interview question groups.
    Returns the raw response text.
    """
    messages = build_interview_messages(bundle, entity_id_map)
    response_text = generate(messages, call_label="call_2")
    return response_text
