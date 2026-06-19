import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Me = {
  id: string;
  email: string;
  name: string | null;
  provider: string;
};

export type Session = {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  company_profile_id: string | null;
  fit_score: number | null;
};

export type Competency = {
  name: string;
  weight: number;
  covered: boolean;
  coverage: number;
  evidence: string | null;
};

export type ScreeningConfig = {
  competency_map: { competencies: Competency[]; coverage_score: number };
  fit: {
    fit_score: number;
    proceed: boolean;
    rationale: string;
    dense_similarity: number;
    coverage: number;
  };
  resume_summary: Record<string, unknown>;
  jd_summary: Record<string, unknown>;
};

export type SessionDetail = {
  id: string;
  status: string;
  resume_id: string | null;
  jd_id: string | null;
  company_profile_id: string | null;
  fit_score: number | null;
  started_at: string | null;
  completed_at: string | null;
  config_json: ScreeningConfig | null;
};

export type FitBand = "Strong" | "Promising" | "Mixed" | "Weak";

/** Map a 0..1 fit score to a display band. Single source of truth for the label. */
export function fitBand(score: number): FitBand {
  if (score >= 0.8) return "Strong";
  if (score >= 0.6) return "Promising";
  if (score >= 0.4) return "Mixed";
  return "Weak";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { credentials: "include", ...init });
  if (!res.ok) throw new Error(`request failed: ${res.status}`);
  return (await res.json()) as T;
}

export function useMe() {
  return useQuery<Me | null>({
    queryKey: ["me"],
    queryFn: async () => {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (res.status === 401) return null;
      if (!res.ok) throw new Error(`/auth/me failed: ${res.status}`);
      return (await res.json()) as Me;
    },
  });
}

export function useSessions(enabled: boolean) {
  return useQuery<Session[]>({
    queryKey: ["sessions"],
    queryFn: () => apiFetch<Session[]>("/sessions"),
    enabled,
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    },
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useUploadResume() {
  return useMutation({
    mutationFn: async (file: File): Promise<{ id: string }> => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/resumes`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
      if (!res.ok) throw new Error(`resume upload failed: ${res.status}`);
      return (await res.json()) as { id: string };
    },
  });
}

export function useUploadJD() {
  return useMutation({
    mutationFn: async (input: { rawText?: string; file?: File }): Promise<{ id: string }> => {
      const fd = new FormData();
      if (input.rawText) fd.append("raw_text", input.rawText);
      if (input.file) fd.append("file", input.file);
      const res = await fetch(`${API}/job_descriptions`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
      if (!res.ok) throw new Error(`jd upload failed: ${res.status}`);
      return (await res.json()) as { id: string };
    },
  });
}

export function useRunScreening() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { resumeId: string; jdId: string }) =>
      apiFetch<SessionDetail>("/screening", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_id: input.resumeId, jd_id: input.jdId }),
      }),
    onSuccess: (detail) => {
      qc.invalidateQueries({ queryKey: ["sessions"] });
      qc.setQueryData(["session", detail.id], detail);
    },
  });
}

export function useSession(id: string) {
  return useQuery<SessionDetail>({
    queryKey: ["session", id],
    queryFn: () => apiFetch<SessionDetail>(`/sessions/${id}`),
    enabled: Boolean(id),
  });
}

export function loginUrl(): string {
  return `${API}/auth/google/login`;
}
