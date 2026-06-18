import { loginUrl } from "../lib/api";

export default function SignIn() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center max-w-md px-6">
        <h1 className="text-3xl font-semibold mb-2">Praxis</h1>
        <p className="text-slate-600 mb-8">
          Practice real technical interviews by voice.
        </p>
        <a
          href={loginUrl()}
          className="inline-block px-5 py-2.5 rounded-md bg-slate-900 text-white hover:bg-slate-800"
        >
          Continue with Google
        </a>
      </div>
    </main>
  );
}
