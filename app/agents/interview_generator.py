import json
from app.llm.client import generate

def _compact_entity_references(entity_id_map: list, bundle: dict) -> list[dict]:
    referenced_ids = set()
    for pair in bundle.get("signal_evidence_pairs", []):
        signal = pair.get("signal", {}) if isinstance(pair, dict) else {}
        for entity_id in signal.get("referenced_entity_ids", []) or []:
            if entity_id:
                referenced_ids.add(entity_id)
        for evidence in pair.get("evidence", []) or []:
            if isinstance(evidence, dict) and evidence.get("entity_id"):
                referenced_ids.add(evidence["entity_id"])

    compact_refs = []
    seen = set()
    for entry in entity_id_map:
        entity_id = entry.get("entity_id")
        if entity_id not in referenced_ids or entity_id in seen:
            continue
        seen.add(entity_id)
        compact_entry = {"entity_id": entity_id}
        descriptor = entry.get("descriptor")
        if descriptor:
            compact_entry["descriptor"] = descriptor
        compact_refs.append(compact_entry)
    return compact_refs


def build_interview_messages(bundle: dict, entity_id_map: list) -> list[dict]:
    """
    Builds the exact Stage 1.7 Call 2 prompt messages.
    """

    # Reduced prohibited terms - keeping only extreme bias or admissions outcomes
    prohibited_terms = [
        "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor"
    ]

    system_prompt = f"""
    You are a Senior Admissions Interviewer. Your task is to generate sophisticated interview themes and probing question groups based on the provided Signal-Evidence Bundle.
    
    You must synthesize the signals and evidence to find the "hooks" for a meaningful conversation.

    RULES:
    1. Base all themes and questions on the signals and supporting evidence in the bundle.
    2. Think like an interviewer: look for depth, contradictions, or unique achievements in the evidence.
    3. Questions must be probing, exploratory, and show that you have read the applicant's specific content (essays/activities).
    4. Avoid generic questions (e.g., "What did you learn?"). Prefer questions that reference their specific projects or experiences.
    5. PROHIBITED TERMS: Do not imply an admissions decision. Do not use: {", ".join(prohibited_terms)}
    6. Output must be a single JSON object with exactly two top-level keys: "themes" and "question_groups".
    7. Every object in "question_groups" MUST contain exactly these keys:
       - "theme_id"
       - "group_title"
       - "questions"
    10. Every "question_groups[i].theme_id" must exactly match one of the emitted "themes[*].theme_id" values.
    11. Every "group_title" must be a short neutral label and must never be empty or null.
    12. If there are 4 themes, there must be 4 question_groups, one linked to each theme_id.
    13. "questions" must be a JSON array of plain strings only. Do not return question objects, dictionaries, metadata, numbering objects, or nested arrays.
    14. Each question must be a single sentence string.

    OUTPUT SCHEMA:
    {{
      "themes": [
        {{
          "theme_id": "THEME-###",
          "title": "A neural, concise label for the theme",
          "description": "Factual summary of the behavioral theme",
          "referenced_entity_ids": ["Entity IDs from the bundle/map"]
        }}
      ],
      "question_groups": [
        {{
          "theme_id": "THEME-###",
          "group_title": "A neutral, concise title for the question group",
          "questions": ["Specific, exploratory, open-ended questions"]
        }}
      ]
    }}

    Theme IDs must be numbered sequentially from THEME-001. 
    Every question group must link to a defined theme_id.
    Example valid question_groups structure:
    [
      {{
        "theme_id": "THEME-001",
        "group_title": "Exploring Technical Engagement",
        "questions": [
          "How did your interest in this area develop over time?",
          "Can you walk through one project or activity in detail?"
        ]
      }},
      {{
        "theme_id": "THEME-002",
        "group_title": "Understanding Leadership Context",
        "questions": [
          "What responsibilities did you handle in this role?",
          "How did decisions get made in that setting?"
        ]
      }}
    ]
    """

    compact_entity_map = _compact_entity_references(entity_id_map, bundle)

    user_prompt = f"""
    Generate an interview preparation report based on the following Signal-Evidence Bundle:

    {json.dumps(bundle, indent=2)}

    Reference the following compact entity grounding list when you need to map IDs to evidence:
    {json.dumps(compact_entity_map, indent=2)}

    Return exactly valid JSON.
    Before returning, verify that every question group has a non-empty "theme_id", a non-empty "group_title", and a "questions" array of plain string questions only.
    """

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def generate_interview(bundle: dict, entity_id_map: list) -> str:
    """
    Agent 16: Interview generator (LLM Call 2).
    Makes exactly one LLM call to produce interview themes and questions.
    Returns the raw response text (resp.text).
    """
    messages = build_interview_messages(bundle, entity_id_map)

    # Exactly one LLM call
    response_text = generate(messages, call_label="call_2")

    return response_text
