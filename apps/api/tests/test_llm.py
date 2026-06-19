"""Tests for the LLM adapter via the deterministic FakeLLM."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from praxis.orchestrator.llm import FakeLLM, LLMError


class _Reply(BaseModel):
    answer: str
    score: int


async def test_returns_queued_responses_in_order() -> None:
    llm = FakeLLM(responses=[{"answer": "a", "score": 1}, {"answer": "b", "score": 2}])

    first = await llm.complete_json(prompt="p1", schema=_Reply)
    second = await llm.complete_json(prompt="p2", schema=_Reply, system="sys")

    assert (first.answer, first.score) == ("a", 1)
    assert (second.answer, second.score) == ("b", 2)


async def test_accepts_json_string_and_basemodel() -> None:
    llm = FakeLLM(responses=['{"answer": "j", "score": 3}', _Reply(answer="m", score=4)])

    from_str = await llm.complete_json(prompt="p", schema=_Reply)
    from_model = await llm.complete_json(prompt="p", schema=_Reply)

    assert from_str.score == 3
    assert from_model.score == 4


async def test_records_calls() -> None:
    llm = FakeLLM(responses=[{"answer": "a", "score": 1}])

    await llm.complete_json(prompt="hello", schema=_Reply, system="be terse")

    assert llm.calls == [{"prompt": "hello", "system": "be terse"}]


async def test_raises_when_exhausted() -> None:
    llm = FakeLLM(responses=[])

    with pytest.raises(LLMError):
        await llm.complete_json(prompt="p", schema=_Reply)


async def test_validates_response_shape() -> None:
    llm = FakeLLM(responses=[{"answer": "missing score"}])

    with pytest.raises(ValidationError):
        await llm.complete_json(prompt="p", schema=_Reply)
