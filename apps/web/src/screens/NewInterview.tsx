import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Me } from "../lib/api";
import { useRunScreening, useUploadJD, useUploadResume } from "../lib/api";

export default function NewInterview({ user: _user }: { user: Me }) {
  const navigate = useNavigate();
  const [resume, setResume] = useState<File | null>(null);
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const uploadResume = useUploadResume();
  const uploadJD = useUploadJD();
  const runScreening = useRunScreening();

  const submit = async () => {
    setError(null);
    if (!resume) {
      setError("Please select a resume file.");
      return;
    }
    if (!jdText.trim() && !jdFile) {
      setError("Paste a job description or upload a JD file.");
      return;
    }
    try {
      const resumeRes = await uploadResume.mutateAsync(resume);
      const jdRes = await uploadJD.mutateAsync({
        rawText: jdText.trim() || undefined,
        file: jdFile ?? undefined,
      });
      const session = await runScreening.mutateAsync({
        resumeId: resumeRes.id,
        jdId: jdRes.id,
      });
      navigate(`/sessions/${session.id}`);
    } catch (e) {
      setError(String(e));
    }
  };

  const busy =
    uploadResume.isPending || uploadJD.isPending || runScreening.isPending;

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-semibold mb-6">New interview</h1>

        <section className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Resume (PDF / DOCX)
          </label>
          <input
            type="file"
            accept=".pdf,.docx,application/pdf"
            onChange={(e) => setResume(e.target.files?.[0] ?? null)}
          />
        </section>

        <section className="mb-6">
          <label className="block text-sm font-medium mb-2">Job description</label>
          <textarea
            className="w-full border rounded p-2 mb-2"
            rows={6}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the job description, or upload a file below…"
          />
          <input
            type="file"
            accept=".pdf,.docx,.txt,application/pdf"
            onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
          />
        </section>

        {error && <div className="mb-4 text-red-600 text-sm">{error}</div>}

        <div className="flex gap-2">
          <button
            className="px-4 py-2 rounded bg-slate-900 text-white disabled:opacity-50 hover:bg-slate-800"
            disabled={busy}
            onClick={submit}
          >
            {runScreening.isPending
              ? "Screening…"
              : busy
                ? "Uploading…"
                : "Upload & screen"}
          </button>
          <button
            className="px-4 py-2 rounded border hover:bg-slate-100"
            disabled={busy}
            onClick={() => navigate("/")}
          >
            Cancel
          </button>
        </div>
      </div>
    </main>
  );
}
