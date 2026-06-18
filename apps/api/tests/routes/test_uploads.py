"""Upload endpoints — resume + JD."""

from __future__ import annotations

import io


async def _login(client) -> None:
    await client.get("/auth/google/callback", follow_redirects=False)


async def test_upload_resume_requires_auth(client) -> None:
    r = await client.post("/resumes", files={"file": ("r.pdf", b"x", "application/pdf")})
    assert r.status_code == 401


async def test_upload_resume_ok(client) -> None:
    await _login(client)
    r = await client.post(
        "/resumes",
        files={"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["file_url"].startswith("file://")
    assert body["id"]


async def test_upload_resume_rejects_bad_type(client) -> None:
    await _login(client)
    r = await client.post("/resumes", files={"file": ("r.txt", b"x", "text/plain")})
    assert r.status_code == 415


async def test_upload_jd_text(client) -> None:
    await _login(client)
    r = await client.post("/job_descriptions", data={"raw_text": "we need a backend engineer"})
    assert r.status_code == 201
    assert r.json()["raw_text"] == "we need a backend engineer"


async def test_upload_jd_requires_something(client) -> None:
    await _login(client)
    r = await client.post("/job_descriptions", data={})
    assert r.status_code == 400
