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
    mutationFn: async (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/resumes`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
      if (!res.ok) throw new Error(`resume upload failed: ${res.status}`);
      return res.json();
    },
  });
}

export function useUploadJD() {
  return useMutation({
    mutationFn: async (input: { rawText?: string; file?: File }) => {
      const fd = new FormData();
      if (input.rawText) fd.append("raw_text", input.rawText);
      if (input.file) fd.append("file", input.file);
      const res = await fetch(`${API}/job_descriptions`, {
        method: "POST",
        credentials: "include",
        body: fd,
      });
      if (!res.ok) throw new Error(`jd upload failed: ${res.status}`);
      return res.json();
    },
  });
}

export function loginUrl(): string {
  return `${API}/auth/google/login`;
}
