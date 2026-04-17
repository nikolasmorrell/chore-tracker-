"""Claude API wrapper.

Phase 2 adds retry, prompt-version tagging, and structured-output helpers.
This stub exists so other modules can import the interface today.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ClaudeResponse:
    text: str
    model: str
    usage_input_tokens: int
    usage_output_tokens: int


class ClaudeClient:
    async def complete(self, prompt: str, *, model: str | None = None) -> ClaudeResponse:  # pragma: no cover
        raise NotImplementedError("Claude client implemented in Phase 2")
