"""resolve_company_profile: default, JD override, and unseeded error."""

from __future__ import annotations

import pytest

from praxis.db.repositories import CompanyProfileRepository
from praxis.db.seeds.company_profiles import seed_company_profiles
from praxis.schemas.parsing import JDParsed
from praxis.screening.company import UnseededArchetypeError, resolve_company_profile


async def test_default_when_no_keywords(db) -> None:
    await seed_company_profiles(db)
    repo = CompanyProfileRepository(db)

    profile = await resolve_company_profile(JDParsed(role="Backend Engineer"), repo)

    assert profile.id == "faang-structured"


async def test_jd_override_startup(db) -> None:
    await seed_company_profiles(db)
    repo = CompanyProfileRepository(db)

    profile = await resolve_company_profile(
        JDParsed(role="Engineer", must_haves=["thrive at a fast-paced startup"]), repo
    )

    assert profile.id == "startup-pragmatic"


async def test_jd_override_enterprise(db) -> None:
    await seed_company_profiles(db)
    repo = CompanyProfileRepository(db)

    profile = await resolve_company_profile(
        JDParsed(role="Engineer", required_competencies=["stakeholder management"]), repo
    )

    assert profile.id == "enterprise-behavioral"


async def test_unseeded_raises(db) -> None:
    repo = CompanyProfileRepository(db)

    with pytest.raises(UnseededArchetypeError):
        await resolve_company_profile(JDParsed(role="Engineer"), repo)
