"""Celery tasks for the document pipeline."""
from __future__ import annotations

from app.workers.celery_app import celery


@celery.task(name="documents.extract", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def extract_document(self, document_id: str) -> None:  # noqa: ARG001 pragma: no cover
    raise NotImplementedError("Wired in Phase 2")
