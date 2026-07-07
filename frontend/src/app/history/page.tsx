"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, getToken } from "@/lib/api";

const BAND_LABEL: Record<string, string> = {
  building_baseline: "Building baseline",
  building: "Building",
  developing: "Developing",
  nearly_ready: "Nearly Ready",
  interview_ready: "Interview Ready",
};

export default function HistoryPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    api.analytics().then(setData).catch((e) => setError(e.message));
  }, [router]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading…</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Interview history</h1>

      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <div className="text-sm text-slate-500">Completed</div>
          <div className="text-2xl font-bold">{data.totals.interviews_completed}</div>
        </div>
        <div className="card">
          <div className="text-sm text-slate-500">Avg score</div>
          <div className="text-2xl font-bold">{data.totals.avg_score}</div>
        </div>
        <div className="card">
          <div className="text-sm text-slate-500">Change (30d)</div>
          <div className="text-2xl font-bold text-green-600">
            {data.totals.readiness_change_30d >= 0 ? "+" : ""}
            {data.totals.readiness_change_30d}
          </div>
        </div>
      </div>

      <div className="card p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-slate-400">
              <th className="p-3">Date</th>
              <th className="p-3">Track</th>
              <th className="p-3">Score</th>
              <th className="p-3">Band</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.sessions.length === 0 && (
              <tr>
                <td className="p-3 text-slate-400" colSpan={5}>
                  No interviews yet.
                </td>
              </tr>
            )}
            {data.sessions.map((s: any) => (
              <tr key={s.id} className="border-b border-slate-50">
                <td className="p-3">{s.date}</td>
                <td className="p-3 capitalize">{s.track === "pm" ? "Product" : s.track}</td>
                <td className="p-3 font-medium">{s.overall != null ? Math.round(s.overall) : "—"}</td>
                <td className="p-3 text-slate-500">{s.band ? BAND_LABEL[s.band] : "—"}</td>
                <td className="p-3 text-slate-500">{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
