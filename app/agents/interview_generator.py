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

PROHIBITED TERMS: """ + ", ".join(prohibited_terms) + """

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
"""

    user_prompt = f"""
Produce interview question groups for this applicant based on the
following theme-first signal-evidence bundle.

THEME SIGNAL-EVIDENCE BUNDLE:
{json.dumps(bundle, indent=2)}

ENTITY REFERENCE MAP:
{json.dumps(entity_id_map, indent=2)}

Apply your internal question-building framework silently. Return only valid JSON matching the output schema.
Produce exactly one question_group for every theme_id in the bundle, and no others.
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
