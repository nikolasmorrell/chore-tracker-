"""tenants.twilio_phone_number

Revision ID: 0003_tenant_twilio_number
Revises: 0002_password_reset
Create Date: 2026-04-18 00:00:01
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_tenant_twilio_number"
down_revision: str | None = "0002_password_reset"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("twilio_phone_number", sa.String(length=40), nullable=True),
    )
    op.create_unique_constraint(
        "uq_tenants_twilio_phone_number", "tenants", ["twilio_phone_number"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_tenants_twilio_phone_number", "tenants", type_="unique")
    op.drop_column("tenants", "twilio_phone_number")
