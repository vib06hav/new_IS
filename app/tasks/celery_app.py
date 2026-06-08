from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.config import settings


def _broker_url() -> str:
    return settings.CELERY_BROKER_URL or "memory://"


def _result_backend() -> str | None:
    if settings.CELERY_RESULT_BACKEND:
        return settings.CELERY_RESULT_BACKEND
    if _broker_url() == "memory://":
        return "cache+memory://"
    return None


celery_app = Celery(
    "ag_interview_standardiser",
    broker=_broker_url(),
    backend=_result_backend(),
    include=[
        "app.tasks.processing",
        "app.tasks.maintenance",
    ],
)

task_exchange = Exchange("agis", type="direct")

celery_app.conf.update(
    task_default_queue=settings.CELERY_QUEUE_DEFAULT,
    task_default_exchange="agis",
    task_default_exchange_type="direct",
    task_default_routing_key=settings.CELERY_QUEUE_DEFAULT,
    task_queues=(
        Queue(settings.CELERY_QUEUE_DEFAULT, task_exchange, routing_key=settings.CELERY_QUEUE_DEFAULT),
        Queue(settings.CELERY_QUEUE_PROCESSING, task_exchange, routing_key=settings.CELERY_QUEUE_PROCESSING),
        Queue(settings.CELERY_QUEUE_GENERATION, task_exchange, routing_key=settings.CELERY_QUEUE_GENERATION),
        Queue(settings.CELERY_QUEUE_MAINTENANCE, task_exchange, routing_key=settings.CELERY_QUEUE_MAINTENANCE),
    ),
    task_routes={
        "app.tasks.processing.run_processing_job_task": {
            "queue": settings.CELERY_QUEUE_PROCESSING,
            "routing_key": settings.CELERY_QUEUE_PROCESSING,
        },
        "app.tasks.maintenance.recover_stale_processing_jobs_task": {
            "queue": settings.CELERY_QUEUE_MAINTENANCE,
            "routing_key": settings.CELERY_QUEUE_MAINTENANCE,
        },
    },
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT_SECONDS,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=settings.CELERY_TASK_EAGER_PROPAGATES,
    broker_connection_retry_on_startup=True,
)
