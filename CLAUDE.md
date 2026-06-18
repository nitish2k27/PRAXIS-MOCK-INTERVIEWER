# Praxis — Agent Context (root)

Voice-native adaptive technical interview engine. This file is read automatically by
Claude Code. Keep it accurate; it is the main defense against drift.

## Read first
- Full system flow & data: `docs/01-system-architecture.md`
- LOCKED stack: `docs/02-technical-requirements.md`
- Build order: `docs/03-build-plan.md`
- Requirements & latency targets: `docs/04-functional-nonfunctional-requirements.md`

## Current phase
> **Phase 1 — Foundations.** Do not build ahead of this phase.
> (Update this line every time you start a new phase.)

## Non-negotiables (do not violate)
- The stack is LOCKED in docs/02. Never add a library outside it without recording a
  decision in that file's decision log first.
- LangGraph owns ALL control flow. No imperative round-sequencing anywhere.
- Every external provider (STT, TTS, LLM, embeddings, reranker, sandbox) is called
  through an adapter/interface. Nodes and routes NEVER import a provider SDK directly.
- The LangGraph state is ONE Pydantic model (`apps/api/praxis/schemas/graph_state.py`).
  No loose dicts passed between nodes.
- Rubric SCORES come from the scoring module, not the LLM. The LLM only does
  qualitative critique + the probe/branch decision.
- Async end-to-end. Blocking ML calls run in a thread/process pool.
- No browser storage for app data. Server is the source of truth; the SPA caches via
  React Query.
- Config (model names, thresholds, rubric weights, time budgets) lives in a typed
  config module + `.env`. No magic numbers in code.

## Definition of done (every task)
- Python: `ruff check`, `ruff format`, `mypy` all clean; `pytest` passing.
- TS: `tsc --noEmit`, ESLint, Prettier clean; Vitest passing.
- New module → has a test. New adapter → has an interface + a fake for tests.

## When unsure — ASK before:
- adding a dependency, changing the graph topology, or altering the DB schema.
Prefer the smallest change that satisfies the current phase task.

## Repo map
- `apps/api` — FastAPI backend (has its own CLAUDE.md)
- `apps/web` — React + Vite + TS frontend (has its own CLAUDE.md)
- `ml/` — LoRA training + RAG corpora sources + ingestion (outside the serving path)
- `infra/` — Dockerfiles, seed scripts
- `docker-compose.yml` — dev stack (root)
