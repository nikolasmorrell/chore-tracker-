"""Claude API wrapper with prompt-version tagging and bounded retries.

Thin by design: a single `complete` entry point that callers wrap in whatever
domain logic they need. Uses the async `AsyncAnthropic` client and applies
jittered exponential backoff on transient errors.
"""
from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass
from pathlib import Path

from anthropic import APIError, APIStatusError, AsyncAnthropic
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings

logger = logging.getLogger(__name__)

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_VERSION_RE = re.compile(r"version:\s*(v\d+)")


@dataclass
class ClaudeResponse:
    text: str
    model: str
    usage_input_tokens: int
    usage_output_tokens: int


_env = Environment(
    loader=FileSystemLoader(PROMPT_DIR),
    autoescape=select_autoescape(enabled_extensions=()),
    keep_trailing_newline=True,
)


def render_prompt(name: str, **ctx: object) -> str:
    template = _env.get_template(name)
    return template.render(**ctx)


def prompt_version(name: str) -> str:
    """Read the `{# version: vN #}` comment from a prompt file.

    Falls back to "v0" if no version marker is present. Pinning the version in
    the DB row lets us replay old extractions later without confusion.
    """
    path = PROMPT_DIR / name
    if not path.exists():
        return "v0"
    first_line = path.read_text(encoding="utf-8").splitlines()[:1]
    if not first_line:
        return "v0"
    match = _VERSION_RE.search(first_line[0])
    return match.group(1) if match else "v0"


class ClaudeClient:
    def __init__(self, *, api_key: str | None = None, max_retries: int = 3) -> None:
        settings = get_settings()
        self._client = AsyncAnthropic(api_key=api_key or settings.anthropic_api_key or None)
        self._max_retries = max_retries

    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        system: str | None = None,
    ) -> ClaudeResponse:
        settings = get_settings()
        chosen_model = model or settings.claude_model_primary
        max_out = max_tokens or settings.claude_max_output_tokens

        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                message = await self._client.messages.create(
                    model=chosen_model,
                    max_tokens=max_out,
                    system=system or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": prompt}],
                )
                text_parts = [
                    block.text for block in message.content if getattr(block, "type", None) == "text"
                ]
                return ClaudeResponse(
                    text="".join(text_parts),
                    model=message.model,
                    usage_input_tokens=message.usage.input_tokens,
                    usage_output_tokens=message.usage.output_tokens,
                )
            except APIStatusError as exc:
                # 4xx: don't retry unless it's a rate limit.
                if exc.status_code == 429:
                    last_err = exc
                else:
                    raise
            except APIError as exc:
                last_err = exc
            # Exponential backoff with jitter: 0.5s, 1s, 2s base.
            import anyio

            delay = (2**attempt) * 0.5 + random.uniform(0, 0.25)
            logger.warning("claude.retry", extra={"attempt": attempt, "delay": delay})
            await anyio.sleep(delay)

        assert last_err is not None
        raise last_err
