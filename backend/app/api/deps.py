"""Request-scoped FastAPI dependencies.

Every authenticated route gets a session where Postgres `app.current_tenant`
is bound to the caller's tenant, so RLS filters all reads/writes.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.tenancy import set_current_tenant
from app.db.models.user import User
from app.db.session import SessionLocal


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def _extract_token(
    authorization: str | None,
    access_cookie: str | None,
) -> str:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    if access_cookie:
        return access_cookie
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing access token")


async def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    access_token: Annotated[str | None, Cookie(alias="access_token")] = None,
) -> User:
    token = _extract_token(authorization, access_token)
    try:
        claims = decode_token(token, expected_kind="access")
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    try:
        user_id = UUID(claims["sub"])
        tenant_id = UUID(claims["tid"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "malformed token") from exc

    # Bind RLS *before* the lookup so cross-tenant IDs can't be read via
    # a stolen-but-scoped token.
    await set_current_tenant(session, tenant_id)

    user = await session.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed: str) -> Callable[[User], User]:
    """FastAPI dependency factory that enforces the user's role."""

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient role")
        return user

    return _checker
