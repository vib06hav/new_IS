import httpx
import logging
import os
import random
import re
import threading
import time
from dataclasses import dataclass
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


@dataclass(frozen=True)
class LLMPolicy:
    name: str
    api_key: str
    primary_model: str
    fallback_model: str
    max_retries: int
    backoff_seconds: float
    max_concurrency: int
    max_tokens: int


class LLMCapacityError(LLMClientError):
    """Raised when app-side LLM request concurrency is exhausted."""


class LLMBudgetExceededError(LLMClientError):
    """Raised when upstream budget limits are exhausted."""


class _RequestCapacity:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.active = 0
        self.lock = threading.Lock()

    def snapshot(self) -> dict[str, int]:
        with self.lock:
            return {"active": self.active, "limit": self.limit}

    def acquire(self, policy_name: str) -> None:
        with self.lock:
            if self.active >= self.limit:
                raise LLMCapacityError(
                    f"{policy_name.replace('_', ' ').title()} capacity is temporarily full. Please try again shortly."
                )
            self.active += 1

    def release(self) -> None:
        with self.lock:
            self.active = max(0, self.active - 1)


_policy_capacities = {
    "generation": _RequestCapacity(settings.AICREDITS_GENERATION_MAX_CONCURRENCY),
    "report_chat": _RequestCapacity(settings.AICREDITS_REPORT_CHAT_MAX_CONCURRENCY),
}


def get_llm_capacity_snapshot() -> dict[str, dict[str, int]]:
    return {name: capacity.snapshot() for name, capacity in _policy_capacities.items()}


def _policy_for_call(call_label: str | None) -> LLMPolicy:
    if call_label in {"call_1", "call_2"}:
        return LLMPolicy(
            name="generation",
            api_key=settings.AICREDITS_GENERATION_API_KEY,
            primary_model=settings.AICREDITS_GENERATION_MODEL_PRIMARY,
            fallback_model=settings.AICREDITS_GENERATION_MODEL_FALLBACK,
            max_retries=settings.AICREDITS_GENERATION_MAX_RETRIES,
            backoff_seconds=settings.AICREDITS_GENERATION_BACKOFF_SECONDS,
            max_concurrency=settings.AICREDITS_GENERATION_MAX_CONCURRENCY,
            max_tokens=settings.AICREDITS_GENERATION_MAX_TOKENS,
        )
    return LLMPolicy(
        name="report_chat",
        api_key=settings.AICREDITS_REPORT_CHAT_API_KEY,
        primary_model=settings.AICREDITS_REPORT_CHAT_MODEL_PRIMARY,
        fallback_model=settings.AICREDITS_REPORT_CHAT_MODEL_FALLBACK,
        max_retries=settings.AICREDITS_REPORT_CHAT_MAX_RETRIES,
        backoff_seconds=settings.AICREDITS_REPORT_CHAT_BACKOFF_SECONDS,
        max_concurrency=settings.AICREDITS_REPORT_CHAT_MAX_CONCURRENCY,
        max_tokens=settings.AICREDITS_REPORT_CHAT_MAX_TOKENS,
    )


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

    if settings.LLM_PROVIDER == "aicredits":
        return _run_with_braintrust_trace(
            messages,
            call_label,
            lambda: _generate_aicredits(messages, call_label),
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


def _generate_aicredits(messages: list[dict], call_label: str | None = None) -> str:
    if not messages:
        raise LLMClientError("generate() called with an empty messages list.")

    policy = _policy_for_call(call_label)
    capacity = _policy_capacities[policy.name]
    capacity.acquire(policy.name)
    try:
        return _run_aicredits_policy(messages, call_label, policy)
    finally:
        capacity.release()


def _run_aicredits_policy(messages: list[dict], call_label: str | None, policy: LLMPolicy) -> str:
    if not policy.api_key:
        raise LLMClientError(f"{policy.name} API key is not configured.")
    if not policy.primary_model:
        raise LLMClientError(f"{policy.name} primary model is not configured.")

    models = [policy.primary_model]
    if policy.fallback_model and policy.fallback_model != policy.primary_model:
        models.append(policy.fallback_model)

    last_error: Exception | None = None
    for model_index, model_name in enumerate(models):
        max_attempts = policy.max_retries + 1
        for attempt in range(max_attempts):
            try:
                return _send_aicredits_request(
                    messages=messages,
                    call_label=call_label,
                    model_name=model_name,
                    api_key=policy.api_key,
                    max_tokens=policy.max_tokens,
                )
            except LLMBudgetExceededError:
                raise
            except LLMClientError as exc:
                last_error = exc
                if not _is_retryable_llm_error(exc):
                    raise
                if attempt >= max_attempts - 1:
                    break
                _sleep_with_backoff(policy.backoff_seconds, attempt)
        if model_index == 0 and len(models) > 1 and call_label in {"call_1", "call_2"}:
            logger.warning("Switching %s from primary model to fallback model after retryable failures.", call_label)
        elif model_index == 0 and len(models) > 1:
            logger.warning("Switching %s traffic from primary model to fallback model.", policy.name)

    if last_error is not None:
        raise last_error
    raise LLMClientError("AICredits request failed before a response was produced.")


def _send_aicredits_request(
    *,
    messages: list[dict],
    call_label: str | None,
    model_name: str,
    api_key: str,
    max_tokens: int,
) -> str:
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": settings.LLM_TEMPERATURE,
        "max_tokens": max_tokens,
    }
    if settings.LLM_JSON_MODE:
        payload["response_format"] = {"type": "json_object"}

    logger.info(
        "AICredits request prepared%s using model=%s. Estimated prompt tokens=%s",
        f" [{call_label}]" if call_label else "",
        model_name,
        estimate_messages_tokens(messages),
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            f"{settings.AICREDITS_BASE_URL.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
            timeout=float(settings.LLM_TIMEOUT_SECONDS),
        )
    except httpx.TimeoutException as exc:
        raise LLMClientError(f"LLM timeout calling {model_name}.") from exc
    except httpx.TransportError as exc:
        raise LLMClientError(f"LLM transport failure calling {model_name}: {exc}") from exc

    _log_rate_limit_headers(response, call_label, model_name)

    if response.status_code == 402:
        raise LLMBudgetExceededError("AICredits budget has been exhausted for this key.")
    if response.status_code in {400, 401, 403}:
        raise LLMClientError(f"AICredits rejected the request with status {response.status_code}.")
    if response.status_code == 429:
        raise LLMClientError("AICredits rate limit reached.")
    if response.status_code >= 500:
        raise LLMClientError(f"AICredits upstream error ({response.status_code}).")
    try:
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        raise LLMClientError(f"AICredits request failed with status {response.status_code}.") from exc
    except ValueError as exc:
        raise LLMClientError("AICredits returned invalid JSON.") from exc

    response_text = _extract_openai_compatible_text(data)
    if not response_text.strip():
        raise LLMClientError("AICredits response did not include usable content.")

    logger.info(
        "AICredits response received%s using model=%s. Estimated response tokens=%s",
        f" [{call_label}]" if call_label else "",
        model_name,
        estimate_text_tokens(response_text),
    )
    _log_preview(response_text)
    return response_text


def _log_rate_limit_headers(response: httpx.Response, call_label: str | None, model_name: str) -> None:
    limit = response.headers.get("X-RateLimit-Limit")
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset = response.headers.get("X-RateLimit-Reset")
    if limit or remaining or reset:
        logger.info(
            "AICredits rate-limit headers%s model=%s limit=%s remaining=%s reset=%s",
            f" [{call_label}]" if call_label else "",
            model_name,
            limit or "unknown",
            remaining or "unknown",
            reset or "unknown",
        )


def _sleep_with_backoff(base_seconds: float, attempt: int) -> None:
    delay = (base_seconds * (2 ** attempt)) + random.uniform(0, 1)
    time.sleep(delay)


def _is_retryable_llm_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(token in text for token in ("rate limit", "timeout", "transport", "upstream error", "status 5", "invalid json"))


def _extract_openai_compatible_text(data: Any) -> str:
    choices = data.get("choices", []) if isinstance(data, dict) else []
    if not choices or not isinstance(choices, list):
        raise LLMClientError("OpenAI-compatible response is missing choices[].")

    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message", {})
    content = message.get("content")

    if isinstance(content, str):
        return _clean_json_response(content)

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return _clean_json_response("".join(parts))

    return ""


def _clean_json_response(text: str) -> str:
    """
    Strips markdown code fences (e.g., ```json ... ```) and leading/trailing
    whitespace from LLM responses to ensure valid JSON parsing.
    """
    if not text:
        return ""
    
    text = text.strip()
    
    # Try to extract content from markdown fences first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    else:
        # Fallback: if no fences, try to find the first '{' and last '}'
        # This handles preambles like "Sure, here is the JSON:"
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
    
    return text.strip()


def _log_preview(response_text: str) -> None:
    preview = response_text[:80].replace("\n", " ")
    if len(response_text) > 80:
        preview += "..."
    logger.info(f"LLM successfully responded. Content preview: {preview}")
