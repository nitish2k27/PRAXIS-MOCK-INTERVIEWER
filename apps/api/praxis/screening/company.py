"""Resolve a seeded company archetype for a screening.

Default archetype id comes from config; a JD can override it when its parsed fields mention
archetype-defining keywords. Profiles are read through the repository.
"""

from __future__ import annotations

from praxis.config import settings
from praxis.db.models import CompanyProfile
from praxis.db.repositories import CompanyProfileRepository
from praxis.schemas.parsing import JDParsed

# Keyword → archetype id. Checked in this order; the first archetype with a keyword hit in
# the JD wins. Ids must match the seeded profiles.
ARCHETYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "startup-pragmatic": (
        "startup",
        "early-stage",
        "early stage",
        "fast-paced",
        "scrappy",
        "founding",
    ),
    "enterprise-behavioral": (
        "enterprise",
        "fortune 500",
        "compliance",
        "stakeholder",
        "behavioral",
    ),
    "faang-structured": ("faang", "big tech", "large-scale", "distributed systems", "hyperscale"),
}


class UnseededArchetypeError(RuntimeError):
    """Raised when neither the resolved nor the default archetype exists in the DB."""


def _archetype_for_jd(jd: JDParsed) -> str:
    haystack = " ".join(
        [jd.role or "", jd.role_level or "", *jd.must_haves, *jd.required_competencies]
    ).lower()
    for archetype_id, keywords in ARCHETYPE_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return archetype_id
    return settings.default_company_archetype


async def resolve_company_profile(jd: JDParsed, repo: CompanyProfileRepository) -> CompanyProfile:
    resolved_id = _archetype_for_jd(jd)
    profile = await repo.get_by_id(resolved_id)
    if profile is None and resolved_id != settings.default_company_archetype:
        profile = await repo.get_by_id(settings.default_company_archetype)
    if profile is None:
        raise UnseededArchetypeError(
            f"no company profile for {resolved_id!r} or default "
            f"{settings.default_company_archetype!r}; run the company-profile seed"
        )
    return profile
