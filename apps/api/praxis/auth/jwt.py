"""JWT issue/verify helpers. Tokens are app-issued; provider tokens never leave the server."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt

from praxis.config import settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(sub: str) -> str:
    expire = _now() + timedelta(minutes=settings.access_token_ttl_min)
    payload = {"sub": sub, "typ": "access", "exp": expire, "iat": _now()}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_refresh_token(sub: str) -> str:
    expire = _now() + timedelta(days=settings.refresh_token_ttl_days)
    payload = {"sub": sub, "typ": "refresh", "exp": expire, "iat": _now()}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str, expected_typ: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError as e:
        raise TokenError(f"invalid token: {e}") from e
    if payload.get("typ") != expected_typ:
        raise TokenError(f"expected typ={expected_typ}, got {payload.get('typ')}")
    if not isinstance(payload.get("sub"), str):
        raise TokenError("missing sub")
    return payload
