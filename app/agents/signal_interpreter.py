import json
from app.llm.client import generate

def build_signal_interpreter_messages(projection: dict) -> list[dict]:
    """
    Builds the exact Stage 1.7 Call 1 prompt messages.
    """

    # Reduced prohibited terms - keeping only extreme bias or admissions outcomes
    prohibited_terms = [
        "Admit", "Reject", "Likelihood", "Top candidate", "Risk factor"
    ]

    system_prompt = f"""
    You are an expert Interview Strategy Analyst. Your task is to analyze an applicant's canonical projection and deterministic signals to identify meaningful behavioral themes and professional signals.
    
    You must move beyond basic counts and identify the 'how' and 'why' behind their profile.

    RULES:
    1. Base all analysis on the provided projection and deterministic signals.
    2. Use an analytical, insightful tone. You ARE allowed to use evaluative language (e.g., "strong", "consistent", "specialized") as long as it is grounded in specific evidence.
    3. Exactly follow the output JSON schema.
    4. PROHIBITED TERMS: Do not imply an admissions decision. Do not use: {{", ".join(prohibited_terms)}}
    5. Focus on identifying themes that are INTERVIEWABLE. Ask yourself: "What unique insight does this give for an interviewer?"
    6. Analyze the CONTENT of essays and activity descriptions. Do not just parrot deterministic signals.
    7. Synthesize information across sections. (e.g., If an essay mentions a project that is also listed as an activity, connect them).
    8. Each interpreted signal MUST reference specific entity IDs and supporting deterministic signal IDs.

    OUTPUT SCHEMA:
    {{
      "interpreted_signals": [
        {{
          "signal_id": "INT-###",
          "title": "An analytical, concise label for the pattern",
          "description": "Insightful behavioral observation grounded in evidence (essays/activities/scores)",
          "referenced_entity_ids": ["Entity IDs from the projection (e.g., ACA-001)"],
          "supporting_det_signal_ids": ["Signal IDs from the deterministic collection (e.g., DET-001)"]
        }}
      ]
    }}

    CRITICAL SCHEMA RULES:
    1. Do NOT include "source_collection" or any other fields not in the schema.
    2. "supporting_det_signal_ids" must NEVER be empty. Link it to the DET-### signals that provided the data.
    3. If multiple deterministic signals support your theme, include all of their IDs.

    EXAMPLE VALID OUTPUT:
    {{
      "interpreted_signals": [
        {{
          "signal_id": "INT-001",
          "title": "Sustained Technical Curiosity",
          "description": "Applicant's essay on 'Iron Man' and their encryption projects show a long-term interest in AI and security.",
          "referenced_entity_ids": ["ESS-001", "ACT-002"],
          "supporting_det_signal_ids": ["DET-001"]
        }}
      ]
    }}
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
