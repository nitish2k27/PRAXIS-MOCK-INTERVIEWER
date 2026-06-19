import { Link, useParams } from "react-router-dom";
import type { Me } from "../lib/api";
import { useSession } from "../lib/api";
import ScreeningResult from "../components/ScreeningResult";

export default function SessionDetail({ user: _user }: { user: Me }) {
  const { id = "" } = useParams();
  const session = useSession(id);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="font-semibold">Praxis</div>
          <Link to="/" className="text-sm text-slate-600 hover:underline">
            ← Back to dashboard
          </Link>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-semibold mb-6">Screening result</h1>
        {session.isLoading && <div className="text-slate-500">Loading…</div>}
        {session.isError && (
          <div className="text-red-600 text-sm">Could not load this session.</div>
        )}
        {session.data && (
          <div className="rounded border bg-white p-6">
            <ScreeningResult session={session.data} />
          </div>
        )}
      </div>
    </main>
  );
}
