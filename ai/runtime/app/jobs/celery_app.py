from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_service",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.jobs.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300, # 5 min hard limit
)


def active_mathvision_workers(timeout: float = 1.0) -> list[str]:
    """A Redis connection alone cannot prove arithmetic jobs will be processed."""
    replies = celery_app.control.ping(timeout=timeout)
    return [name for reply in replies for name, value in reply.items()
            if name.startswith("mathvision@") and value.get("ok") == "pong"]
