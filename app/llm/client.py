import httpx
import logging

from app.config import settings

logger = logging.getLogger(__name__)

def generate(messages: list[dict]) -> str:
    """
    Makes exactly one synchronous HTTP call to the configured LLM endpoint.
    Accepts a messages list in the format required by the endpoint.
    Returns the raw response text (resp.text).
    Does not parse, validate, or interpret the response.
    Does not retry on failure.
    Raises on HTTP error.
    """
    payload = {
        "model": settings.LLM_MODEL_NAME,
        "messages": messages,
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
        return response.text
        
    except httpx._exceptions.HTTPError as e:
        logger.error(f"LLM failure: {str(e)}")
        raise RuntimeError(f"LLM Generation Failed: {str(e)}")
