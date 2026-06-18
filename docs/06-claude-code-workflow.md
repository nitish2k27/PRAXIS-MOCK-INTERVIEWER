# Praxis — Building with Claude Code in VS Code

> Some Claude Code specifics change over time. For current install steps, flags, and features, check the official docs:
> - Overview: https://docs.claude.com/en/docs/claude-code/overview
> - npm package: https://www.npmjs.com/package/@anthropic-ai/claude-code
>
> The workflow and conventions below are durable.

---

## 1. Setup

1. Install Node.js (recent LTS).
2. Install Claude Code globally: `npm install -g @anthropic-ai/claude-code`.
3. In VS Code, open the **Praxis monorepo root**. Use Claude Code from the **integrated terminal** (`claude`) and/or the Claude Code VS Code extension if installed. Keeping it at the repo root (not inside `apps/api` or `apps/web`) lets it see the whole project and the `docs/`.
4. Authenticate per the docs.

---

## 2. The single most important habit: CLAUDE.md

Claude Code automatically reads a `CLAUDE.md` at the repo root (and respects nested ones). This is how you stop drift. Put a `CLAUDE.md` at the root and one in each app. A starter for the root:

```md
# Praxis — Agent Context

## What this is
Voice-native adaptive technical interview engine. See docs/01-system-architecture.md
for the full flow and docs/02-technical-requirements.md for the LOCKED stack.

## Non-negotiables (do not violate)
- Stack is LOCKED in docs/02. Never introduce a library outside it without
  recording a decision in that file's decision log.
- LangGraph owns ALL control flow. No imperative round-sequencing.
- All provider calls (STT/TTS/LLM/embeddings/rerank/sandbox) go through adapters.
  Nodes never import a provider SDK directly.
- Graph state is ONE Pydantic model (schemas/graph_state.py). No loose dicts.
- Rubric SCORES come from the scorer module, not from the LLM. The LLM does
  qualitative critique + the probe decision only.
- Async end-to-end. Blocking ML calls run in a thread/process pool.
- No browser storage for app data. Server is source of truth.
- Config (model names, thresholds, weights) lives in config + .env. No magic numbers.

## Build order
Follow docs/03-build-plan.md phases. We are currently in Phase: <UPDATE THIS>.
Do not build ahead of the current phase.

## Conventions
- Python: Ruff + mypy clean before done. Tests with pytest. Type everything.
- TS: strict mode, ESLint + Prettier clean. Tests with Vitest.
- Every new module gets a test. Every adapter gets an interface + a fake for tests.

## When unsure
Ask before introducing a new dependency, changing the graph topology, or altering
the DB schema. Prefer the smallest change that satisfies the current phase task.
```

Update the "currently in Phase" line as you progress — it's the cheapest way to keep sessions scoped.

---

## 3. Working without losing context

Context bloat is the main cause of bad agent output. Tactics:

- **One task per session.** Start Claude Code with a single, concrete task tied to a build-plan phase ("Implement the faster-whisper streaming STT adapter behind the STT interface, with a fake for tests"). Don't dump the whole project at it.
- **`/clear` between unrelated tasks.** A fresh context for a new module beats a long polluted one. Use `/compact` when a long task is still relevant but the history is large.
- **Plan first, then build.** Ask for a short plan/diff outline before it writes code; approve, then let it implement. This catches stack drift before files are touched.
- **Point at docs, don't re-explain.** "Per docs/02 section 1, the STT default is faster-whisper" beats pasting requirements. The docs are the memory.
- **Small diffs, frequent commits.** Commit after each working unit so you can revert a bad agent edit cleanly. Keep PRs/changes reviewable.
- **Keep the agent inside one app per session** when possible (`apps/api` work vs `apps/web` work) to limit the surface it reasons about.
- **Write the test or the interface first**, then ask it to implement against that. Constrains the solution space.
- **Custom slash commands / project commands** for repeated workflows (run tests, lint, migrate) so you and the agent invoke the same thing.
- **MCP servers** only if they earn it (e.g., a Postgres MCP to inspect the schema). Don't over-connect; each adds context cost.

Anti-patterns: one endless session for the whole build; asking for five unrelated changes at once; letting it "refactor while you're at it."

---

## 4. VS Code extensions that keep the project bug-free

These give you fast local feedback so bugs surface as you type, not at runtime. Most map to the quality tooling in docs/02.

### Python (apps/api, ml)
- **Python** (Microsoft) + **Pylance** — IntelliSense, type checking surfaced inline.
- **Ruff** — lint + format on save (matches the repo's Ruff config).
- **Mypy Type Checker** — static type errors inline.
- **Python Test Explorer / built-in testing** — run pytest from the editor.

### TypeScript / React (apps/web)
- **ESLint** — lint on save.
- **Prettier — Code formatter** — format on save.
- **Tailwind CSS IntelliSense** — class autocomplete + warnings.
- **Vitest** (extension) — run/watch tests in-editor.

### General
- **Error Lens** — shows errors/warnings inline at the line; this alone catches a huge share of bugs early.
- **GitLens** — history/blame, helps review agent diffs.
- **Docker** — manage the compose stack (Postgres, Redis, Chroma, Judge0).
- **REST Client** or **Thunder Client** — hit FastAPI endpoints without leaving VS Code.
- **DotENV** — `.env` syntax highlighting.
- **SQLAlchemy/SQL** highlighting (optional) for the data layer.

### Editor settings to enable
- Format on save (Ruff for Python, Prettier for TS).
- `tsc --strict` and mypy strict — treat type errors as build-blocking.
- **pre-commit** hooks running Ruff, mypy, ESLint, Prettier, and the test suites on staged files, so nothing broken gets committed (this is your real "bug-free" guardrail; extensions catch, hooks enforce).

---

## 5. A good session loop (repeat per phase task)

1. Update `CLAUDE.md` "current phase" line.
2. Open a fresh Claude Code session (`/clear` if reusing).
3. State one task, referencing the relevant doc section.
4. Ask for a brief plan; approve or correct.
5. Let it implement + write tests.
6. Run lint/types/tests locally (extensions + terminal); fix with it.
7. Commit. `/clear`. Next task.

This keeps context tight, diffs reviewable, and the stack locked — which is exactly what makes an agent-assisted build stay bug-free and on-spec.
