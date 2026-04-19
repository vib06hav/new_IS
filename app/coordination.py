from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

try:
    from redis import Redis
    from redis.exceptions import RedisError
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    Redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        """Fallback redis error when the redis package is unavailable."""

from app.config import settings

logger = logging.getLogger(__name__)


class LockNotAcquiredError(RuntimeError):
    """Raised when a non-blocking coordination lock cannot be acquired."""


class BaseLockBackend:
    def clear(self) -> None:  # pragma: no cover - interface only
        raise NotImplementedError

    @contextmanager
    def acquire(self, key: str, timeout_seconds: float, blocking_timeout: float = 0.0) -> Iterator[None]:
        raise NotImplementedError


class InMemoryLockBackend(BaseLockBackend):
    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def clear(self) -> None:
        with self._guard:
            self._locks = {}

    def _get_lock(self, key: str) -> threading.Lock:
        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock

    @contextmanager
    def acquire(self, key: str, timeout_seconds: float, blocking_timeout: float = 0.0) -> Iterator[None]:
        lock = self._get_lock(key)
        acquired = lock.acquire(timeout=max(0.0, blocking_timeout))
        if not acquired:
            raise LockNotAcquiredError(key)
        try:
            yield
        finally:
            lock.release()


class RedisLockBackend(BaseLockBackend):
    def __init__(self, client: Redis, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    def clear(self) -> None:
        # Shared Redis state should not be globally flushed from application code.
        pass

    @contextmanager
    def acquire(self, key: str, timeout_seconds: float, blocking_timeout: float = 0.0) -> Iterator[None]:
        lock = self._client.lock(
            f"{self._prefix}:lock:{key}",
            timeout=max(1, int(timeout_seconds)),
            blocking_timeout=max(0.0, blocking_timeout),
        )
        acquired = False
        try:
            acquired = bool(lock.acquire())
        except RedisError as exc:  # pragma: no cover - exercised only with real Redis failures
            logger.warning("Redis lock acquisition failed for %s; falling back to local coordination: %s", key, exc)
            raise LockNotAcquiredError(key) from exc
        if not acquired:
            raise LockNotAcquiredError(key)
        try:
            yield
        finally:
            try:
                lock.release()
            except RedisError:  # pragma: no cover - defensive cleanup
                logger.warning("Redis lock release failed for %s", key, exc_info=True)


class CoordinationManager:
    def __init__(self, prefix: str, redis_url: str) -> None:
        self._prefix = prefix
        self._fallback_backend = InMemoryLockBackend()
        self._redis_backend: RedisLockBackend | None = None
        if redis_url and Redis is not None:
            try:
                client = Redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
                    socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
                )
                client.ping()
                self._redis_backend = RedisLockBackend(client, prefix)
                logger.info("Redis coordination enabled")
            except RedisError:
                logger.warning("Redis unavailable at startup; using in-memory coordination fallback", exc_info=True)
        elif redis_url:
            logger.warning("REDIS_URL is configured but the redis package is not installed; using in-memory coordination fallback")

    def clear(self) -> None:
        self._fallback_backend.clear()

    @property
    def uses_redis(self) -> bool:
        return self._redis_backend is not None

    @contextmanager
    def acquire(self, key: str, timeout_seconds: float, blocking_timeout: float = 0.0) -> Iterator[None]:
        namespaced_key = f"{self._prefix}:{key}"
        if self._redis_backend is not None:
            try:
                with self._redis_backend.acquire(
                    namespaced_key,
                    timeout_seconds=timeout_seconds,
                    blocking_timeout=blocking_timeout,
                ):
                    yield
                    return
            except LockNotAcquiredError:
                raise
            except Exception:  # pragma: no cover - defensive fallback path
                logger.warning("Redis coordination failed for %s; falling back to in-memory lock", namespaced_key, exc_info=True)
        with self._fallback_backend.acquire(
            namespaced_key,
            timeout_seconds=timeout_seconds,
            blocking_timeout=blocking_timeout,
        ):
            yield


@lru_cache(maxsize=1)
def get_coordination_manager() -> CoordinationManager:
    return CoordinationManager(settings.REDIS_KEY_PREFIX, settings.REDIS_URL)
