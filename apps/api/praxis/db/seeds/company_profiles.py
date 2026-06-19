"""Seed the three company archetypes. Idempotent: upserts by id, safe to re-run.

Run with:  python -m praxis.db.seeds.company_profiles
"""

from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from praxis.db.repositories import CompanyProfileRepository
from praxis.db.session import SessionLocal

ARCHETYPES: list[dict[str, Any]] = [
    {
        "id": "faang-structured",
        "name": "FAANG — structured",
        "round_mix_json": {"coding": 0.45, "system_design": 0.35, "hr": 0.20},
        "rubric_weights_json": {
            "correctness": 0.30,
            "problem_solving": 0.25,
            "system_design": 0.25,
            "communication": 0.20,
        },
        "persona_json": {
            "tone": "structured and rigorous",
            "pacing": "brisk",
            "strictness": "high",
            "follow_ups": "probes edge cases, complexity, and scale",
        },
    },
    {
        "id": "startup-pragmatic",
        "name": "Startup — pragmatic",
        "round_mix_json": {"coding": 0.50, "system_design": 0.25, "hr": 0.25},
        "rubric_weights_json": {
            "correctness": 0.30,
            "pragmatism": 0.30,
            "breadth": 0.20,
            "communication": 0.20,
        },
        "persona_json": {
            "tone": "casual and collaborative",
            "pacing": "fast",
            "strictness": "medium",
            "follow_ups": "favors shipping and tradeoffs over theory",
        },
    },
    {
        "id": "enterprise-behavioral",
        "name": "Enterprise — behavioral",
        "round_mix_json": {"coding": 0.30, "system_design": 0.25, "hr": 0.45},
        "rubric_weights_json": {
            "correctness": 0.20,
            "communication": 0.30,
            "stakeholder_mgmt": 0.30,
            "process": 0.20,
        },
        "persona_json": {
            "tone": "formal and measured",
            "pacing": "deliberate",
            "strictness": "medium",
            "follow_ups": "emphasizes behavioral STAR answers and process",
        },
    },
]


async def seed_company_profiles(session: AsyncSession) -> int:
    """Upsert all archetypes. Returns the number seeded. Caller-agnostic to commit timing."""
    repo = CompanyProfileRepository(session)
    for archetype in ARCHETYPES:
        await repo.upsert(
            profile_id=archetype["id"],
            name=archetype["name"],
            round_mix_json=archetype["round_mix_json"],
            rubric_weights_json=archetype["rubric_weights_json"],
            persona_json=archetype["persona_json"],
        )
    return len(ARCHETYPES)


async def _main() -> None:
    async with SessionLocal() as session:
        count = await seed_company_profiles(session)
        await session.commit()
    print(f"seeded {count} company profiles")


if __name__ == "__main__":
    asyncio.run(_main())
