"""Tests for the embeddings adapter via the deterministic FakeEmbeddings."""

from __future__ import annotations

from praxis.retrieval.embeddings import EMBEDDING_DIM, FakeEmbeddings


async def test_deterministic_same_text_same_vector() -> None:
    emb = FakeEmbeddings()

    (a,) = await emb.embed(["hello"])
    (b,) = await emb.embed(["hello"])

    assert a == b


async def test_different_text_different_vector() -> None:
    emb = FakeEmbeddings()

    a, b = await emb.embed(["hello", "world"])

    assert a != b


async def test_dimension_and_batch_length() -> None:
    emb = FakeEmbeddings()

    vectors = await emb.embed(["one", "two", "three"])

    assert len(vectors) == 3
    assert all(len(v) == EMBEDDING_DIM for v in vectors)


async def test_unit_norm() -> None:
    emb = FakeEmbeddings()

    (vector,) = await emb.embed(["normalize me"])

    norm = sum(v * v for v in vector) ** 0.5
    assert abs(norm - 1.0) < 1e-6


async def test_empty_input() -> None:
    emb = FakeEmbeddings()

    assert await emb.embed([]) == []
