"""Auth primitives: password hashing, JWT encoding, token helpers.

Uses HS256 with a shared secret. For production swap `JWT_SECRET` to a long
random value (>= 32 bytes) stored in a secret manager. RS256 key-pair support
can be layered on later without changing call sites — `encode_access_token`
and `decode_token` are the only entry points.
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

TokenKind = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def utcnow() -> datetime:
    return datetime.now(UTC)


def token_expiry(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)


def _encode(
    subject: str,
    tenant_id: UUID,
    kind: TokenKind,
    ttl_seconds: int,
    extra: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = utcnow()
    claims: dict[str, Any] = {
        "sub": subject,
        "tid": str(tenant_id),
        "kind": kind,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl_seconds)).timestamp()),
        "jti": uuid4().hex,
    }
    if extra:
        claims.update(extra)
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def encode_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    s = get_settings()
    return _encode(str(user_id), tenant_id, "access", s.jwt_access_ttl_seconds, {"role": role})


def encode_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    s = get_settings()
    return _encode(str(user_id), tenant_id, "refresh", s.jwt_refresh_ttl_seconds)


def decode_token(token: str, expected_kind: TokenKind | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc
    if expected_kind is not None and claims.get("kind") != expected_kind:
        raise ValueError(f"expected {expected_kind} token, got {claims.get('kind')!r}")
    return claims


def generate_secret_token(num_bytes: int = 32) -> str:
    """Return a URL-safe random token for email invites / password resets."""
    return secrets.token_urlsafe(num_bytes)


def hash_secret_token(token: str) -> str:
    """Stable, fast hash for invite / reset tokens. Not for passwords."""
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
