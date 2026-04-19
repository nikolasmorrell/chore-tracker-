"""Document + Extraction + Alert ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin, UUIDPKMixin


class DocumentStatus(str):
    PENDING = "pending"
    OCR = "ocr"
    EXTRACTING = "extracting"
    READY = "ready"
    FAILED = "failed"


class DocumentType(str):
    INSURANCE_CERT = "insurance_cert"
    PERMIT = "permit"
    CONTRACT = "contract"
    LIEN_WAIVER = "lien_waiver"
    OTHER = "other"


class Document(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sha256", name="uq_documents_tenant_sha256"),
        Index("ix_documents_tenant_created", "tenant_id", "created_at"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("pending", "ocr", "extracting", "ready", "failed", name="document_status"),
        nullable=False,
        default="pending",
    )
    doc_type: Mapped[str] = mapped_column(
        Enum(
            "insurance_cert",
            "permit",
            "contract",
            "lien_waiver",
            "other",
            name="document_type",
        ),
        nullable=False,
        default="other",
    )

    extractions: Mapped[list[DocumentExtraction]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    alerts: Mapped[list[Alert]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentExtraction(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "document_extractions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claude_model: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    structured: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))

    document: Mapped[Document] = relationship(back_populates="extractions")


class AlertKind(str):
    EXPIRING_30 = "expiring_30"
    EXPIRING_14 = "expiring_14"
    EXPIRING_7 = "expiring_7"
    EXPIRING_0 = "expiring_0"
    MISSING_FIELD = "missing_field"


class AlertStatus(str):
    SCHEDULED = "scheduled"
    SENT = "sent"
    DISMISSED = "dismissed"


class Alert(UUIDPKMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_due_scheduled", "due_at"),)

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
    )
    kind: Mapped[str] = mapped_column(
        Enum(
            "expiring_30",
            "expiring_14",
            "expiring_7",
            "expiring_0",
            "missing_field",
            name="alert_kind",
        ),
        nullable=False,
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("scheduled", "sent", "dismissed", name="alert_status"),
        nullable=False,
        default="scheduled",
    )
    channel: Mapped[str] = mapped_column(
        Enum("email", "sms", "inapp", name="alert_channel"),
        nullable=False,
        default="email",
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document: Mapped[Document | None] = relationship(back_populates="alerts")
