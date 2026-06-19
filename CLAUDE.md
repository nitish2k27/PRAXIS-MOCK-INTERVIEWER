# Praxis — Agent Context (root)

Voice-native adaptive technical interview engine. This file is read automatically by
Claude Code. Keep it accurate; it is the main defense against drift.

## Read first
- Full system flow & data: `docs/01-system-architecture.md`
- LOCKED stack: `docs/02-technical-requirements.md`
- Build order: `docs/03-build-plan.md`
- Requirements & latency targets: `docs/04-functional-nonfunctional-requirements.md`

## Current phase
> **Phase 2 — Voice layer (NOT STARTED).** Do not build ahead of this phase.
> (Update this line every time you start a new phase.)
>
> Phase 0 (Foundations: auth, DB schema, upload + storage, app shell) is **complete**.
> Phase 1 (Ingestion & screening) is **complete** — see summary below. Phase 2 work
> (faster-whisper STT + silero-vad, Piper TTS, WebSocket audio + barge-in, latency
> instrumentation; docs/03) has **not** begun.
>
> **Phase 1 — DONE.** Inputs become structured, persisted, visible state:
> - Adapters: `orchestrator/llm.py` (`LLMAdapter`/`GroqLLM`/`FakeLLM`),
>   `retrieval/embeddings.py` (`EmbeddingsAdapter`/`BgeEmbeddings`/`FakeEmbeddings`).
> - `ingestion/` extract (pdfplumber/docx2txt via storage adapter) + parse (LLM JSON →
>   `ResumeParsed`/`JDParsed`, persisted to `parsed_json`) + competency map.
> - `screening/` fit (`w_dense·cosine + w_coverage·LLM-coverage`) + company archetype
>   resolution. `POST /screening` pipeline + `GET /sessions/{id}`.
> - Web: `POST /screening` after upload; result (fit + band + archetype + top
>   competencies + rationale) on session detail; fit score in dashboard list.
> - 3 company archetypes seeded (`python -m praxis.db.seeds.company_profiles`).
>
> Phase 1 decisions (locked, still in force): competency map persists in
> `interview_sessions.config_json` (no schema change); screening runs via an explicit
> `POST /screening {resume_id, jd_id}`; deps added — pdfplumber, docx2txt, groq,
> sentence-transformers (all recorded in docs/02). Storage adapter gained `read(url)`.

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
