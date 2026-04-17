"""FastAPI dependencies (auth, tenant scoping, role gates).

These are intentionally stubs in Phase 1. Phase 2 implements JWT validation,
user lookup, and calls `set_current_tenant` on the session before yielding it
back to the route.
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


async def get_session(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncIterator[AsyncSession]:
    yield session


def get_current_user() -> None:  # pragma: no cover — phase 2
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "Auth implemented in Phase 2")


def require_role(*roles: str) -> Callable[[], None]:  # pragma: no cover — phase 2
    def _guard() -> None:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "RBAC implemented in Phase 2")

    return _guard
