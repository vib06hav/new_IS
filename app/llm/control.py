from __future__ import annotations

import threading
from contextlib import contextmanager

from app.config import settings


class CapacityFullError(RuntimeError):
    def __init__(self, active: int, limit: int) -> None:
        self.active = active
        self.limit = limit
        super().__init__(
            f"Report generation is temporarily at capacity. {active} of {limit} generation slots are currently in use. "
            "Please wait for an active generation to finish and try again."
        )


class GenerationJobLimiter:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._active = 0
        self._lock = threading.Lock()

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {"active": self._active, "limit": self._limit}

    @contextmanager
    def acquire(self):
        with self._lock:
            if self._active >= self._limit:
                raise CapacityFullError(self._active, self._limit)
            self._active += 1
        try:
            yield
        finally:
            with self._lock:
                self._active = max(0, self._active - 1)


generation_job_limiter = GenerationJobLimiter(settings.AICREDITS_GENERATION_MAX_ACTIVE_JOBS)
