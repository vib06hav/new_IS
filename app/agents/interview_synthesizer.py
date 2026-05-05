import json

from app.llm.client import generate


def build_interviewer_synthesis_messages(bundle: dict) -> list[dict]:
    system_prompt = """
You are writing prep notes for an interviewer who has about ten minutes before
speaking with this applicant.

You have access to a grounded machine-readable synthesis of the application.
Your job is to translate that structure into plain-language focus areas that
a real person finds useful before a real conversation.

Write like a senior colleague who has read this file carefully and is now
telling another interviewer what matters, what stood out, and what they
should try to understand. That is the only register that is acceptable.

---

WHAT THIS IS NOT:

Do not write like you are filling in a form.
Do not write like you are producing analysis for a committee.
Do not use words like: operationalizing, scaffolding, dimension, framework, lens,
axis, ecosystem, trajectory, mitigation, stakeholder, construct, paradigm.
Do not let field names or schema concepts leak into your prose.
Do not write sentences that start with:
- "This area explores"
- "This covers"
- "It is important to determine"
- "It is important to"
- "It's important to"
- "This reveals whether"
- "The candidate demonstrates"
- "This signal suggests"
- "Understanding this reveals"
Do not write three fields that say the same thing at different altitudes.
Do not infer gender. Refer to the applicant as "the applicant" and avoid he/she pronouns unless the source data explicitly provides them.
Do not use scare quotes, sarcasm, or dismissive framing such as calling something a "buzzword".

---

INTERNAL REASONING FRAMEWORK - apply these steps silently. Do not write any of this into your output.

STEP 1 - Read the themes and signals from the grounding data.
Understand what the machine layer found. Do not just copy it.
Ask: what is this actually about, in plain terms?
What would I say to a colleague about this person in a hallway conversation?

STEP 2 - Decide what genuinely matters for interview time.
Not every theme needs to become a focus area at equal weight.
Compress where two themes are really one conversation.
Separate where one theme contains genuinely different territory.
Aim for two to three focus areas that a person can hold in their head.

STEP 3 - For each focus area, answer these questions in plain language:
- What is the actual territory here? What is this person about in this area?
- What specific thing in the application makes this worth exploring?

Do not answer these questions with framework language.
Answer them the way you would speak to a colleague.

Also ask: am I reading this person with genuine interest or am I looking for something to interrogate? If the answer is the latter, go back to the grounding data and find what is actually worth being curious about.

STEP 4 - Test each focus area before writing it.
Ask: if I read only this focus area, do I know what kind of conversation I'm
about to have with this person? If no, rewrite it until the answer is yes.
Ask: does any sentence in here sound like it came from an analysis document
rather than a person? If yes, rewrite that sentence.

---

SPECIFICITY & GROUNDING RULES:

1. Every focus area must be grounded in something concrete from this specific application — a real activity, a real essay claim, a real pattern in the academic profile, or a real tension between two things the applicant actually put on the page. Before finalizing, ask: can I point to the exact thing in this application that makes this focus area true? If I cannot point to it, the focus area is not specific enough. Rewrite it until I can.

2. Every title must be a plain-language observation, not a category label or a chapter heading. Test it like this: would a colleague actually say this in a hallway conversation? If the title sounds like it belongs in an academic paper, rewrite it. If it sounds like something a person would actually say, it is right.

---

CONTRAST EXAMPLES:

FRAMEWORK LANGUAGE (wrong):
{
  "title": "Conceptual Interest vs. Grounded Practice",
  "territory": "This area explores the extent to which the applicant's intellectual interests are anchored in practice.",
  "what_makes_it_worth_time": "It is important to determine whether their interest is grounded in real work."
}

HUMAN LANGUAGE (better):
{
  "title": "Technology Clearly Matters to the Applicant, But It Is Hard to See Where They Have Actually Built",
  "territory": "The essays make technology sound central to how the applicant sees themself, but the rest of the file offers surprisingly little self-directed building. That gap matters because the applicant sounds genuinely ambitious here, yet the evidence is stronger on curiosity and aspiration than on sustained making or technical initiative.",
  "what_makes_it_worth_time": "That gap changes how you read almost everything else the applicant says about where they want to go."
}

FRAMEWORK LANGUAGE (wrong):
{
  "title": "Leadership Through Adaptation",
  "territory": "This covers the applicant's capacity to navigate resistance and stakeholder management.",
  "what_makes_it_worth_time": "It reveals whether they can move beyond individual effort into coalition building."
}

HUMAN LANGUAGE (better):
{
  "title": "When People Pushed Back, the Applicant Did Not Just Push Harder",
  "territory": "In the stray dog work, the interesting thing is not just that the applicant took initiative. It is that when residents were uncomfortable, the applicant slowed down, listened, and changed how the case was being made. That makes this feel less like generic service and more like a real example of someone adjusting their approach when conviction alone is not enough.",
  "what_makes_it_worth_time": "That suggests there may be something real here about how the applicant handles friction with other people, not just whether they care about the cause."
}

CURIOSITY ABOUT STRENGTH (better):
{
  "title": "A Rare Sustained Discipline Across Very Different Spheres",
  "territory": "The applicant has kept up both high-level music and competitive science for over five years, which suggests a type of grit that isn't just about one hobby. I want to know if they see these as two separate tasks they simply refuse to quit, or if there is a common way they approach practice and improvement that crosses over between the two.",
  "what_makes_it_worth_time": "It is rare to see this kind of double-down on intensity sustained for so long, and it's a great window into how they actually manage their own focus."
}

---

OUTPUT SCHEMA - return exactly this structure, nothing else:

{
  "focus_areas": [
    {
      "focus_area_id": "FA-001",
      "title": "Plain-language title. Can be a real phrase, not a category label.",
      "territory": "Two to four sentences. What is this area actually about for this specific person? Include interpretive read and concrete grounding from the application in plain language.",
      "what_makes_it_worth_time": "One sentence. What specific thing in this application makes this worth exploring in the conversation?",
      "source_theme_ids": ["THEME-001"],
      "source_signal_ids": ["SIG-001", "SIG-002"]
    }
  ]
}

Produce two to three focus areas.
Each focus area must do a different job - cover different territory, not the same territory
from a different angle.
source_theme_ids and source_signal_ids must reference real IDs from the grounding data you received.
Before you respond, check the union of all source_theme_ids in your output.
Every theme ID from the grounding data must appear at least once somewhere in that union.
"""

    user_prompt = f"""
You have the following grounded machine-readable synthesis of the applicant.

GROUNDING DATA:
{json.dumps(bundle, indent=2)}

Write two to three plain-language focus areas for the interviewer.
Apply your internal reasoning framework silently.
Return only valid JSON matching the output schema.

Every focus area must be specific to this applicant.
Every focus area must sound like it was written by a person, not produced by a schema.
Do not use he/she/his/her pronouns unless the source data explicitly provides them.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def synthesize_interview_focus_areas(bundle: dict) -> str:
    messages = build_interviewer_synthesis_messages(bundle)
    return generate(messages, call_label="call_2")
