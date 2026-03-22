import httpx
import logging
import time
from typing import Any

from app.config import settings
from app.llm.token_counter import estimate_messages_tokens, estimate_text_tokens

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when the LLM client cannot obtain a valid response."""


def generate(messages: list[dict], call_label: str | None = None) -> str:
    """
    Provider-agnostic public interface for exactly one logical LLM call.
    The active transport is selected by settings.LLM_PROVIDER.
    """
    if settings.LLM_PROVIDER == "ollama":
        return _generate_ollama(messages, call_label)

    if settings.LLM_PROVIDER in {"openai", "openrouter", "openai_compatible"}:
        return _generate_openai_compatible(messages, call_label)

    raise LLMClientError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")


def _generate_ollama(messages: list[dict], call_label: str | None = None) -> str:
    """
    Submits a messages list to Ollama and returns the response text.
    Handles Ollama cold-starts (done_reason='load') transparently by polling.
    """
    prompt = _build_prompt(messages)
    prompt_token_estimate = estimate_messages_tokens(messages)
    logger.info(
        "LLM request prepared%s. Estimated prompt tokens=%s",
        f" [{call_label}]" if call_label else "",
        prompt_token_estimate,
    )
    payload = {
        "model": settings.LLM_MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "keep_alive": settings.LLM_KEEP_ALIVE,
        "options": {
            "temperature": settings.LLM_TEMPERATURE
        }
    }

    elapsed = 0
    while True:
        try:
            response = httpx.post(
                settings.LLM_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=float(settings.LLM_OLLAMA_TIMEOUT_SECONDS)
            )
            response.raise_for_status()
            data = response.json()

            response_text = data.get("response", "")
            done_reason = data.get("done_reason", "")

            if done_reason == "stop" and response_text.strip():
                response_tokens = estimate_text_tokens(response_text)
                logger.info(
                    "LLM response received%s. Estimated response tokens=%s",
                    f" [{call_label}]" if call_label else "",
                    response_tokens,
                )
                _log_preview(response_text)
                return response_text

            if done_reason == "load":
                if elapsed >= settings.LLM_LOAD_WAIT_TIMEOUT_SECONDS:
                    raise LLMClientError(
                        f"Ollama model '{settings.LLM_MODEL_NAME}' load timeout after "
                        f"{settings.LLM_LOAD_WAIT_TIMEOUT_SECONDS}s"
                    )

                logger.info(
                    "Ollama cold-start in progress (load). Waiting %ss... (%s/%s)",
                    settings.LLM_LOAD_POLL_INTERVAL_SECONDS,
                    elapsed,
                    settings.LLM_LOAD_WAIT_TIMEOUT_SECONDS,
                )
                time.sleep(settings.LLM_LOAD_POLL_INTERVAL_SECONDS)
                elapsed += settings.LLM_LOAD_POLL_INTERVAL_SECONDS
                continue

            raise LLMClientError(
                f"Ollama unusable response: done_reason={done_reason}, "
                f"empty={not response_text.strip()}"
            )
        except httpx.HTTPError as e:
            logger.error(f"LLM Transport Failure: {str(e)}")
            raise LLMClientError(f"LLM Transport Failure: {str(e)}")


def _generate_openai_compatible(messages: list[dict], call_label: str | None = None) -> str:
    """
    Sends a chat-completions style request to an OpenAI-compatible endpoint,
    which covers providers such as OpenAI and OpenRouter.
    """
    if not messages:
        raise LLMClientError("generate() called with an empty messages list.")

    payload: dict[str, Any] = {
        "model": settings.LLM_MODEL_NAME,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
    }
    logger.info(
        "LLM request prepared%s. Estimated prompt tokens=%s",
        f" [{call_label}]" if call_label else "",
        estimate_messages_tokens(messages),
    )
    if settings.LLM_JSON_MODE:
        payload["response_format"] = {"type": "json_object"}

    headers = {"Content-Type": "application/json"}
    if settings.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LLM_API_KEY}"

    try:
        response = httpx.post(
            settings.LLM_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=float(settings.LLM_TIMEOUT_SECONDS)
        )
        response.raise_for_status()
        data = response.json()

        response_text = _extract_openai_compatible_text(data)
        if not response_text.strip():
            raise LLMClientError("OpenAI-compatible response did not include usable content.")

        logger.info(
            "LLM response received%s. Estimated response tokens=%s",
            f" [{call_label}]" if call_label else "",
            estimate_text_tokens(response_text),
        )
        _log_preview(response_text)
        return response_text
    except httpx.HTTPError as e:
        logger.error(f"LLM Transport Failure: {str(e)}")
        raise LLMClientError(f"LLM Transport Failure: {str(e)}")


def _extract_openai_compatible_text(data: Any) -> str:
    choices = data.get("choices", []) if isinstance(data, dict) else []
    if not choices or not isinstance(choices, list):
        raise LLMClientError("OpenAI-compatible response is missing choices[].")

    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)

    return ""


def _build_prompt(messages: list[dict]) -> str:
    """Flattens role/content dicts into a single prompt string for Ollama."""
    if not messages:
        raise LLMClientError("generate() called with an empty messages list.")

    parts = []
    for msg in messages:
        role = str(msg.get("role", "user")).upper()
        content = str(msg.get("content", "")).strip()
        if content:
            parts.append(f"{role}: {content}")

    if not parts:
        raise LLMClientError("generate() called with a messages list containing no non-empty content.")

    return "\n\n".join(parts)


def _log_preview(response_text: str) -> None:
    preview = response_text[:80].replace("\n", " ")
    if len(response_text) > 80:
        preview += "..."
    logger.info(f"LLM successfully responded. Content preview: {preview}")
