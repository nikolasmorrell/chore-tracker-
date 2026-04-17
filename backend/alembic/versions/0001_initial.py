"""initial schema with tenant RLS

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-17 00:00:00
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Tables that are scoped to a tenant and must enforce RLS.
TENANT_TABLES: tuple[str, ...] = (
    "users",
    "invites",
    "customers",
    "documents",
    "document_extractions",
    "alerts",
    "calls",
    "call_turns",
    "tasks",
    "audit_logs",
    "subscriptions",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    # Enums --------------------------------------------------------------
    tenant_plan = postgresql.ENUM(
        "trial", "starter", "pro", "enterprise", name="tenant_plan"
    )
    tenant_status = postgresql.ENUM(
        "active", "past_due", "canceled", "suspended", name="tenant_status"
    )
    user_role = postgresql.ENUM("owner", "admin", "staff", name="user_role")
    document_status = postgresql.ENUM(
        "pending", "ocr", "extracting", "ready", "failed", name="document_status"
    )
    document_type = postgresql.ENUM(
        "insurance_cert", "permit", "contract", "lien_waiver", "other", name="document_type"
    )
    alert_kind = postgresql.ENUM(
        "expiring_30",
        "expiring_14",
        "expiring_7",
        "expiring_0",
        "missing_field",
        name="alert_kind",
    )
    alert_status = postgresql.ENUM("scheduled", "sent", "dismissed", name="alert_status")
    alert_channel = postgresql.ENUM("email", "sms", "inapp", name="alert_channel")
    call_direction = postgresql.ENUM("inbound", "outbound", name="call_direction")
    call_speaker = postgresql.ENUM("caller", "assistant", name="call_speaker")
    task_source = postgresql.ENUM(
        "document", "call", "manual", "alert", name="task_source"
    )
    task_priority = postgresql.ENUM(
        "low", "normal", "high", "urgent", name="task_priority"
    )
    task_status = postgresql.ENUM(
        "open", "in_progress", "done", "cancelled", name="task_status"
    )

    bind = op.get_bind()
    for enum in (
        tenant_plan,
        tenant_status,
        user_role,
        document_status,
        document_type,
        alert_kind,
        alert_status,
        alert_channel,
        call_direction,
        call_speaker,
        task_source,
        task_priority,
        task_status,
    ):
        enum.create(bind, checkfirst=True)

    # tenants ------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column(
            "plan",
            postgresql.ENUM(name="tenant_plan", create_type=False),
            nullable=False,
            server_default="trial",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="tenant_status", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True)),
        sa.Column("stripe_customer_id", sa.String(120), unique=True),
        sa.Column("stripe_subscription_id", sa.String(120), unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # users --------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM(name="user_role", create_type=False), nullable=False, server_default="staff"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    # invites ------------------------------------------------------------
    op.create_table(
        "invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email", sa.String(254), nullable=False, index=True),
        sa.Column("role", postgresql.ENUM(name="user_role", create_type=False), nullable=False, server_default="staff"),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # customers ----------------------------------------------------------
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(40), index=True),
        sa.Column("email", sa.String(254), index=True),
        sa.Column("address", postgresql.JSONB),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # documents ----------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, index=True),
        sa.Column("status", postgresql.ENUM(name="document_status", create_type=False), nullable=False, server_default="pending"),
        sa.Column("doc_type", postgresql.ENUM(name="document_type", create_type=False), nullable=False, server_default="other"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "sha256", name="uq_documents_tenant_sha256"),
    )
    op.create_index("ix_documents_tenant_created", "documents", ["tenant_id", "created_at"])

    # document_extractions ----------------------------------------------
    op.create_table(
        "document_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("claude_model", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(40), nullable=False),
        sa.Column("raw_text", sa.Text),
        sa.Column("structured", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Numeric(3, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # alerts -------------------------------------------------------------
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("kind", postgresql.ENUM(name="alert_kind", create_type=False), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", postgresql.ENUM(name="alert_status", create_type=False), nullable=False, server_default="scheduled"),
        sa.Column("channel", postgresql.ENUM(name="alert_channel", create_type=False), nullable=False, server_default="email"),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_alerts_due_scheduled",
        "alerts",
        ["due_at"],
        postgresql_where=sa.text("status = 'scheduled'"),
    )

    # calls --------------------------------------------------------------
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("twilio_call_sid", sa.String(64), nullable=False, unique=True),
        sa.Column("from_number", sa.String(40), nullable=False),
        sa.Column("to_number", sa.String(40), nullable=False),
        sa.Column("direction", postgresql.ENUM(name="call_direction", create_type=False), nullable=False, server_default="inbound"),
        sa.Column("status", sa.String(40), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("recording_url", sa.String(500)),
        sa.Column("summary", sa.Text),
        sa.Column("intent", sa.String(80)),
        sa.Column("transferred_to", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # call_turns ---------------------------------------------------------
    op.create_table(
        "call_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("speaker", postgresql.ENUM(name="call_speaker", create_type=False), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("audio_key", sa.String(500)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # tasks --------------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("source", postgresql.ENUM(name="task_source", create_type=False), nullable=False, server_default="manual"),
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("priority", postgresql.ENUM(name="task_priority", create_type=False), nullable=False, server_default="normal"),
        sa.Column("status", postgresql.ENUM(name="task_status", create_type=False), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # subscriptions ------------------------------------------------------
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("stripe_subscription_id", sa.String(120), nullable=False, unique=True),
        sa.Column("price_id", sa.String(120), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # audit_logs ---------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(80), nullable=False, index=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("extra", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("ip", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Row-Level Security -------------------------------------------------
    # Every tenant table: enable RLS and add a policy that matches rows to
    # `current_setting('app.current_tenant')`. When the GUC is unset the
    # policy evaluates to false, so a forgotten `set_current_tenant` call
    # returns zero rows instead of leaking data.
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)
            """
        )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")

    op.drop_table("audit_logs")
    op.drop_table("subscriptions")
    op.drop_table("tasks")
    op.drop_table("call_turns")
    op.drop_table("calls")
    op.drop_index("ix_alerts_due_scheduled", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("document_extractions")
    op.drop_index("ix_documents_tenant_created", table_name="documents")
    op.drop_table("documents")
    op.drop_table("customers")
    op.drop_table("invites")
    op.drop_table("users")
    op.drop_table("tenants")

    for enum_name in (
        "task_status",
        "task_priority",
        "task_source",
        "call_speaker",
        "call_direction",
        "alert_channel",
        "alert_status",
        "alert_kind",
        "document_type",
        "document_status",
        "user_role",
        "tenant_status",
        "tenant_plan",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
