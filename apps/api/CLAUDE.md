# Praxis API — Agent Context (apps/api)

FastAPI backend: REST (auth/CRUD) + WebSocket, LangGraph orchestrator, retrieval,
scoring, voice adapters. Read the root `CLAUDE.md` first.

## Stack (locked — see docs/02)
- Python 3.11+, FastAPI (async), Uvicorn, Pydantic v2.
- LangGraph + langchain-core for control flow.
- SQLAlchemy 2.0 async + Alembic. PostgreSQL (Neon in prod, local in dev).
- Redis (live session state, pub/sub, rate limit).
- ChromaDB (vectors), sentence-transformers (bge-small), bge-reranker-base.
- Groq `llama-3.3-70b-versatile` (behind an LLM adapter).
- faster-whisper + silero-vad (STT/VAD), Piper (TTS) — behind adapters.
- Auth: Authlib (Google OIDC) + app JWT in httpOnly cookies.

## Package layout (`praxis/`)
- `orchestrator/` — graphs (controller + per-round) + nodes + conditional edges.
- `schemas/` — Pydantic models, including `graph_state.py` (the ONE state model).
- `voice/` — `stt`, `vad`, `tts` adapters behind interfaces + fakes.
- `retrieval/` — Chroma client, chunking/ingestion per corpus, hybrid search, rerank.
- `scoring/` — scorer interface, prompted impl (MVP) + LoRA impl, rubric defs.
- `rounds/` — `coding`, `system_design`, `hr` (round-specific sources/rubrics; coding
  has the sub-graph + sandbox adapter).
- `auth/` — oauth flow, jwt issue/verify, cookie handling, route guard dependency.
- `db/` — SQLAlchemy models, Alembic env, repositories (no raw SQL in nodes/routes).
- `ws/` — WebSocket lifecycle, message protocol, Redis pub/sub bridge.
- `reports/` — synthesis + persistence + serialization.
- `config.py` — typed config; all model names/thresholds/weights here + `.env`.

## Rules specific to the backend
- Routes/nodes depend on adapters and repositories via FastAPI dependency injection,
  never on concrete SDK clients.
- Blocking ML (whisper, embeddings, scorer) runs via `run_in_executor` / a worker, not
  inline in the event loop.
- All DB access through `db/repositories`. No SQL strings scattered in business logic.
- WebSocket handlers are thin: they translate messages to/from orchestrator events and
  Redis; logic lives in `orchestrator/`.
- Every adapter ships with a deterministic fake so tests don't hit providers/network.

## Commands
- Run dev: `uvicorn praxis.main:app --reload`
- Migrate: `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`
- Quality gate: `ruff check . && ruff format --check . && mypy . && pytest`

## Phase 0 scope here
Auth (Google OAuth + JWT cookies + users upsert + route guard), DB models + first
migration for all core tables, file upload → object storage, and the FastAPI app shell.
Nothing from later phases.
