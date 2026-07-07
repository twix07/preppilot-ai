"use client";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "preppilot_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API}${path}`, { ...options, headers: { ...headers, ...(options.headers || {}) } });
  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = body?.error || {};
    throw new ApiError(res.status, err.code || "ERROR", err.message || "Request failed");
  }
  return body as T;
}

// ---- auth ----
export const api = {
  devLogin: (email: string, name: string) =>
    request<{ access_token: string; user: any }>("/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email, name }),
    }),
  googleLogin: (idToken: string) =>
    request<{ access_token: string; user: any }>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token: idToken }),
    }),
  me: () => request<{ id: string; email: string; name: string }>("/auth/me"),

  // ---- context ----
  uploadResume: (raw_text: string) =>
    request<{ id: string }>("/resume/upload", { method: "POST", body: JSON.stringify({ raw_text }) }),
  uploadJD: (raw_text: string, company_notes?: string) =>
    request<{ id: string }>("/jd/upload", {
      method: "POST",
      body: JSON.stringify({ raw_text, company_notes }),
    }),

  // ---- interview ----
  startInterview: (track: string, resume_id?: string | null, jd_id?: string | null) =>
    request<any>("/interview/start", {
      method: "POST",
      body: JSON.stringify({ track, resume_id, jd_id }),
    }),
  answer: (session_id: string, question_id: string, text: string) =>
    request<any>("/interview/answer", {
      method: "POST",
      body: JSON.stringify({ session_id, question_id, text }),
    }),
  report: (sessionId: string) => request<any>(`/interview/${sessionId}`),
  thumbs: (session_id: string, helpful: boolean, question_id?: string | null) =>
    request<any>("/interview/feedback/thumbs", {
      method: "POST",
      body: JSON.stringify({ session_id, helpful, question_id }),
    }),

  // ---- intelligence (E1 / E2) ----
  analyzeResume: (resume_id: string, jd_id?: string | null) =>
    request<any>("/resume/analyze", { method: "POST", body: JSON.stringify({ resume_id, jd_id }) }),
  analyzeJD: (jd_id: string, resume_id?: string | null) =>
    request<any>("/jd/analyze", { method: "POST", body: JSON.stringify({ jd_id, resume_id }) }),

  // ---- data ----
  dashboard: () => request<any>("/dashboard"),
  analytics: () => request<any>("/analytics"),
  deleteData: () => request<void>("/user/data", { method: "DELETE" }),
};

export { API };
