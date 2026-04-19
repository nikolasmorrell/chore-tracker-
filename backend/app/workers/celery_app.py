"""Celery application.

Broker + result backend come from settings; task modules are auto-discovered
from app.workers.tasks.*.
"""
from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery = Celery(
    "serva",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[
        "app.workers.tasks.documents",
        "app.workers.tasks.alerts",
        "app.workers.tasks.calls",
        "app.workers.tasks.notifications",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "dispatch-due-alerts": {
            "task": "alerts.dispatch_due",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
