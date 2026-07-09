from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import settings

logger = logging.getLogger(__name__)

_client: Any | None = None
_client_loaded = False


def langfuse_configured() -> bool:
    return bool(
        settings.LANGFUSE_ENABLED
        and settings.LANGFUSE_HOST
        and settings.LANGFUSE_PUBLIC_KEY
        and settings.LANGFUSE_SECRET_KEY
    )


def get_langfuse_client() -> Any | None:
    global _client, _client_loaded
    if not langfuse_configured():
        return None
    if _client_loaded:
        return _client
    _client_loaded = True
    try:
        from langfuse import get_client

        _client = get_client()
        return _client
    except Exception as exc:  # pragma: no cover - tracing must never break product flow
        logger.warning("Langfuse initialization failed: %s", exc)
        _client = None
        return None


@contextmanager
def langfuse_observation(
    *,
    name: str,
    as_type: str = "span",
    model: str | None = None,
    metadata: dict[str, Any] | None = None,
    input_payload: Any | None = None,
) -> Iterator[Any | None]:
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    kwargs: dict[str, Any] = {
        "name": name,
        "as_type": as_type,
    }
    if model:
        kwargs["model"] = model

    try:
        with client.start_as_current_observation(**kwargs) as observation:
            update_payload: dict[str, Any] = {}
            if metadata:
                update_payload["metadata"] = metadata
            if settings.LANGFUSE_CAPTURE_IO and input_payload is not None:
                update_payload["input"] = input_payload
            if update_payload:
                observation.update(**update_payload)
            yield observation
    except Exception as exc:  # pragma: no cover
        logger.warning("Langfuse observation failed name=%s error=%s", name, exc)
        yield None


def update_langfuse_observation(
    observation: Any | None,
    *,
    output: Any | None = None,
    metadata: dict[str, Any] | None = None,
    usage_details: dict[str, Any] | None = None,
    status_message: str | None = None,
) -> None:
    if observation is None:
        return
    payload: dict[str, Any] = {}
    if settings.LANGFUSE_CAPTURE_IO and output is not None:
        payload["output"] = output
    if metadata:
        payload["metadata"] = metadata
    if usage_details:
        payload["usage_details"] = usage_details
    if status_message:
        payload["status_message"] = status_message
    if not payload:
        return
    try:
        observation.update(**payload)
    except Exception as exc:  # pragma: no cover
        logger.debug("Langfuse observation update failed: %s", exc)


def flush_langfuse() -> None:
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:  # pragma: no cover
        logger.debug("Langfuse flush failed: %s", exc)
