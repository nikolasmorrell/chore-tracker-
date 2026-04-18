"""Document / extraction / alert DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DocumentStatus = Literal["pending", "ocr", "extracting", "ready", "failed"]
DocumentType = Literal["insurance_cert", "permit", "contract", "lien_waiver", "other"]


class DocumentUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=120)
    size_bytes: int = Field(gt=0, le=50 * 1024 * 1024)  # 50 MB cap
    sha256: str = Field(min_length=64, max_length=64)
    doc_type: DocumentType = "other"
    customer_id: UUID | None = None


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    upload_url: str
    fields: dict[str, str] = Field(default_factory=dict)
    """Fields to include with multipart form POST (presigned POST contract)."""


class DocumentExtractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    claude_model: str
    prompt_version: str
    structured: dict[str, Any]
    confidence: float | None
    created_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    customer_id: UUID | None
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    status: DocumentStatus
    doc_type: DocumentType
    created_at: datetime
    updated_at: datetime


AlertKind = Literal["expiring_30", "expiring_14", "expiring_7", "expiring_0", "missing_field"]
AlertStatus = Literal["scheduled", "sent", "dismissed"]
AlertChannel = Literal["email", "sms", "inapp"]


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    document_id: UUID | None
    kind: AlertKind
    status: AlertStatus
    channel: AlertChannel
    due_at: datetime
    sent_at: datetime | None
    created_at: datetime
