"""compute_fit over FakeLLM (coverage rubric) + FakeEmbeddings (dense similarity)."""

from __future__ import annotations

import pytest

from praxis.orchestrator.llm import FakeLLM
from praxis.retrieval.embeddings import FakeEmbeddings
from praxis.screening.fit import compute_fit


async def test_proceeds_above_threshold() -> None:
    llm = FakeLLM(responses=[{"coverage": 0.75, "rationale": "strong", "met": ["python"]}])
    # Identical resume/jd text → dense cosine 1.0 (FakeEmbeddings is deterministic).
    result = await compute_fit("same text", "same text", ["python"], llm, FakeEmbeddings())

    assert result.dense_similarity == pytest.approx(1.0)
    assert result.coverage == pytest.approx(0.75)
    # 0.4*1.0 + 0.6*0.75
    assert result.fit_score == pytest.approx(0.85)
    assert result.proceed is True
    assert "strong" in result.rationale


async def test_below_threshold_does_not_proceed() -> None:
    llm = FakeLLM(responses=[{"coverage": 0.1, "rationale": "weak"}])
    result = await compute_fit(
        "resume words", "totally different jd", ["python"], llm, FakeEmbeddings()
    )

    assert result.fit_score < 0.6
    assert result.proceed is False


async def test_no_must_haves_skips_llm() -> None:
    llm = FakeLLM(responses=[])  # would raise if called
    result = await compute_fit("same text", "same text", [], llm, FakeEmbeddings())

    assert result.coverage == 1.0
    assert llm.calls == []
    assert result.fit_score == pytest.approx(1.0)
    assert result.proceed is True
