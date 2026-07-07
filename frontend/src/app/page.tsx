"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "@/lib/api";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@preppilot.ai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.devLogin(email, "Demo Student");
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.message || "Sign in failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center">
      <h1 className="text-3xl font-bold text-brand-600">
        PrepPilot<span className="text-slate-400"> AI</span>
      </h1>
      <p className="mt-3 text-lg text-slate-700">
        Know if you&apos;re interview ready. Practice against your resume and the job, get
        rubric-based feedback, and watch your readiness improve over time.
      </p>

      <div className="card mt-8">
        <label className="text-sm font-medium text-slate-600">Email (dev sign-in)</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2"
          placeholder="you@college.edu"
        />
        <button onClick={signIn} disabled={loading} className="btn-primary mt-4 w-full">
          {loading ? "Signing in…" : "Continue"}
        </button>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        <p className="mt-4 text-xs text-slate-400">
          Demo uses passwordless dev sign-in. Production uses Google OAuth. Try{" "}
          <code>demo@preppilot.ai</code> to see seeded sessions.
        </p>
      </div>

      <div className="mt-6 flex gap-2 text-xs text-slate-500">
        <span className="chip bg-slate-100">Behavioral</span>
        <span className="chip bg-slate-100">Product Management</span>
      </div>
    </div>
  );
}
