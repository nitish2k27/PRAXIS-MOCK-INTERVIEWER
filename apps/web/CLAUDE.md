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

## Phase 0 scope here
App shell: sign-in screen ("Continue with Google"), dashboard with an (empty) history
list, and the resume/JD upload form. No interview UI yet.
