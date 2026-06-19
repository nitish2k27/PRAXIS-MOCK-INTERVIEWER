"""parse_resume / parse_jd over FakeLLM — no network."""

from __future__ import annotations

from praxis.ingestion.parse import parse_jd, parse_resume
from praxis.orchestrator.llm import FakeLLM


async def test_parse_resume_returns_validated_model() -> None:
    llm = FakeLLM(
        responses=[
            {
                "skills": ["python", "fastapi"],
                "experience": [{"company": "Acme", "title": "SWE", "highlights": ["shipped x"]}],
                "projects": [{"name": "Praxis", "tech": ["langgraph"]}],
                "seniority": "senior",
            }
        ]
    )

    parsed = await parse_resume("Jane Doe — Senior Engineer at Acme", llm)

    assert parsed.skills == ["python", "fastapi"]
    assert parsed.experience[0].company == "Acme"
    assert parsed.projects[0].name == "Praxis"
    assert parsed.seniority == "senior"


async def test_parse_jd_returns_validated_model() -> None:
    llm = FakeLLM(
        responses=[
            {
                "role": "Backend Engineer",
                "role_level": "senior",
                "must_haves": ["5y python"],
                "required_competencies": ["api design", "databases"],
            }
        ]
    )

    parsed = await parse_jd("We need a senior backend engineer...", llm)

    assert parsed.role == "Backend Engineer"
    assert parsed.must_haves == ["5y python"]
    assert parsed.required_competencies == ["api design", "databases"]


async def test_source_text_reaches_prompt() -> None:
    llm = FakeLLM(responses=[{}])

    await parse_resume("UNIQUE_RESUME_MARKER_123", llm)

    assert "UNIQUE_RESUME_MARKER_123" in llm.calls[0]["prompt"]
    assert llm.calls[0]["system"] is not None


async def test_sparse_response_uses_defaults() -> None:
    llm = FakeLLM(responses=[{}])

    parsed = await parse_resume("anything", llm)

    assert parsed.skills == []
    assert parsed.seniority is None
