"""Tenant onboarding: turn a signup payload into a Tenant + owner User.

Kept small on purpose — the HTTP layer composes the transaction, and the rest
of the system (billing trials, invite emails, welcome copy) plugs in via the
services next to this one.
"""
from __future__ import annotations

import re
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password, utcnow
from app.core.tenancy import set_current_tenant
from app.db.models.tenant import Tenant
from app.db.models.user import User

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.lower()).strip("-")
    return slug or "tenant"


async def _unique_slug(session: AsyncSession, base: str) -> str:
    slug = base
    for _ in range(5):
        existing = await session.scalar(select(Tenant.id).where(Tenant.slug == slug))
        if existing is None:
            return slug
        slug = f"{base}-{secrets.token_hex(3)}"
    return f"{base}-{secrets.token_hex(4)}"


async def create_tenant_with_owner(
    session: AsyncSession,
    *,
    company_name: str,
    full_name: str,
    email: str,
    password: str,
) -> tuple[Tenant, User]:
    """Create tenant + owner atomically and start the 14-day trial.

    The caller is responsible for the outer transaction/commit; this function
    flushes but does not commit so the audit log entry can share the txn.
    """
    settings = get_settings()

    base_slug = slugify(company_name)
    slug = await _unique_slug(session, base_slug)

    tenant = Tenant(
        name=company_name.strip(),
        slug=slug,
        plan="trial",
        status="active",
        trial_ends_at=utcnow() + timedelta(days=settings.stripe_trial_days),
    )
    session.add(tenant)
    await session.flush()

    # Bind RLS before inserting anything that carries tenant_id so policies
    # evaluate against the new tenant on the same connection.
    await set_current_tenant(session, tenant.id)

    user = User(
        tenant_id=tenant.id,
        email=email.lower().strip(),
        full_name=full_name.strip(),
        password_hash=hash_password(password),
        role="owner",
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return tenant, user
