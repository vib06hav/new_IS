from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import settings

logger = logging.getLogger(__name__)

_client: Any | None = None
_client_loaded = False


def langfuse_configured() -> bool:
    return bool(
        settings.LANGFUSE_ENABLED
        and _langfuse_base_url()
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
        _prepare_langfuse_environment()
        from langfuse import get_client

        _client = get_client()
        return _client
    except Exception as exc:  # pragma: no cover - tracing must never break product flow
        logger.warning("Langfuse initialization failed: %s", exc)
        _client = None
        return None


def _langfuse_base_url() -> str:
    return (getattr(settings, "LANGFUSE_BASE_URL", "") or settings.LANGFUSE_HOST or "").strip()


def _prepare_langfuse_environment() -> None:
    base_url = _langfuse_base_url()
    if base_url:
        os.environ.setdefault("LANGFUSE_BASE_URL", base_url)
        os.environ.setdefault("LANGFUSE_HOST", base_url)
    if settings.LANGFUSE_PUBLIC_KEY:
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
    if settings.LANGFUSE_SECRET_KEY:
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)


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

    observation_context = None
    observation = None
    try:
        observation_context = client.start_as_current_observation(**kwargs)
        observation = observation_context.__enter__()
        update_payload: dict[str, Any] = {}
        if metadata:
            update_payload["metadata"] = metadata
        if settings.LANGFUSE_CAPTURE_IO and input_payload is not None:
            update_payload["input"] = input_payload
        if update_payload:
            observation.update(**update_payload)
    except Exception as exc:  # pragma: no cover
        logger.warning("Langfuse observation failed name=%s error=%s", name, exc)
        yield None
        return

    exc_info = (None, None, None)
    try:
        yield observation
    except BaseException:
        exc_info = sys.exc_info()
        raise
    finally:
        try:
            observation_context.__exit__(*exc_info)
        except Exception as exc:  # pragma: no cover
            logger.debug("Langfuse observation close failed name=%s error=%s", name, exc)


@contextmanager
def langfuse_workflow(
    *,
    name: str,
    user_id: str | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    input_payload: Any | None = None,
) -> Iterator[Any | None]:
    client = get_langfuse_client()
    if client is None:
        yield None
        return

    root_context = None
    propagation_context = None
    root_span = None
    try:
        from langfuse import propagate_attributes

        root_context = client.start_as_current_observation(
            as_type="span",
            name=name,
        )
        root_span = root_context.__enter__()

        update_payload: dict[str, Any] = {}
        if metadata:
            update_payload["metadata"] = metadata
        if settings.LANGFUSE_CAPTURE_IO and input_payload is not None:
            update_payload["input"] = input_payload
        if update_payload:
            root_span.update(**update_payload)

        propagation_context = propagate_attributes(
            trace_name=name,
            user_id=user_id,
            session_id=session_id,
            tags=tags or [],
            metadata=_propagated_metadata(metadata),
        )
        propagation_context.__enter__()
    except Exception as exc:  # pragma: no cover
        logger.warning("Langfuse workflow failed name=%s error=%s", name, exc)
        if propagation_context is not None:
            try:
                propagation_context.__exit__(None, None, None)
            except Exception:
                pass
        if root_context is not None:
            try:
                root_context.__exit__(None, None, None)
            except Exception:
                pass
        yield None
        return

    exc_info = (None, None, None)
    try:
        yield root_span
    except BaseException:
        exc_info = sys.exc_info()
        raise
    finally:
        if propagation_context is not None:
            try:
                propagation_context.__exit__(*exc_info)
            except Exception as exc:  # pragma: no cover
                logger.debug("Langfuse propagation close failed name=%s error=%s", name, exc)
        if root_context is not None:
            try:
                root_context.__exit__(*exc_info)
            except Exception as exc:  # pragma: no cover
                logger.debug("Langfuse workflow close failed name=%s error=%s", name, exc)


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


def _propagated_metadata(metadata: dict[str, Any] | None) -> dict[str, str]:
    clean: dict[str, str] = {}
    for key, value in (metadata or {}).items():
        clean_key = "".join(char for char in str(key) if char.isalnum())
        if not clean_key:
            continue
        clean_value = str(value)
        if len(clean_value) <= 200:
            clean[clean_key] = clean_value
    return clean
