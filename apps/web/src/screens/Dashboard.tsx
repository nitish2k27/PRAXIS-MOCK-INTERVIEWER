import { Link } from "react-router-dom";
import type { Me } from "../lib/api";
import { useLogout, useSessions } from "../lib/api";

export default function Dashboard({ user }: { user: Me }) {
  const sessions = useSessions(true);
  const logout = useLogout();

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="font-semibold">Praxis</div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user.email}</span>
            <button
              className="px-3 py-1 rounded border hover:bg-slate-100"
              onClick={() => logout.mutate()}
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="mb-6">
          <Link
            to="/new"
            className="inline-block px-4 py-2 rounded bg-slate-900 text-white hover:bg-slate-800"
          >
            Start a new interview
          </Link>
        </div>

        <h2 className="text-lg font-medium mb-3">Your interviews</h2>
        {sessions.isLoading && <div className="text-slate-500">Loading…</div>}
        {sessions.data && sessions.data.length === 0 && (
          <div className="text-slate-500">No interviews yet.</div>
        )}
        {sessions.data && sessions.data.length > 0 && (
          <ul className="space-y-2">
            {sessions.data.map((s) => (
              <li
                key={s.id}
                className="p-3 rounded border bg-white flex justify-between"
              >
                <div>
                  <div className="text-sm text-slate-600">
                    {s.company_profile_id ?? "—"}
                  </div>
                  <div className="text-xs text-slate-400">{s.started_at}</div>
                </div>
                <div className="text-sm">{s.status}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
