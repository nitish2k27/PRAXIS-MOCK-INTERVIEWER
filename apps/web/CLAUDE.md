# Praxis Web — Agent Context (apps/web)

React + Vite + TypeScript SPA: auth, upload, the voice interview client, Monaco coding
panel, history/report views. Read the root `CLAUDE.md` first.

## Stack (locked — see docs/02)
- React 18 + Vite + TypeScript **strict**.
- Tailwind CSS.
- React Query (server state) + Zustand (local UI/session state). No Redux.
- Native WebSocket client; Web Audio API / MediaRecorder for mic + playback.
- `@monaco-editor/react` for the coding round.

## Rules specific to the frontend
- **No browser storage (localStorage/sessionStorage) for app data.** Server is source of
  truth; cache via React Query. Auth is httpOnly cookies (not readable by JS) — do not
  try to store tokens in JS.
- All API/WS URLs and config come from `import.meta.env` (Vite env), never hardcoded.
- The interview screen is voice-first: show clear listening / speaking / thinking state;
  barge-in must visibly cut off interviewer audio.
- WebSocket message types mirror the backend contract (see docs/01 §10). Keep a single
  typed message module shared across components.
- Components stay presentational where possible; data fetching via React Query hooks.

## Component inventory (see docs/05)
`AuthButton`, `DashboardHeader`, `SessionCard`, `UploadForm`, `ArchetypePicker`,
`SetupSummary`, `InterviewStage`, `InterviewControls`, `CodePanel`, `ReportView`,
`RoundSection`, `ConnectionBanner`.

## Commands
- Dev: `npm run dev`
- Quality gate: `tsc --noEmit && npm run lint && npm run test`

## Phase 1 scope here (Ingestion & screening — light surfacing)
Phase 0 (sign-in, dashboard with history list, resume/JD upload form) is **done**. The
backend is the heavy part of Phase 1; the web job is only to make the screening result
**visible**:
- After upload, call `POST /screening {resume_id, jd_id}` (React Query mutation).
- Render the result on session detail and the dashboard: fit score + band, resolved
  company archetype, top weighted competencies, and the fit rationale.
- Server stays the source of truth; cache via React Query, no browser storage of app data.
- No interview/voice UI, no Monaco yet — those are Phase 2+.
