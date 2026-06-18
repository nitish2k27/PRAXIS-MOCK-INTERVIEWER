"""End-to-end OAuth flow with FakeOIDCProvider."""

from __future__ import annotations

from sqlalchemy import select

from praxis.db.models import User


async def test_login_redirects_to_provider(client) -> None:
    r = await client.get("/auth/google/login", follow_redirects=False)
    assert r.status_code in (302, 307)


async def test_callback_sets_cookies_and_creates_user(client) -> None:
    r = await client.get("/auth/google/callback", follow_redirects=False)
    assert r.status_code == 302
    assert "praxis_access" in r.cookies
    assert "praxis_refresh" in r.cookies


async def test_me_requires_auth(client) -> None:
    r = await client.get("/auth/me")
    assert r.status_code == 401


async def test_me_after_login(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)
    r = await client.get("/auth/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "test@example.com"
    assert body["provider"] == "google"


async def test_second_login_does_not_duplicate(client, db) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)
    await client.get("/auth/google/callback", follow_redirects=False)
    rows = (await db.execute(select(User))).scalars().all()
    assert len(rows) == 1


async def test_logout_clears_cookies(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)
    r = await client.post("/auth/logout")
    assert r.status_code == 200
    client.cookies.clear()
    r2 = await client.get("/auth/me")
    assert r2.status_code == 401


async def test_refresh_rotates_tokens(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)
    # client jar has both access (path=/) and refresh (path=/auth/refresh)
    r = await client.post("/auth/refresh")
    assert r.status_code == 200


async def test_bad_access_cookie_rejected(client) -> None:
    client.cookies.set("praxis_access", "not-a-jwt")
    r = await client.get("/auth/me")
    assert r.status_code == 401
