"""Document pipeline: OCR → Claude → DocumentExtraction → alerts.

Invoked from the Celery worker. The task gives us a document_id; we hydrate,
run OCR, run Claude, persist an extraction, and hand off to the alert engine.
Designed to be idempotent — re-running the task replays all steps and only
creates a new extraction row (the document row flips status back to `ocr`).
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.tenancy import set_current_tenant
from app.db.models.document import Document, DocumentExtraction
from app.services.alerts import schedule_alerts_for_extraction
from app.services.claude_client import ClaudeClient, prompt_version, render_prompt
from app.services.ocr import extract_text
from app.services.storage import get_object_bytes

logger = logging.getLogger(__name__)


def _parse_claude_json(text: str) -> dict[str, Any]:
    """Claude sometimes wraps JSON in prose/code fences; strip them."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # drop an optional "json" language tag on the first line
        if "\n" in cleaned:
            head, _, rest = cleaned.partition("\n")
            if head.strip().lower() in {"json", ""}:
                cleaned = rest
    try:
        return dict(json.loads(cleaned))
    except json.JSONDecodeError as exc:
        logger.warning("claude.invalid_json", extra={"snippet": cleaned[:200]})
        raise ValueError("Claude did not return valid JSON") from exc


async def process_document(session: AsyncSession, document_id: UUID) -> DocumentExtraction:
    settings = get_settings()

    # Load the document without RLS first so the worker can find any tenant's
    # row, then bind RLS before touching anything else.
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise ValueError(f"document {document_id} not found")

    await set_current_tenant(session, document.tenant_id)
    document.status = "ocr"
    await session.flush()

    file_bytes = await get_object_bytes(settings.s3_bucket_documents, document.s3_key)
    raw_text = await extract_text(file_bytes)

    document.status = "extracting"
    await session.flush()

    prompt = render_prompt("document_extract.j2", raw_text=raw_text or "")
    client = ClaudeClient()
    response = await client.complete(prompt)
    try:
        structured = _parse_claude_json(response.text)
    except ValueError:
        document.status = "failed"
        await session.flush()
        raise

    extraction = DocumentExtraction(
        tenant_id=document.tenant_id,
        document_id=document.id,
        claude_model=response.model,
        prompt_version=prompt_version("document_extract.j2"),
        raw_text=raw_text,
        structured=structured,
        confidence=_safe_float(structured.get("confidence_score")),
    )
    session.add(extraction)
    await session.flush()

    # Propagate structured doc_type when Claude is confident; otherwise leave
    # whatever the uploader picked.
    claude_doc_type = structured.get("doc_type")
    if claude_doc_type in {"insurance_cert", "permit", "contract", "lien_waiver", "other"}:
        document.doc_type = claude_doc_type

    document.status = "ready"
    await session.flush()

    await schedule_alerts_for_extraction(session, document=document, extraction=extraction)
    return extraction


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        return max(0.0, min(1.0, f))
    except (TypeError, ValueError):
        return None
