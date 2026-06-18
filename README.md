# Praxis

Voice-native adaptive technical interview engine. See [docs/](docs/) for the full design (start with `01-system-architecture.md`).

## Layout
- `apps/web` — React + Vite + TypeScript frontend
- `apps/api` — FastAPI backend (LangGraph orchestrator, voice, retrieval, scoring)
- `ml/` — LoRA training notebooks, scripts, datasets
- `infra/` — Docker / seed scripts (Judge0 added in Phase 5)
- `docs/` — design documents
- `CLAUDE.md` — agent context (root + per-app)

## Phase 0 — run the stack

### 1. Infra (Postgres + Redis + Chroma) via docker-compose

```sh
docker compose up -d postgres redis chroma
```

Optional: bring up the api + web containers as well (`docker compose up -d`). For dev iteration you can run them locally instead:

### 2. API locally

```sh
cd apps/api
cp .env.example .env       # then fill GOOGLE_CLIENT_ID / SECRET if testing real OAuth
python -m venv .venv && . .venv/Scripts/activate    # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn praxis.main:app --reload
```

Quality gate:
```sh
ruff check . && ruff format --check . && mypy . && pytest
```

### 3. Web locally

```sh
cd apps/web
cp .env.example .env
npm install
npm run dev
```

Quality gate:
```sh
tsc --noEmit && npm run lint && npm test
```

## Phase 0 DoD

A user signs in via Google, uploads a resume + JD, rows + files exist; revisiting the dashboard lists their (empty) interview sessions.

## Google OAuth setup (dev)

1. https://console.cloud.google.com/ → APIs & Services → Credentials → Create OAuth client (Web application).
2. Authorized redirect URI: `http://localhost:8000/auth/google/callback`.
3. Copy client id + secret into `apps/api/.env`.
4. The `FakeOIDCProvider` covers tests — no Google credentials needed to run the test suite.
