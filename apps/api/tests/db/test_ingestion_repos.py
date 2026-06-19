"""ResumeRepository / JobDescriptionRepository persist parsed_json round-trips."""

from __future__ import annotations

from praxis.db.models import JobDescription, Resume, User
from praxis.db.repositories import JobDescriptionRepository, ResumeRepository


async def _user(db) -> User:
    user = User(oauth_provider="google", oauth_sub="s1", email="a@x.com", name="A")
    db.add(user)
    await db.flush()
    return user


async def test_resume_save_parsed(db) -> None:
    user = await _user(db)
    resume = Resume(user_id=user.id, file_url="file:///tmp/r.pdf")
    db.add(resume)
    await db.flush()

    repo = ResumeRepository(db)
    saved = await repo.save_parsed(resume.id, {"skills": ["python"], "seniority": "senior"})
    await db.commit()

    assert saved is not None
    fetched = await repo.get_by_id(resume.id)
    assert fetched is not None
    assert fetched.parsed_json == {"skills": ["python"], "seniority": "senior"}


async def test_jd_save_parsed(db) -> None:
    user = await _user(db)
    jd = JobDescription(user_id=user.id, raw_text="role text")
    db.add(jd)
    await db.flush()

    repo = JobDescriptionRepository(db)
    saved = await repo.save_parsed(jd.id, {"role": "Backend Engineer", "must_haves": ["python"]})
    await db.commit()

    assert saved is not None
    fetched = await repo.get_by_id(jd.id)
    assert fetched is not None
    assert fetched.parsed_json == {"role": "Backend Engineer", "must_haves": ["python"]}


async def test_save_parsed_missing_returns_none(db) -> None:
    repo = ResumeRepository(db)
    assert await repo.save_parsed("does-not-exist", {"skills": []}) is None
