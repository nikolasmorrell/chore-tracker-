"""Document upload + extraction routes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("", summary="Upload a document (PDF/image) for extraction", status_code=status.HTTP_201_CREATED)
async def upload_document() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.get("", summary="List documents with status filters")
async def list_documents() -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.get("/{document_id}", summary="Fetch a document with its latest extraction")
async def get_document(document_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")


@router.post("/{document_id}/reprocess", summary="Re-run OCR + Claude extraction")
async def reprocess_document(document_id: UUID) -> None:  # noqa: ARG001
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Phase 2")
