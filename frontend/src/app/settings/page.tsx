"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [me, setMe] = useState<any>(null);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    api.me().then(setMe).catch(() => router.push("/"));
  }, [router]);

  async function deleteData() {
    setBusy(true);
    setError(null);
    try {
      await api.deleteData();
      clearToken();
      router.push("/");
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="card">
        <div className="text-sm text-slate-500">Account</div>
        <div className="mt-1 font-medium">{me?.email}</div>
      </div>

      <div className="card">
        <div className="text-sm text-slate-500">Data retention</div>
        <p className="mt-1 text-sm text-slate-600">
          Your resume text is encrypted at rest. Inactive resumes are automatically deleted after
          90 days.
        </p>
      </div>

      <div className="card border-red-200 bg-red-50/40">
        <div className="font-medium text-red-700">Delete my data</div>
        <p className="mt-1 text-sm text-slate-600">
          Permanently removes your account, resumes, job descriptions, interviews, and scores. This
          cannot be undone.
        </p>
        {!confirming ? (
          <button onClick={() => setConfirming(true)} className="btn mt-3 bg-red-600 text-white hover:bg-red-700">
            Delete my data
          </button>
        ) : (
          <div className="mt-3 flex gap-2">
            <button onClick={deleteData} disabled={busy} className="btn bg-red-600 text-white hover:bg-red-700">
              {busy ? "Deleting…" : "Yes, delete everything"}
            </button>
            <button onClick={() => setConfirming(false)} className="btn-ghost">
              Cancel
            </button>
          </div>
        )}
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}
