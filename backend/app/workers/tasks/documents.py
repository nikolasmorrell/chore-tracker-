"""Celery tasks for the document pipeline."""
from __future__ import annotations

import asyncio
from uuid import UUID

from app.db.session import SessionLocal
from app.services.documents import process_document
from app.workers.celery_app import celery


async def _run(document_id: str) -> None:
    async with SessionLocal() as session:
        try:
            await process_document(session, UUID(document_id))
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@celery.task(
    name="documents.extract",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def extract_document(self: object, document_id: str) -> None:
    asyncio.run(_run(document_id))
