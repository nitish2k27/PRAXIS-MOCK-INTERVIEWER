"""Auth cookie helpers — httpOnly, Secure, SameSite as required by docs/02."""

from __future__ import annotations

from typing import Literal, cast

from fastapi import Response

from praxis.config import settings

ACCESS_COOKIE = "praxis_access"
REFRESH_COOKIE = "praxis_refresh"
REFRESH_PATH = "/auth/refresh"


def _samesite() -> Literal["lax", "strict", "none"]:
    return cast(Literal["lax", "strict", "none"], settings.cookie_samesite.lower())


def set_auth_cookies(response: Response, *, access: str, refresh: str) -> None:
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access,
        max_age=settings.access_token_ttl_min * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=_samesite(),
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh,
        max_age=settings.refresh_token_ttl_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=_samesite(),
        domain=settings.cookie_domain,
        path=REFRESH_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/", domain=settings.cookie_domain)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH, domain=settings.cookie_domain)
