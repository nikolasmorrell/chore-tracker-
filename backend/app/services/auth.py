"""Auth business logic: login, refresh, password reset.

The HTTP layer in `api.v1.auth` stays thin — it validates payloads, calls
these functions, and attaches cookies. Everything here is deterministic and
test-friendly.
"""
from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    encode_access_token,
    encode_refresh_token,
    generate_secret_token,
    hash_password,
    hash_secret_token,
    utcnow,
    verify_password,
)
from app.core.tenancy import set_current_tenant
from app.db.models.password_reset import PasswordResetToken
from app.db.models.user import User


class AuthError(Exception):
    """Raised for auth failures the HTTP layer should translate to 401."""


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    """Return the active user for email+password, or raise AuthError.

    Email is unique per tenant, not global, so we look it up without the RLS
    GUC bound. The query includes `is_active=True` so disabled accounts fail
    the same way as wrong passwords.
    """
    normalized = email.lower().strip()
    user = await session.scalar(
        select(User).where(User.email == normalized, User.is_active.is_(True))
    )
    if user is None:
        # Still hash to avoid timing oracle on user-existence.
        hash_password(password)
        raise AuthError("invalid credentials")
    if not verify_password(password, user.password_hash):
        raise AuthError("invalid credentials")
    user.last_login_at = utcnow()
    await session.flush()
    return user


def issue_tokens(user: User) -> tuple[str, str, int]:
    """Return (access_token, refresh_token, access_expires_in_seconds)."""
    settings = get_settings()
    access = encode_access_token(user.id, user.tenant_id, user.role)
    refresh = encode_refresh_token(user.id, user.tenant_id)
    return access, refresh, settings.jwt_access_ttl_seconds


async def rotate_refresh(session: AsyncSession, *, user_id: UUID, tenant_id: UUID) -> User:
    """Look up the user for a valid refresh token. Caller already decoded the JWT."""
    await set_current_tenant(session, tenant_id)
    user = await session.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    if user is None:
        raise AuthError("user not found")
    return user


async def create_password_reset(session: AsyncSession, email: str) -> tuple[str, User] | None:
    """Create a single-use reset token. Returns (plaintext_token, user) or None.

    Returning None for unknown emails keeps the endpoint a no-op from the
    caller's perspective so enumeration is not possible.
    """
    settings = get_settings()
    normalized = email.lower().strip()
    user = await session.scalar(
        select(User).where(User.email == normalized, User.is_active.is_(True))
    )
    if user is None:
        return None

    await set_current_tenant(session, user.tenant_id)
    plaintext = generate_secret_token()
    token = PasswordResetToken(
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=hash_secret_token(plaintext),
        expires_at=utcnow() + timedelta(seconds=settings.password_reset_ttl_seconds),
    )
    session.add(token)
    await session.flush()
    return plaintext, user


async def consume_password_reset(
    session: AsyncSession, *, plaintext: str, new_password: str
) -> User:
    """Verify a reset token, rotate the password, mark the token used."""
    token_hash = hash_secret_token(plaintext)
    token = await session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if token is None or token.used_at is not None or token.expires_at < utcnow():
        raise AuthError("invalid or expired token")

    await set_current_tenant(session, token.tenant_id)
    user = await session.scalar(select(User).where(User.id == token.user_id))
    if user is None or not user.is_active:
        raise AuthError("user not found")

    user.password_hash = hash_password(new_password)
    token.used_at = utcnow()
    await session.flush()
    return user
