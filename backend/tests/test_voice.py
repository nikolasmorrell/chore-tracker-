"""Unit tests for Phase 3 voice helpers (no DB, no network)."""
from __future__ import annotations

from app.services.twilio_verify import compute_signature
from app.services.voice import _parse_reply
from app.workers.tasks.calls import _parse_summary


def test_twilio_signature_matches_known_vector() -> None:
    # Sample adapted from Twilio docs: signature is deterministic given
    # (auth_token, url, sorted params).
    token = "12345"
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {"CallSid": "CA123", "From": "+15551230000", "To": "+15559990000"}
    sig = compute_signature(token, url, params)
    # Recompute independently in the test to pin the algorithm
    import base64
    import hashlib
    import hmac

    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    expected = base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode("ascii")
    assert sig == expected


def test_parse_reply_plain_json() -> None:
    decision = _parse_reply(
        '{"reply_text": "Hi", "intent": "schedule", "transfer": false, "end_call": false}'
    )
    assert decision["reply_text"] == "Hi"
    assert decision["intent"] == "schedule"
    assert decision["transfer"] is False


def test_parse_reply_fenced() -> None:
    text = '```json\n{"reply_text": "Sure", "intent": "hours"}\n```'
    decision = _parse_reply(text)
    assert decision["reply_text"] == "Sure"


def test_parse_reply_falls_back_on_garbage() -> None:
    decision = _parse_reply("not json at all")
    assert "reply_text" in decision
    assert decision["end_call"] is False


def test_parse_summary_fenced() -> None:
    text = '```json\n{"summary": "Caller wants a quote", "intent": "schedule", "action_items": []}\n```'
    parsed = _parse_summary(text)
    assert parsed["summary"].startswith("Caller")
    assert parsed["action_items"] == []


def test_parse_summary_garbage_returns_snippet() -> None:
    parsed = _parse_summary("not parseable")
    assert "summary" in parsed
    assert parsed["action_items"] == []
