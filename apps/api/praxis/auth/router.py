"""Auth endpoints: Google login, callback, refresh, logout, me."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from praxis.auth.cookies import REFRESH_COOKIE, clear_auth_cookies, set_auth_cookies
from praxis.auth.deps import get_current_user, get_oidc_provider
from praxis.auth.jwt import TokenError, create_access_token, create_refresh_token, decode_token
from praxis.auth.providers import OIDCProvider
from praxis.config import settings
from praxis.db.models import User
from praxis.db.repositories import UserRepository
from praxis.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login(
    request: Request,
    provider: OIDCProvider = Depends(get_oidc_provider),
) -> Response:
    return await provider.authorize_redirect(request, settings.oauth_redirect_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    provider: OIDCProvider = Depends(get_oidc_provider),
    session: AsyncSession = Depends(get_session),
) -> Response:
    info = await provider.exchange(request)
    repo = UserRepository(session)
    user = await repo.upsert_by_oauth(
        provider=info.provider, sub=info.sub, email=info.email, name=info.name
    )
    await session.commit()
    response = RedirectResponse(url=settings.web_base_url, status_code=302)
    set_auth_cookies(
        response,
        access=create_access_token(user.id),
        refresh=create_refresh_token(user.id),
    )
    return response


@router.post("/refresh")
async def refresh(
    response: Response,
    praxis_refresh: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    if not praxis_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no refresh")
    try:
        payload = decode_token(praxis_refresh, "refresh")
    except TokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    repo = UserRepository(session)
    user = await repo.get_by_id(payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    set_auth_cookies(
        response,
        access=create_access_token(user.id),
        refresh=create_refresh_token(user.id),
    )
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response) -> dict[str, Any]:
    clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "provider": user.oauth_provider,
    }
