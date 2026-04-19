from __future__ import annotations

import logging

from app.config import settings
from app.processing import run_worker_forever

logging.getLogger().setLevel(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting dedicated processing worker")
    run_worker_forever(poll_seconds=settings.PROCESSING_WORKER_POLL_SECONDS)


if __name__ == "__main__":
    main()
