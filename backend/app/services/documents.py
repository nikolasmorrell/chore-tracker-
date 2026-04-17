"""Document pipeline orchestration (upload → OCR → Claude → alerts)."""
from __future__ import annotations

from uuid import UUID


async def process_document(document_id: UUID) -> None:  # pragma: no cover
    raise NotImplementedError("Document pipeline implemented in Phase 2")
