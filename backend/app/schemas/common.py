"""Shared request/response primitives."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Message(BaseModel):
    detail: str


class CursorPage(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    next_cursor: str | None = None
