"""LLM adapter. Nodes/routes depend on `LLMAdapter`, never on the groq SDK.

`GroqLLM` is the real implementation; `FakeLLM` is a deterministic fake for tests.
The only capability exposed is structured JSON output validated into a Pydantic model —
the orchestrator never deals with raw strings.
"""

from __future__ import annotations

import json
from collections import deque
from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when the provider returns no/invalid content."""


class LLMAdapter(Protocol):
    async def complete_json(
        self,
        *,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        """Return the model's response parsed and validated into `schema`."""
        ...


class GroqLLM:
    """Groq-backed adapter using the async SDK client.

    Network I/O is awaited on the event loop (the SDK client is async), so no
    executor offload is needed here.
    """

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        from groq import AsyncGroq

        from praxis.config import settings

        self._model = model or settings.groq_model
        self._client = AsyncGroq(api_key=api_key or settings.groq_api_key)

    async def complete_json(
        self,
        *,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        messages: list[dict[str, str]] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Plain dicts are valid at runtime; they don't match the SDK's TypedDict overloads.
        completion = await self._client.chat.completions.create(  # type: ignore[call-overload]
            model=self._model,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            raise LLMError("Groq returned empty content")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - provider misbehaviour
            raise LLMError(f"Groq returned non-JSON content: {exc}") from exc
        return schema.model_validate(payload)


class FakeLLM:
    """Deterministic in-memory LLM for tests.

    Construct with the responses to hand back, in order. Each may be a dict, a JSON
    string, or a `BaseModel`; every response is validated against the requested schema
    so tests fail loudly on a shape mismatch.
    """

    def __init__(self, responses: list[dict[str, object] | str | BaseModel] | None = None) -> None:
        self._responses: deque[dict[str, object] | str | BaseModel] = deque(responses or [])
        self.calls: list[dict[str, str | None]] = []

    async def complete_json(
        self,
        *,
        prompt: str,
        schema: type[T],
        system: str | None = None,
    ) -> T:
        self.calls.append({"prompt": prompt, "system": system})
        if not self._responses:
            raise LLMError("FakeLLM has no queued responses left")
        raw = self._responses.popleft()
        if isinstance(raw, BaseModel):
            return schema.model_validate(raw.model_dump())
        if isinstance(raw, str):
            raw = json.loads(raw)
        return schema.model_validate(raw)


_llm: LLMAdapter | None = None


def get_llm() -> LLMAdapter:
    """FastAPI dependency. Tests override via `app.dependency_overrides`."""
    global _llm
    if _llm is None:
        _llm = GroqLLM()
    return _llm
