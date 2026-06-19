"""Embeddings adapter. Retrieval/screening depend on `EmbeddingsAdapter`, never on
sentence-transformers directly.

`BgeEmbeddings` wraps the `BAAI/bge-small-en-v1.5` model; its blocking `encode` runs in
an executor so the event loop is never blocked. `FakeEmbeddings` produces deterministic
unit vectors for tests without loading any model.
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import Protocol

# bge-small-en-v1.5 output dimensionality. Kept in sync with the model in config; the
# fake uses it so tests exercise the real vector width.
EMBEDDING_DIM = 384


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors. Returns 0.0 if either is zero."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class EmbeddingsAdapter(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in order."""
        ...


class BgeEmbeddings:
    """sentence-transformers `BAAI/bge-small-en-v1.5`, loaded lazily and run off-loop."""

    def __init__(self, *, model_name: str | None = None) -> None:
        from praxis.config import settings

        self._model_name = model_name or settings.embedding_model
        self._model: object | None = None

    def _load(self) -> object:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._encode, texts)

    def _encode(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(  # type: ignore[attr-defined]
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        return [vector.tolist() for vector in vectors]


class FakeEmbeddings:
    """Deterministic fake: same text always yields the same unit vector.

    Vectors come from a hash of the text, so they are stable across runs and processes
    without any model download. Cosine similarity is meaningful enough for tests.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self._dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        raw = bytearray()
        counter = 0
        while len(raw) < self._dim * 2:
            digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
            raw.extend(digest)
            counter += 1
        # Map byte pairs to floats in [-1, 1], then L2-normalize.
        values = [
            (int.from_bytes(raw[i : i + 2], "big") / 65535.0) * 2.0 - 1.0
            for i in range(0, self._dim * 2, 2)
        ]
        norm = sum(v * v for v in values) ** 0.5 or 1.0
        return [v / norm for v in values]


_embeddings: EmbeddingsAdapter | None = None


def get_embeddings() -> EmbeddingsAdapter:
    """FastAPI dependency. Tests override via `app.dependency_overrides`."""
    global _embeddings
    if _embeddings is None:
        _embeddings = BgeEmbeddings()
    return _embeddings
