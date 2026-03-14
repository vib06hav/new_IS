import json
from app.llm.client import generate

def generate_interview(bundle: dict, entity_id_map: list) -> str:
    """
    Agent 16: Interview generator (LLM Call 2).
    Makes exactly one LLM call to produce interview themes and questions.
    Returns the raw response text (resp.text).
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
    """

    user_prompt = f"""
    Generate an interview preparation report based on the following Signal-Evidence Bundle:

    {json.dumps(bundle, indent=2)}

    Reference the provided entity ID map for grounding:
    {json.dumps(entity_id_map, indent=2)}

    Return exactly valid JSON.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Exactly one LLM call
    response_text = generate(messages)

    return response_text
