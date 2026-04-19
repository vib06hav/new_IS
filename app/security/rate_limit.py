from __future__ import annotations

import threading
import time
from collections import deque
from typing import Protocol

from fastapi import HTTPException, Request, status
try:
    from redis import Redis
    from redis.exceptions import RedisError
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    Redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        """Fallback redis error when the redis package is unavailable."""

from app.config import settings


class RateLimiterBackend(Protocol):
    def clear(self) -> None:
        ...

    def check(self, key: str, *, limit: int, window_seconds: int, detail: str) -> None:
        ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[str, deque[float]] = {}

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()

    def check(self, key: str, *, limit: int, window_seconds: int, detail: str) -> None:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
            bucket.append(now)


class RedisRateLimiter:
    def __init__(self, client: Redis, prefix: str) -> None:
        self._client = client
        self._prefix = prefix

    def clear(self) -> None:
        # Shared Redis keys should not be globally deleted from application code.
        pass

    def check(self, key: str, *, limit: int, window_seconds: int, detail: str) -> None:
        namespaced_key = f"{self._prefix}:ratelimit:{key}"
        try:
            current = int(self._client.incr(namespaced_key))
            if current == 1:
                self._client.expire(namespaced_key, window_seconds)
            if current > limit:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)
        except RedisError as exc:
            raise RuntimeError("redis_rate_limiter_unavailable") from exc


class RateLimiter:
    def __init__(self) -> None:
        self._fallback = InMemoryRateLimiter()
        self._redis_backend: RedisRateLimiter | None = None
        if settings.REDIS_URL and Redis is not None:
            try:
                client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
                    socket_timeout=settings.REDIS_CONNECT_TIMEOUT_SECONDS,
                )
                client.ping()
                self._redis_backend = RedisRateLimiter(client, settings.REDIS_KEY_PREFIX)
            except RedisError:
                self._redis_backend = None
        elif settings.REDIS_URL:
            self._redis_backend = None

    def clear(self) -> None:
        self._fallback.clear()

    def check(self, key: str, *, limit: int, window_seconds: int, detail: str) -> None:
        if self._redis_backend is not None:
            try:
                self._redis_backend.check(
                    key,
                    limit=limit,
                    window_seconds=window_seconds,
                    detail=detail,
                )
                return
            except RuntimeError:
                pass
        self._fallback.check(key, limit=limit, window_seconds=window_seconds, detail=detail)


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    remote_host = request.client.host if request.client and request.client.host else ""
    if settings.TRUST_X_FORWARDED_FOR and remote_host in settings.TRUSTED_PROXY_IPS:
        forwarded_for = request.headers.get("x-forwarded-for", "").strip()
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    if remote_host:
        return remote_host
    return "unknown"
