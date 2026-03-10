import json
from typing import Dict, Any
from app.llm.client import generate_synthesis
import logging

logger = logging.getLogger(__name__)

import uuid

def _uuid_encoder(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def _format_canonical_for_prompt(canonical_data: Dict[str, Any]) -> str:
    """Format the specific allowed canonical collections for the LLM."""
    lines = []
    
    # academic_entries[]
    lines.append("ACADEMIC ENTRIES:")
    for entry in canonical_data.get("academic_entries", []):
        lines.append(json.dumps(entry, separators=(',', ':'), default=_uuid_encoder))
        
    # schooling_history[]
    lines.append("\nSCHOOLING HISTORY:")
    for entry in canonical_data.get("schooling_history", []):
        lines.append(json.dumps(entry, separators=(',', ':'), default=_uuid_encoder))
        
    # test_entries[]
    lines.append("\nTEST ENTRIES:")
    for entry in canonical_data.get("test_entries", []):
        lines.append(json.dumps(entry, separators=(',', ':'), default=_uuid_encoder))
        
    # essay_entries[]
    lines.append("\nESSAY ENTRIES:")
    for entry in canonical_data.get("essay_entries", []):
        lines.append(json.dumps(entry, separators=(',', ':'), default=_uuid_encoder))
        
    # activity_entries[]
    lines.append("\nACTIVITY ENTRIES:")
    for entry in canonical_data.get("activity_entries", []):
        lines.append(json.dumps(entry, separators=(',', ':'), default=_uuid_encoder))
        
    # identifiers.family_background
    lines.append("\nFAMILY BACKGROUND:")
    family_bg = canonical_data.get("identifiers", {}).get("family_background")
    if family_bg:
        lines.append(json.dumps(family_bg, separators=(',', ':'), default=_uuid_encoder))
        
    # extract valid entity IDs
    valid_ids = []
    for section in ["academic_entries", "schooling_history", "test_entries", "essay_entries", "activity_entries"]:
        for entry in canonical_data.get(section, []):
            if "entity_id" in entry:
                valid_ids.append(str(entry["entity_id"]))
                
    lines.append("\nVALID ENTITY IDs FOR REFERENCE:")
    if valid_ids:
        for vid in valid_ids:
            lines.append(f"- {vid}")
    else:
        lines.append("None")
        
    return "\n".join(lines)


def run_synthesis_agent(canonical_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 12 - Synthesis Agent.
    Accepts projection-annotated canonical representation.
    Produces themes and question_groups via exactly one LLM call.
    """
    
    formatted_input = _format_canonical_for_prompt(canonical_data)
    
    prompt_template = """INPUT CANONICAL DATA:
%s

You are an objective, structural system that generates interview preparation themes and questions based ONLY on the provided Canonical Data Profile above.

RULES:
1. Output strictly valid JSON matching the exact schema below.
2. Reference ONLY the `entity_id` values explicitly listed in the "VALID ENTITY IDs FOR REFERENCE" section at the end of the input (e.g., "ACA-001", "TEST-001", "ESS-001", "ACT-001", "LEAD-001", "SCH-001"). 
3. NEVER construct new identifiers or infer prefixes from section names (e.g., DO NOT use "ESSAY-###" or "ACADEMIC-###"). You must EXACTLY copy the literal string from the valid IDs list. If there are no references or if you are unsure, return an empty array `[]`.
4. `theme_id` values MUST follow the exact format "THEME-###" (e.g., THEME-001).
5. STRICTLY BANNED WORDS: You must NEVER use the words "strength", "weakness", "outstanding", "deficiency", "below average", "underperformance", "high potential", "top candidate", "risk factor", "admit", "reject", "likelihood", or any of their plural forms. Use completely neutral, structural language.
6. POSITIVE GUIDANCE: Instead of asking about "strengths" or "weaknesses", ask about "performance patterns", "characteristics", "outcomes", or "areas of focus". Focus exclusively on facts and metrics.
7. Do not output any additional text outside the JSON object.

REQUIRED JSON SCHEMA:
{
  "themes": [
    { "theme_id": "THEME-###", "title": "string", "description": "string", "referenced_entity_ids": ["string"] }
  ],
  "question_groups": [
    { "theme_id": "THEME-###", "group_title": "string", "questions": ["string"] }
  ]
}
"""
    prompt = prompt_template % (formatted_input,)
    
    logger.debug(f"Synthesis prompt length (chars): {len(prompt)}")
    logger.info("Executing Synthesis Agent (Agent 12) LLM generation.")
    
    # Exactly one LLM call, no multi-stage reasoning
    synthesis_output = generate_synthesis(prompt)
    
    logger.debug(f"Raw LLM synthesis output: {json.dumps(synthesis_output, indent=2)}")
    
    return synthesis_output
