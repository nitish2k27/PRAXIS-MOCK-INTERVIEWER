"""OIDC provider adapter + deterministic fake for tests.

Per the project non-negotiable: nothing outside this module imports Authlib.
The router and deps only see the `OIDCProvider` Protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from praxis.config import settings


@dataclass(frozen=True)
class UserInfo:
    sub: str
    email: str
    name: str | None
    provider: str


class OIDCProvider(Protocol):
    name: str

    async def authorize_redirect(self, request: Request, redirect_uri: str) -> Response: ...

    async def exchange(self, request: Request) -> UserInfo: ...


class GoogleOIDCProvider:
    """Real Google OIDC via Authlib. Configure via GOOGLE_CLIENT_ID/SECRET."""

    name = "google"

    def __init__(self) -> None:
        self._oauth = OAuth()
        self._oauth.register(
            name="google",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            server_metadata_url=("https://accounts.google.com/.well-known/openid-configuration"),
            client_kwargs={"scope": "openid email profile"},
        )

    async def authorize_redirect(self, request: Request, redirect_uri: str) -> Response:
        result: Response = await self._oauth.google.authorize_redirect(request, redirect_uri)
        return result

    async def exchange(self, request: Request) -> UserInfo:
        token: dict[str, Any] = await self._oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo") or await self._oauth.google.userinfo(token=token)
        return UserInfo(
            sub=str(userinfo["sub"]),
            email=str(userinfo["email"]),
            name=userinfo.get("name"),
            provider="google",
        )


class FakeOIDCProvider:
    """Deterministic in-process provider for tests. Never touches the network."""

    name = "google"

    def __init__(
        self,
        sub: str = "fake-sub-1",
        email: str = "test@example.com",
        name: str | None = "Test User",
    ) -> None:
        self.userinfo = UserInfo(sub=sub, email=email, name=name, provider="google")

    async def authorize_redirect(self, request: Request, redirect_uri: str) -> Response:
        return RedirectResponse(
            url=f"{redirect_uri}?code=fake-code&state=fake-state",
            status_code=302,
        )

    async def exchange(self, request: Request) -> UserInfo:
        return self.userinfo
