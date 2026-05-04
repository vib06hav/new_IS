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

---

WRITING RULES:

- The group_label should be short and scannable.
- line_of_inquiry should be one sentence.
- Every question must be usable as-is in a real interview.
- Questions should be specific to this applicant, not generic admissions prompts.
- Do not infer gender.
- Do not use committee language or framework language.
- Do not overpack the questions with tiny technical details unless those details are the point.

PROHIBITED QUESTION FORMS:
- "Tell me about X"
- "Can you elaborate on X"
- "Could you tell me about"
- "Could you walk me through"
- "Walk me through"
- "What drew you to X"
- "How did your interest in X develop over time"

BAD QUESTION GROUP:
{
  "group_label": "Technical interest",
  "line_of_inquiry": "Understand whether the applicant is really serious about technology.",
  "questions": [
    { "question_id": "Q-001", "question": "Tell me about your interest in technology." },
    { "question_id": "Q-002", "question": "Walk me through your technical projects." }
  ]
}

BETTER QUESTION GROUP:
{
  "group_label": "Interest versus making",
  "line_of_inquiry": "Whether the applicant's stated interest in technology has translated into self-directed building, experimentation, or sustained technical choices.",
  "questions": [
    { "question_id": "Q-001", "question": "When you think about the projects or experiments that most shaped your technical confidence, which one actually changed how you worked and why?" },
    { "question_id": "Q-002", "question": "Where does your file understate the hands-on work you have really done, and where does it overstate how far that work has gone?" },
    { "question_id": "Q-003", "question": "What has kept your technical interests most alive so far: building, reading, problem-solving with others, or something else?" }
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
          "question": "One interview-ready question."
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
