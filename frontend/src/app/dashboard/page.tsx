"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CompetencyBars } from "@/components/dashboard/CompetencyBars";
import { ReadinessCard } from "@/components/dashboard/ReadinessCard";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { api, getToken } from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    api
      .dashboard()
      .then(setData)
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!data) return <p className="text-slate-400">Loading your dashboard…</p>;

  const empty = data.readiness.session_count === 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Your readiness</h1>
        <Link href="/interview" className="btn-primary">
          ▶ Start interview
        </Link>
      </div>

      {empty ? (
        <div className="card text-center">
          <p className="text-lg font-medium">Let&apos;s build your baseline.</p>
          <p className="mt-1 text-slate-500">
            Add your resume or a job description and complete your first mock interview.
          </p>
          <Link href="/interview" className="btn-primary mt-4 inline-flex">
            Start your first interview
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <ReadinessCard
            overall={data.readiness.overall}
            band={data.readiness.band}
            sessionCount={data.readiness.session_count}
            minSessions={data.readiness.min_sessions}
          />

          <div className="card lg:col-span-2">
            <div className="mb-2 text-sm font-medium text-slate-500">Readiness trend</div>
            <TrendChart data={data.trend} />
          </div>

          <div className="card">
            <div className="mb-3 text-sm font-medium text-slate-500">Competencies</div>
            <CompetencyBars competencies={data.competencies} />
          </div>

          <div className="card">
            <div className="mb-3 text-sm font-medium text-slate-500">Top things to fix</div>
            <ul className="space-y-3">
              {data.top_weaknesses.map((w: any) => (
                <li key={w.competency}>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{w.name}</span>
                    <span className="text-slate-500">{w.score}</span>
                  </div>
                  <p className="text-xs text-slate-500">{w.why}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <div className="mb-1 text-sm font-medium text-slate-500">This week&apos;s roadmap</div>
            <p className="text-xs text-slate-400">Focus: {data.roadmap.focus.join(", ") || "—"}</p>
            <ul className="mt-2 space-y-2 text-sm">
              {data.roadmap.actions.map((a: string, i: number) => (
                <li key={i} className="flex gap-2">
                  <span className="text-brand-500">•</span>
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
