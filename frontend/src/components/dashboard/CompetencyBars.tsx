"use client";

type Comp = { key: string; name: string; score: number };

function color(score: number) {
  if (score >= 85) return "bg-green-500";
  if (score >= 70) return "bg-brand-500";
  if (score >= 50) return "bg-yellow-500";
  return "bg-red-400";
}

export function CompetencyBars({ competencies }: { competencies: Comp[] }) {
  return (
    <div className="space-y-3">
      {competencies.map((c) => (
        <div key={c.key}>
          <div className="flex justify-between text-sm">
            <span className="text-slate-600">{c.name}</span>
            <span className="font-medium text-slate-800">{c.score > 0 ? Math.round(c.score) : "—"}</span>
          </div>
          <div className="mt-1 h-2 w-full rounded-full bg-slate-100">
            <div
              className={`h-2 rounded-full ${color(c.score)}`}
              style={{ width: `${Math.max(3, c.score)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
