import json
import httpx
from typing import Dict, Any
import logging

from app.config import settings
from app.llm.projection import build_synthesis_projection

logger = logging.getLogger(__name__)

def generate_interview_prep(canonical_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 12 - Interview Preparation Generator
    Synchronous LLM call over HTTP. 
    Strictly accepts canonical data, strictly returns 3 fields.
    No retries, no orchestration frameworks.
    """
    
    # Contract: Semantic categories, non-evaluative, descriptive phrasing only.
    # explicit forbid ranking, scoring, or value-laden adjectives.
    projection_text = build_synthesis_projection(canonical_data)

    prompt = f"""
    You are an objective, structural system that generates interview preparation materials based ONLY on the provided Applicant Profile.

    Rules:
    1. Do not use evaluative adjectives (e.g., "strong", "weak", "excellent").
    2. Do not score, rank, or compare the applicant.
    3. Use descriptive, neutral, structural phrasing only.
    4. Base all output strictly on the provided structured Profile data. No inference beyond explicit data.
    5. Output exactly valid JSON with ONLY three keys: "snapshot", "discussion_focus_areas", "suggested_questions".
    6. Each value MUST be a plain string. No arrays, no nested objects, no additional keys. If you have lists, convert them into newline-separated text inside a single string.
    7. Do not return explanations or text outside the JSON object.

    Applicant Profile:
    {projection_text}
    """

    payload = {
        "model": settings.LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0
        }
    }

    try:
        response = httpx.post(
            settings.LLM_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180.0
        )
        response.raise_for_status()
        result_json = response.json()
        
        # Parse Ollama response format
        content_str = result_json.get("response", "{}")
        content = json.loads(content_str)
        
        return {
            "snapshot": content.get("snapshot", ""),
            "discussion_focus_areas": content.get("discussion_focus_areas", []),
            "suggested_questions": content.get("suggested_questions", [])
        }
        
    except httpx._exceptions.HTTPError as e:
        # Single Call Rule - no retries. Just bubble up or return empty structure.
        logger.error(f"LLM timeout or failure: {str(e)}")
        raise RuntimeError(f"LLM Synthesis Failed: {str(e)}")
    except json.JSONDecodeError:
        logger.error("LLM timeout or failure (JSON Decode Error).")
        raise RuntimeError("LLM returned malformed JSON.")

def generate_synthesis(prompt: str) -> Dict[str, Any]:
    """
    Synchronous LLM call over HTTP.
    Strictly accepts a fully baked prompt, returns JSON dict.
    No retries, no orchestration frameworks.
    """
    payload = {
        "model": settings.LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0
        }
    }

    try:
        response = httpx.post(
            settings.LLM_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180.0
        )
        response.raise_for_status()
        result_json = response.json()
        
        content_str = result_json.get("response", "{}")
        content = json.loads(content_str)
        return content
        
    except httpx._exceptions.HTTPError as e:
        logger.error(f"LLM timeout or failure: {str(e)}")
        raise RuntimeError(f"LLM Synthesis Failed: {str(e)}")
    except json.JSONDecodeError:
        logger.error("LLM timeout or failure (JSON Decode Error).")
        raise RuntimeError("LLM returned malformed JSON.")
