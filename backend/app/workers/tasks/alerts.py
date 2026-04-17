"""Celery tasks for alert scheduling + delivery."""
from __future__ import annotations

from app.workers.celery_app import celery


@celery.task(name="alerts.dispatch_due")
def dispatch_due_alerts() -> None:  # pragma: no cover
    raise NotImplementedError("Wired in Phase 2")
