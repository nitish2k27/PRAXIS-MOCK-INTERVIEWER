"""Dashboard sessions list."""

from __future__ import annotations


async def test_sessions_requires_auth(client) -> None:
    r = await client.get("/sessions")
    assert r.status_code == 401


async def test_sessions_empty_for_new_user(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)
    r = await client.get("/sessions")
    assert r.status_code == 200
    assert r.json() == []
