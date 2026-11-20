from celery import Celery
from datetime import timedelta
from src.config.settings import settings

celery_app = Celery(
    "deal_hunter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat Schedule. The task is a safe no-op while Flipkart is disabled.
celery_app.conf.beat_schedule = {
    "collect-flipkart-category-feeds": {
        "task": "collect_flipkart_updates",
        "schedule": timedelta(minutes=settings.FLIPKART_SYNC_INTERVAL_MINUTES),
    }
}

# This will be imported in the worker
import src.workers.tasks
