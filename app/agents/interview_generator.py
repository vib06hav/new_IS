import json
from app.llm.client import generate


def build_interview_messages(bundle: dict, entity_id_map: list) -> list[dict]:
    """
    Builds the Stage 1.7 Call 2 prompt messages.
    Instructs the LLM to generate interview themes and questions grounded
    in validated signals, using interview_hook fields as primary targeting.
    """

    prohibited_terms = [
        "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor",
        "Strength", "Weakness", "Outstanding", "Exceptional", "Excellent",
        "Poor", "Impressive", "Concerning"
    ]

    system_prompt = """
You are preparing an interviewer who has never met this applicant but has read
their application file. Your job is to produce interview themes and question
groups that will help the interviewer have a genuinely revealing conversation.

The interviewer has three specific goals for this interview:
  1. GRIT AND GROWTH — understanding how the applicant responds to setbacks,
     difficulty, and the gap between where they are and where they want to be.
  2. PROBLEM SOLVING — understanding how the applicant actually reasons through
     challenges, not just that they solved something.
  3. TECHNOLOGY ENGAGEMENT — understanding whether the applicant's interest in
     technology is genuine and self-directed, or primarily stated.

Every theme you produce must serve at least one of these three goals.
Every question group must contain at least one question that directly probes
the relevant goal through the specific evidence in the bundle.

---

YOUR INPUT:

You will receive a signal-evidence bundle. Each entry in signal_evidence_pairs
contains a signal and its supporting evidence.

The signal contains these fields:
- title: the name of the pattern or tension identified
- essay_claim: what the applicant claimed or implied in their essay
- evidence_observation: what the activity or academic data actually shows
- tension_or_coherence: whether these align or conflict, and how
- interview_hook: the specific line of inquiry an interviewer needs to pursue

The interview_hook is the most important field. It tells you exactly what the
interviewer needs to understand that the application cannot answer by itself.
Your questions must address the interview_hook directly and specifically.

---

HOW TO BUILD THEMES:

Do not create one theme per signal mechanically. Read all signals together and
group them by which interviewer goal they serve. Signals that both relate to
the applicant's academic response to challenge should become one theme, not two.
Aim for 3 to 4 themes that each represent a meaningful interview territory.

Each theme must:
- Have a title that names something specific to this applicant, not a generic
  category. "Academic Resilience Amid Board Transition" is specific.
  "Academic Performance" is not.
- Have a description that explains what the interviewer is trying to understand
  about this person, not just what the evidence shows.
- Reference the entity IDs of the evidence that supports it.

---

HOW TO BUILD QUESTIONS:

For each theme, produce 3 to 4 questions. At least one must directly address
the interview_hook of the signal that drove the theme. The others should probe
the same territory from different angles.

A question is only acceptable if it meets both of these tests:
  TEST 1 — Could this question only be asked about this specific applicant?
           If the same question could be asked of any applicant in this field,
           it fails. Rewrite it to name something specific.
  TEST 2 — Does this question probe reasoning or motivation rather than asking
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

CONTRAST EXAMPLE — understand the difference:

Signal context: applicant's essay emphasizes excitement about solving real-world
problems through technology, but activity profile shows piano, yoga, olympiads,
and reading — no tech projects or internships.
Interview hook: what concrete steps has the applicant taken to build or create
technology beyond coursework, and how do they plan to close the gap between
stated ambition and demonstrated technical work.

WRONG question:
"How has your interest in technology developed over time?"

RIGHT question:
"Your essay describes excitement about designing solutions that create meaningful
impact, but your activities outside school are piano, yoga, and reading — where
in your life have you actually built or created something technical, even
informally, and what happened?"

The right question could not have been asked without reading this specific
application. It names the specific tension. It does not ask for elaboration —
it forces the applicant to account for a gap.

---

PROHIBITED TERMS: """ + ", ".join(prohibited_terms) + """

---

OUTPUT SCHEMA — return exactly this structure, nothing else:

{
  "themes": [
    {
      "theme_id": "THEME-###",
      "title": "Specific label naming something particular to this applicant",
      "description": "What the interviewer is trying to understand about this person through this theme",
      "referenced_entity_ids": ["Entity IDs that support this theme"]
    }
  ],
  "question_groups": [
    {
      "theme_id": "THEME-###",
      "group_title": "Short neutral label for the question group",
      "questions": [
        "Question 1 — specific, probing, names something from this application",
        "Question 2 — probes from a different angle",
        "Question 3 — addresses the interview_hook directly"
      ]
    }
  ]
}

Theme IDs numbered sequentially from THEME-001.
Every question_group must reference a theme_id defined in themes.
questions must be a flat array of plain strings only.
Produce one question_group per theme.
"""

    user_prompt = f"""
Produce interview themes and question groups for this applicant based on the
following signal-evidence bundle.

SIGNAL-EVIDENCE BUNDLE:
{json.dumps(bundle, indent=2)}

ENTITY REFERENCE MAP:
{json.dumps(entity_id_map, indent=2)}

Before writing any question, re-read the interview_hook field of each signal.
That is the core of what the interviewer needs to understand.
Every theme must serve at least one of the three interviewer goals:
grit and growth, problem solving, or technology engagement.
Every question must pass both tests: specific to this applicant, and probing
reasoning rather than requesting elaboration.

Return exactly valid JSON matching the output schema.
Before returning, check each question against the two tests.
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
    Makes exactly one LLM call to produce interview themes and questions.
    Returns the raw response text.
    """
    messages = build_interview_messages(bundle, entity_id_map)
    response_text = generate(messages, call_label="call_2")
    return response_text