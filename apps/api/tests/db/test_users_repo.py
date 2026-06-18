"""UserRepository.upsert_by_oauth insert + conflict-update paths."""

from __future__ import annotations

from praxis.db.repositories import UserRepository


async def test_upsert_creates_then_updates(db) -> None:
    repo = UserRepository(db)
    first = await repo.upsert_by_oauth(provider="google", sub="abc", email="a@x.com", name="A")
    await db.commit()
    second = await repo.upsert_by_oauth(provider="google", sub="abc", email="b@x.com", name="B")
    await db.commit()
    assert first.id == second.id
    assert second.email == "b@x.com"
    assert second.name == "B"


async def test_upsert_different_sub_creates_separate_user(db) -> None:
    repo = UserRepository(db)
    a = await repo.upsert_by_oauth(provider="google", sub="aaa", email="a@x.com", name=None)
    b = await repo.upsert_by_oauth(provider="google", sub="bbb", email="b@x.com", name=None)
    await db.commit()
    assert a.id != b.id
