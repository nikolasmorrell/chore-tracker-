"""Document upload + extraction routes.

Upload is a two-step dance: client calls `POST /documents` with file metadata,
we return a presigned S3 POST, client uploads directly to S3, then hits
`POST /documents/{id}/confirm` to trigger the extraction pipeline.

The pipeline runs in Celery so the HTTP request stays sub-second even when
OCR/Claude are slow. Status transitions: pending → ocr → extracting → ready.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.db.models.document import Document, DocumentExtraction
from app.schemas.common import CursorPage, Message
from app.schemas.document import (
    DocumentExtractionRead,
    DocumentRead,
    DocumentStatus,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.services import audit
from app.services.storage import build_document_key, presigned_get, presigned_post

router = APIRouter()


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve a document slot and return a presigned upload URL",
)
async def create_document(
    payload: DocumentUploadRequest,
    session: SessionDep,
    user: CurrentUser,
) -> DocumentUploadResponse:
    settings = get_settings()

    existing = await session.scalar(
        select(Document).where(Document.sha256 == payload.sha256)
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "document already uploaded")

    key = build_document_key(str(user.tenant_id), payload.filename)
    document = Document(
        tenant_id=user.tenant_id,
        customer_id=payload.customer_id,
        uploaded_by=user.id,
        s3_key=key,
        original_filename=payload.filename,
        mime_type=payload.mime_type,
        size_bytes=payload.size_bytes,
        sha256=payload.sha256,
        status="pending",
        doc_type=payload.doc_type,
    )
    session.add(document)
    await session.flush()

    contract = await presigned_post(
        settings.s3_bucket_documents,
        key,
        content_type=payload.mime_type,
        max_bytes=payload.size_bytes,
    )

    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="document.created",
        entity_type="document",
        entity_id=document.id,
        extra={"doc_type": payload.doc_type, "size_bytes": payload.size_bytes},
    )
    await session.commit()

    return DocumentUploadResponse(
        document_id=document.id,
        upload_url=contract["url"],
        fields=contract["fields"],
    )


@router.post(
    "/{document_id}/confirm",
    response_model=DocumentRead,
    summary="Confirm the upload completed and enqueue extraction",
)
async def confirm_upload(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> DocumentRead:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    if document.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, f"document status is {document.status}")

    document.status = "ocr"
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="document.confirmed",
        entity_type="document",
        entity_id=document.id,
    )
    await session.commit()

    # Import here to avoid Celery at import time in test envs.
    from app.workers.tasks.documents import extract_document

    extract_document.delay(str(document.id))
    return DocumentRead.model_validate(document)


@router.get("", response_model=CursorPage[DocumentRead], summary="List documents")
async def list_documents(
    session: SessionDep,
    user: CurrentUser,
    status_filter: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> CursorPage[DocumentRead]:
    stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
    if status_filter is not None:
        stmt = stmt.where(Document.status == status_filter)
    rows = (await session.scalars(stmt)).all()
    return CursorPage[DocumentRead](items=[DocumentRead.model_validate(r) for r in rows])


@router.get(
    "/{document_id}",
    response_model=DocumentRead,
    summary="Fetch a document with its latest extraction",
)
async def get_document(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> DocumentRead:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    return DocumentRead.model_validate(document)


@router.get(
    "/{document_id}/download",
    response_model=Message,
    summary="Return a short-lived download URL",
)
async def download_document(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> Message:
    settings = get_settings()
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    url = await presigned_get(settings.s3_bucket_documents, document.s3_key)
    return Message(detail=url)


@router.get(
    "/{document_id}/extractions",
    response_model=list[DocumentExtractionRead],
    summary="All extractions for a document (most recent first)",
)
async def list_extractions(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> list[DocumentExtractionRead]:
    rows = (
        await session.scalars(
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document_id)
            .order_by(DocumentExtraction.created_at.desc())
        )
    ).all()
    return [DocumentExtractionRead.model_validate(r) for r in rows]


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentRead,
    summary="Re-run OCR + Claude extraction",
    dependencies=[Depends(lambda: None)],
)
async def reprocess_document(
    document_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> DocumentRead:
    document = await session.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "document not found")
    document.status = "ocr"
    await session.flush()
    await audit.record(
        session,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="document.reprocess",
        entity_type="document",
        entity_id=document.id,
    )
    await session.commit()

    from app.workers.tasks.documents import extract_document

    extract_document.delay(str(document.id))
    return DocumentRead.model_validate(document)
