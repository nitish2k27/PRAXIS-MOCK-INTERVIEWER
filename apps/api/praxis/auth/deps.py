"""FastAPI dependencies: OIDC provider injection + route guard."""

from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.cookies import ACCESS_COOKIE
from praxis.auth.jwt import TokenError, decode_token
from praxis.auth.providers import GoogleOIDCProvider, OIDCProvider
from praxis.db.models import User
from praxis.db.repositories import UserRepository
from praxis.db.session import get_session

_provider: OIDCProvider | None = None


def get_oidc_provider() -> OIDCProvider:
    """Singleton OIDC provider. Tests override via `app.dependency_overrides`."""
    global _provider
    if _provider is None:
        _provider = GoogleOIDCProvider()
    return _provider


async def get_current_user(
    praxis_access: str | None = Cookie(default=None, alias=ACCESS_COOKIE),
    session: AsyncSession = Depends(get_session),
) -> User:
    if not praxis_access:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    try:
        payload = decode_token(praxis_access, "access")
    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    repo = UserRepository(session)
    user = await repo.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user
