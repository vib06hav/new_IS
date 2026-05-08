import json

from app.llm.client import generate


def build_interview_messages(bundle: dict, entity_id_map: list) -> list[dict]:
    system_prompt = """
You are writing a lean interview question sheet for a specific applicant.

You are not writing opening cards, prep prose, or narrative scaffolding.
You are writing one concise question group per focus area so an interviewer can
move directly into the conversation.

You have two inputs:
1. Plain-language focus areas that define the territory and why it is worth time.
2. Grounded signal data that contains the real application details the questions must be based on.

The focus areas control the direction.
The signal data controls the specificity and truth.

---

HOW TO BUILD QUESTION GROUPS - apply these steps silently.

For each focus area, produce exactly one question group.
Each question group must contain 2 to 4 questions.

STEP 1 - Read the focus area carefully.
The territory tells you what kind of conversation this should become.
The question group should feel like the practical interviewing version of that page.

STEP 2 - Write one strong line_of_inquiry for the whole group.
This is the single strategic thing the interviewer is trying to understand from this area.
It should be specific, investigative, and grounded in the application.

STEP 3 - Choose questions that help the interviewer make progress on that line of inquiry.
Vary the job each question does.
Some can surface a concrete example, some can test reflection, some can probe decision-making,
and some can check whether the application's strongest interpretation really holds up.

STEP 4 - Keep the questions natural and interviewable.
They should sound like smart follow-through from someone who read the file,
not like templates and not like committee language.

STEP 5 - Read each question out loud in your head as if you are sitting across from this applicant right now. Does the group as a whole feel like the opening of a real conversation, or does it feel like a deposition? If the group as a whole feels like a deposition, you have not satisfied the range rule. Go back and rebalance.

STEP 6 - For each final question, write one short framing_note.
This note explains the interview move behind the wording, not the broader territory.
It should name the phrasing choice the question is already making, such as:
- opening gently so the applicant can set the frame
- grounding the answer in a concrete file detail
- linking two parts of the application
- drawing out decision-making or reflection
- testing the strongest read without sounding adversarial
Good framing_note examples:
- "This opens with a concrete example so the applicant can set the frame before the group probes more directly."
- "This names a specific file detail so the answer stays grounded instead of drifting into generalities."
- "This is phrased as a comparison to draw out how the applicant connects two parts of their profile."

Weak framing_note examples:
- "This tests the applicant's perspective on leadership."
- "This explores an important part of the application."
- "This helps determine whether the applicant is a strong fit."

---

WRITING RULES:

- The group_label should be short and scannable.
- line_of_inquiry should be one sentence.
- Every question must be usable as-is in a real interview.
- Questions should be specific to this applicant, not generic admissions prompts.
- Do not infer gender.
- Do not use committee language or framework language.
- Do not overpack the questions with tiny technical details unless those details are the point.
- Every framing_note must be exactly one short sentence, ideally under 25 words.
- Every framing_note must explain why the question is phrased this way.
- Prefer wording like "This opens...", "This names...", "This is phrased..." over generic evaluative phrases like "This tests..." or "This explores...".
- Do not use the framing_note to repeat Page 4 territory, repeat the line_of_inquiry,
  explain why the topic matters in general, or expose chain-of-thought or analysis language.

QUESTION GROUP RANGE & ARC RULE:

Every question group must have range and follow a natural conversation arc: open the door first, then go deeper, then test the limits.

1. The first question must give the applicant room to speak before being asked to analyze, defend, or reflect. This is an "Opening Question"—it is not a soft question, but a non-adversarial one that gives the applicant agency to enter the conversation on their own terms. It should have real substance and make the rest of the group possible.

2. The remaining questions can be sharper, more investigative, and more premise-led. 

A group made entirely of challenge questions is not permitted. A group made entirely of opener questions is also not permitted. Both failures produce bad interviews.

BAD QUESTION GROUP:
{
  "group_label": "Technical interest",
  "line_of_inquiry": "Understand whether the applicant is really serious about technology.",
  "questions": [
    { "question_id": "Q-001", "question": "Tell me about your interest in technology." },
    { "question_id": "Q-002", "question": "Walk me through your technical projects." }
  ]
}

BETTER QUESTION GROUP (follows the arc):
{
  "group_label": "Interest versus making",
  "line_of_inquiry": "Whether the applicant's stated interest in technology has translated into self-directed building, experimentation, or sustained technical choices.",
  "questions": [
    { "question_id": "Q-001", "question": "When you think about the projects or experiments that most shaped your technical confidence, which one actually changed how you worked and why?", "framing_note": "This opens with a concrete example so the applicant can set the frame before the group probes more directly." },
    { "question_id": "Q-002", "question": "When you hit the limit of what you could figure out on your own in that project, what was the very next move you made?", "framing_note": "This is worded to draw out decision-making at the exact moment the applicant ran into difficulty." },
    { "question_id": "Q-003", "question": "Where does your file understate the hands-on work you have really done, and where does it overstate how far that work has gone?", "framing_note": "This gently tests the strongest reading of the file without turning the question adversarial." }
  ]
}

---

OUTPUT SCHEMA - return exactly this structure:

{
  "question_groups": [
    {
      "focus_area_id": "FA-001",
      "group_label": "Short scannable label for this question set",
      "line_of_inquiry": "One sentence. The strategic thing the interviewer is trying to understand here.",
      "questions": [
        {
          "question_id": "Q-001",
          "question": "One interview-ready question.",
          "framing_note": "One short sentence explaining the phrasing move behind this question."
        }
      ],
      "source_theme_ids": ["THEME-001"],
      "source_signal_ids": ["SIG-001", "SIG-002"]
    }
  ]
}

Produce exactly one question_group per provided focus_area_id.
Produce 2 to 4 questions per group.
source_theme_ids and source_signal_ids must reference real IDs from the grounding data.
"""

    user_prompt = f"""
Produce interview question groups for this applicant.

FOCUS AREAS (primary input - direction and emphasis):
{json.dumps(bundle, indent=2)}

ENTITY REFERENCE MAP:
{json.dumps(entity_id_map, indent=2)}

Return only valid JSON matching the output schema.
Every question must be grounded in something specific from this application.
Every group must feel ready for live use in the interview, not like prep notes.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_interview(bundle: dict, entity_id_map: list) -> str:
    messages = build_interview_messages(bundle, entity_id_map)
    return generate(messages, call_label="call_3")
