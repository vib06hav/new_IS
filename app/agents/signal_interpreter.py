import json
from app.llm.client import generate

def interpret_signals(projection: dict) -> str:
    """
    Agent 14: Signal interpreter (LLM Call 1).
    Makes exactly one LLM call to interpret signals based on the projection.
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
    You are an objective, structural analysis system. Your task is to analyze an applicant's curated canonical projection and deterministic signals to identify higher-level behavioral patterns (interpreted signals).

    RULES:
    1. Base all analysis strictly on the provided projection and deterministic signals. Do not introduce outside facts.
    2. Maintain a neutral, factual tone. Describe behavior without evaluating it.
    3. Exactly follow the output JSON schema.
    4. PROHIBITED TERMS: You MUST NOT use any of the following terms in your output:
       {", ".join(prohibited_terms)}
    5. No interview questions, no themes, no narrative summaries.
    6. No admissions commentary, no predictions, no likelihood statements.

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
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Exactly one LLM call
    response_text = generate(messages)

    return response_text
