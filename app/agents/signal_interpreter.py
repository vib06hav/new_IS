import json
from app.llm.client import generate

def build_signal_interpreter_messages(projection: dict) -> list[dict]:
    """
    Builds the exact Stage 1.7 Call 1 prompt messages.
    """

    # Prohibited language terms for prompt awareness
    prohibited_terms = [
        "Strength", "Weakness", "Outstanding", "Exceptional", "Deficiency", 
        "Below average", "Underperformance", "High potential", "Top candidate", 
        "Risk factor", "Admit", "Reject", "Likelihood", "Impressive", 
        "Concerning", "Excellent", "Poor", "Weak", "Strong", "Competitive", "Uncompetitive"
    ]

    system_prompt = f"""
    You are an objective, structural analysis system. Your task is to analyze an applicant's curated canonical projection and deterministic signals to identify higher-level behavioral patterns (interpreted signals).

    RULES:
    1. Base all analysis strictly on the provided projection and deterministic signals. Do not introduce outside facts.
    2. Maintain a neutral, factual tone. Describe behavior without evaluating it.
    3. Exactly follow the output JSON schema.
    4. PROHIBITED TERMS: You MUST NOT use any of the following terms in your output:
       {", ".join(prohibited_terms)}
    5. No interview questions, no themes, no narrative summaries.
    6. No admissions commentary, no predictions, no likelihood statements.
    7. Do not use synonyms or indirect evaluative phrasing such as "indicating strong performance", "showing aptitude", "demonstrates excellence", "high achievement", "notable success", or similar language.
    8. Prefer literal observational phrasing. Good examples:
       - "Applicant recorded a score of 99.33% in JEE Mains."
       - "Applicant has leadership entries across 2 activities."
       - "Applicant's academic records include multiple science and mathematics subjects."
       - "Applicant reported 5 activity entries spanning multiple categories."
    9. Bad examples that must not appear:
       - "indicating strong performance"
       - "suggesting aptitude"
       - "reflecting excellence"
       - "showing impressive commitment"
    10. If a description sounds evaluative, rewrite it as a plain observable statement before finalizing output.

    OUTPUT SCHEMA:
    {{
      "interpreted_signals": [
        {{
          "signal_id": "INT-###",
          "title": "A neural, concise label for the pattern",
          "description": "Factual behavioral observation grounded in evidence",
          "referenced_entity_ids": ["Entity IDs from the projection (e.g., ACA-001)"],
          "supporting_det_signal_ids": ["Signal IDs from the deterministic collection (e.g., DET-001)"]
        }}
      ]
    }}

    Signal IDs for interpreted signals must be numbered sequentially from INT-001.
    """

    user_prompt = f"""
    Analyze the following applicant projection and deterministic signals:

    {json.dumps(projection, indent=2)}

    Return exactly valid JSON with the interpreted signals.
    Before returning, check every title and description against the prohibited terms list and remove any evaluative wording.
    """

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def interpret_signals(projection: dict) -> str:
    """
    Agent 14: Signal interpreter (LLM Call 1).
    Makes exactly one LLM call to interpret signals based on the projection.
    Returns the raw response text (resp.text).
    """
    messages = build_signal_interpreter_messages(projection)

    # Exactly one LLM call
    response_text = generate(messages, call_label="call_1")

    return response_text
