"use client";

const BAND_LABEL: Record<string, string> = {
  building_baseline: "Building baseline",
  building: "Building",
  developing: "Developing",
  nearly_ready: "Nearly Ready",
  interview_ready: "Interview Ready",
};

const BAND_COLOR: Record<string, string> = {
  building_baseline: "text-slate-500",
  building: "text-red-500",
  developing: "text-yellow-600",
  nearly_ready: "text-brand-600",
  interview_ready: "text-green-600",
};

export function ReadinessCard({
  overall,
  band,
  sessionCount,
  minSessions,
}: {
  overall: number;
  band: string;
  sessionCount: number;
  minSessions: number;
}) {
  const isBaseline = band === "building_baseline";
  return (
    <div className="card">
      <div className="text-sm font-medium text-slate-500">Readiness</div>
      <div className="mt-2 flex items-end gap-2">
        <span className={`text-5xl font-bold ${isBaseline ? "text-slate-300" : "text-slate-900"}`}>
          {Math.round(overall)}
        </span>
        <span className="pb-2 text-slate-400">/ 100</span>
      </div>
      <div className={`mt-1 font-semibold uppercase tracking-wide ${BAND_COLOR[band] || ""}`}>
        {BAND_LABEL[band] || band}
      </div>
      {isBaseline ? (
        <p className="mt-2 text-xs text-slate-500">
          Building baseline ({sessionCount}/{minSessions} sessions). Complete{" "}
          {Math.max(0, minSessions - sessionCount)} more to unlock a readiness band — we don&apos;t
          show one until the score is trustworthy.
        </p>
      ) : (
        <p className="mt-2 text-xs text-slate-500">
          Based on {sessionCount} sessions, recency-weighted so recent practice counts most.
        </p>
      )}
    </div>
  );
}
