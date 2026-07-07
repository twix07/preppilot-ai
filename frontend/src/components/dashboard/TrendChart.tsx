"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = { date: string; overall: number };

export function TrendChart({ data }: { data: Point[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-slate-400">
        Complete interviews to build your readiness trend.
      </div>
    );
  }
  const chartData = data.map((d, i) => ({ ...d, label: `s${i + 1}` }));
  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
          <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#94a3b8" }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "#94a3b8" }} />
          <Tooltip
            formatter={(v: number) => [`${v}`, "Readiness"]}
            labelFormatter={(_, p: any) => p?.[0]?.payload?.date || ""}
          />
          <ReferenceLine y={85} stroke="#22c55e" strokeDasharray="4 4" label={{ value: "Ready", fontSize: 10, fill: "#22c55e" }} />
          <ReferenceLine y={70} stroke="#eab308" strokeDasharray="4 4" />
          <Line type="monotone" dataKey="overall" stroke="#3b6cf6" strokeWidth={3} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
