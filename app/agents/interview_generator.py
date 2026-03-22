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

    # Prohibited language terms for prompt awareness
    prohibited_terms = [
        "Strength", "Weakness", "Outstanding", "Exceptional", "Deficiency", 
        "Below average", "Underperformance", "High potential", "Top candidate", 
        "Risk factor", "Admit", "Reject", "Likelihood", "Impressive", 
        "Concerning", "Excellent", "Poor", "Weak", "Strong", "Competitive", "Uncompetitive"
    ]

    system_prompt = f"""
    You are an objective communication system. Your task is to generate structured interview themes and question groups based strictly on the provided Signal-Evidence Bundle.

    RULES:
    1. Base all themes and questions ONLY on the signals and supporting evidence in the bundle.
    2. Do NOT re-interpret the signals or introduce outside facts.
    3. Questions must be exploratory and open-ended.
    4. Maintain a neutral, factual tone.
    5. PROHIBITED TERMS: You MUST NOT use any of the following terms in your output:
       {", ".join(prohibited_terms)}
    6. No admissions commentary, no predictions, no likelihood statements.
    7. Output must be a single JSON object with exactly two top-level keys: "themes" and "question_groups".
    8. Every object in "question_groups" MUST contain exactly these keys:
       - "theme_id"
       - "group_title"
       - "questions"
    9. Do not use alternate key names such as "title", "heading", "question_title", "question_group_title", or nested wrappers.
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
