"""JWT issue/decode/expiry/type-mismatch."""

from __future__ import annotations

import time

import pytest

from praxis.auth.jwt import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from praxis.config import settings


def test_access_token_roundtrip() -> None:
    tok = create_access_token("user-1")
    payload = decode_token(tok, "access")
    assert payload["sub"] == "user-1"
    assert payload["typ"] == "access"


def test_refresh_token_roundtrip() -> None:
    tok = create_refresh_token("user-1")
    payload = decode_token(tok, "refresh")
    assert payload["typ"] == "refresh"


def test_type_mismatch_rejected() -> None:
    tok = create_access_token("user-1")
    with pytest.raises(TokenError):
        decode_token(tok, "refresh")


def test_bad_signature_rejected() -> None:
    tok = create_access_token("user-1") + "x"
    with pytest.raises(TokenError):
        decode_token(tok, "access")


def test_expired_token_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "access_token_ttl_min", 0)
    tok = create_access_token("user-1")
    time.sleep(1.1)
    with pytest.raises(TokenError):
        decode_token(tok, "access")
