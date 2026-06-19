"""Company-profile seed is idempotent and sets the expected shape."""

from __future__ import annotations

from praxis.db.repositories import CompanyProfileRepository
from praxis.db.seeds.company_profiles import seed_company_profiles


async def test_seed_is_idempotent(db) -> None:
    count = await seed_company_profiles(db)
    await db.commit()
    await seed_company_profiles(db)  # re-run must not duplicate
    await db.commit()

    repo = CompanyProfileRepository(db)
    profiles = await repo.list_all()

    assert count == 3
    assert len(profiles) == 3
    assert {p.id for p in profiles} == {
        "faang-structured",
        "startup-pragmatic",
        "enterprise-behavioral",
    }


async def test_seed_populates_json_columns(db) -> None:
    await seed_company_profiles(db)
    await db.commit()

    profile = await CompanyProfileRepository(db).get_by_id("faang-structured")

    assert profile is not None
    assert profile.round_mix_json["coding"] == 0.45
    assert "correctness" in profile.rubric_weights_json
    assert profile.persona_json["strictness"] == "high"
