"""Pure-unit tests (no DB, no network)."""
from __future__ import annotations

from datetime import date

import pytest

from app.services.alerts import _parse_expiration
from app.services.documents import _parse_claude_json, _safe_float


def test_parse_claude_json_plain() -> None:
    assert _parse_claude_json('{"a": 1}') == {"a": 1}


def test_parse_claude_json_fenced() -> None:
    text = """```json
{"expiration_date": "2026-01-01"}
```"""
    assert _parse_claude_json(text) == {"expiration_date": "2026-01-01"}


def test_parse_claude_json_fenced_notag() -> None:
    text = "```\n{\"x\": true}\n```"
    assert _parse_claude_json(text) == {"x": True}


def test_parse_claude_json_invalid() -> None:
    with pytest.raises(ValueError):
        _parse_claude_json("not json")


def test_safe_float_clamps() -> None:
    assert _safe_float(0.5) == 0.5
    assert _safe_float(2.0) == 1.0
    assert _safe_float(-1.0) == 0.0
    assert _safe_float(None) is None
    assert _safe_float("bad") is None


def test_parse_expiration_iso() -> None:
    assert _parse_expiration("2026-12-31") == date(2026, 12, 31)


def test_parse_expiration_bad() -> None:
    assert _parse_expiration("not a date") is None
    assert _parse_expiration(None) is None
    assert _parse_expiration(12345) is None


def test_parse_expiration_passthrough_date() -> None:
    d = date(2027, 6, 1)
    assert _parse_expiration(d) == d
