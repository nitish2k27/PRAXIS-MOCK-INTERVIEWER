"""build_competency_map over FakeEmbeddings (identical strings → cosine 1.0)."""

from __future__ import annotations

from praxis.ingestion.competency import build_competency_map
from praxis.retrieval.embeddings import FakeEmbeddings
from praxis.schemas.parsing import ExperienceItem, JDParsed, ResumeParsed


async def test_covered_vs_uncovered_and_weights() -> None:
    jd = JDParsed(must_haves=["python"], required_competencies=["api design"])
    resume = ResumeParsed(skills=["python"])  # "python" matches; "api design" does not

    cmap = await build_competency_map(resume, jd, FakeEmbeddings())

    by_name = {c.name: c for c in cmap.competencies}
    # must-have weight 1.0 vs required 0.6, normalized over 1.6.
    assert by_name["python"].weight == 1.0 / 1.6
    assert by_name["api design"].weight == 0.6 / 1.6

    assert by_name["python"].covered is True
    assert by_name["python"].evidence == "python"
    assert by_name["api design"].covered is False
    assert by_name["api design"].evidence is None

    assert cmap.coverage_score == 1.0 / 1.6


async def test_evidence_from_experience_and_projects() -> None:
    jd = JDParsed(required_competencies=["kubernetes"])
    resume = ResumeParsed(experience=[ExperienceItem(highlights=["kubernetes"])])

    cmap = await build_competency_map(resume, jd, FakeEmbeddings())

    assert cmap.competencies[0].covered is True
    assert cmap.competencies[0].evidence == "kubernetes"


async def test_empty_jd_yields_empty_map() -> None:
    cmap = await build_competency_map(ResumeParsed(skills=["python"]), JDParsed(), FakeEmbeddings())

    assert cmap.competencies == []
    assert cmap.coverage_score == 0.0


async def test_no_signals_nothing_covered() -> None:
    jd = JDParsed(must_haves=["python"])
    cmap = await build_competency_map(ResumeParsed(), jd, FakeEmbeddings())

    assert cmap.competencies[0].covered is False
    assert cmap.coverage_score == 0.0
