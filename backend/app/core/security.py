"""Auth primitives: password hashing + JWT encode/decode.

Implementation is intentionally minimal in Phase 1 — routes are stubs.
Phase 2 wires these into the auth router.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def utcnow() -> datetime:
    return datetime.now(UTC)


def token_expiry(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)


# JWT encode/decode implemented in Phase 2 (needs RS256 key loading).
def encode_jwt(claims: dict[str, Any]) -> str:  # pragma: no cover — phase 2
    raise NotImplementedError("JWT signing is implemented in Phase 2")


def decode_jwt(token: str) -> dict[str, Any]:  # pragma: no cover — phase 2
    raise NotImplementedError("JWT verification is implemented in Phase 2")
