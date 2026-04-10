import httpx
import logging
import os
from typing import Any

from app.config import settings
from app.llm.token_counter import estimate_messages_tokens, estimate_text_tokens

logger = logging.getLogger(__name__)

try:
    from braintrust import init_logger
except ImportError:  # pragma: no cover - optional dependency guard
    init_logger = None

_braintrust_logger = None


def _get_braintrust_logger():
    global _braintrust_logger
    if _braintrust_logger is not None:
        return _braintrust_logger

    if init_logger is None:
        return None

    braintrust_api_key = os.getenv("BRAINTRUST_API_KEY", "").strip()
    if not braintrust_api_key:
        return None

    try:
        _braintrust_logger = init_logger(
            project="AG_InterviewStandardiser",
            api_key=braintrust_api_key,
        )
    except Exception as exc:  # pragma: no cover - tracing must not break LLM calls
        logger.warning("Braintrust initialization failed: %s", exc)
        return None

    return _braintrust_logger


def _messages_for_trace(messages: list[dict]) -> dict[str, Any]:
    system_prompt = ""
    user_payload: list[dict[str, Any]] = []

    for message in messages:
        role = str(message.get("role", ""))
        content = message.get("content", "")
        if role == "system" and not system_prompt:
            system_prompt = str(content)
        else:
            user_payload.append({"role": role, "content": content})

    return {
        "system_prompt": system_prompt,
        "user_input": user_payload,
    }


def _run_with_braintrust_trace(
    messages: list[dict],
    call_label: str | None,
    llm_callable,
):
    bt_logger = _get_braintrust_logger()
    if bt_logger is None:
        return llm_callable()

    trace_input = _messages_for_trace(messages)
    metadata = {
        "model_name": settings.LLM_MODEL_NAME,
        "provider": settings.LLM_PROVIDER,
    }
    if call_label:
        metadata["request_identifier"] = call_label

    try:
        span = bt_logger.start_span(
            name=call_label or "llm_call",
            type="llm",
        )
        return _run_llm_span(span, trace_input, metadata, llm_callable)
    except Exception as exc:  # pragma: no cover - tracing must not break LLM calls
        logger.warning("Braintrust tracing failed: %s", exc)
        return llm_callable()


def _run_llm_span(span, trace_input: dict[str, Any], metadata: dict[str, Any], llm_callable):
    try:
        span.log(
            input=trace_input,
            metadata=metadata,
            tags=["pipeline:interview_signals"],
        )
        response_text = llm_callable()
        span.log(output=response_text)
        return response_text
    finally:
        span.end()


class LLMClientError(Exception):
    """Raised when the LLM client cannot obtain a valid response."""


def generate(messages: list[dict], call_label: str | None = None) -> str:
    """
    Provider-agnostic public interface for exactly one logical LLM call.
    The active transport is selected by settings.LLM_PROVIDER.
    """
    if settings.LLM_DISABLE_LIVE_CALLS or os.getenv("LLM_DISABLE_LIVE_CALLS", "").strip().lower() in {"1", "true", "yes", "on"}:
        raise LLMClientError("Live LLM calls are disabled in this environment.")

    if settings.LLM_PROVIDER == "openrouter":
        return _run_with_braintrust_trace(
            messages,
            call_label,
            lambda: _generate_openai_compatible(messages, call_label),
        )

    raise LLMClientError(f"Unsupported LLM_PROVIDER: {settings.LLM_PROVIDER}")

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

def _log_preview(response_text: str) -> None:
    preview = response_text[:80].replace("\n", " ")
    if len(response_text) > 80:
        preview += "..."
    logger.info(f"LLM successfully responded. Content preview: {preview}")
