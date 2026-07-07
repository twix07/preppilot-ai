"use client";

import { useState } from "react";
import { api } from "@/lib/api";

function Dots({ score }: { score: number }) {
  return (
    <span className="tracking-tight">
      {[1, 2, 3, 4, 5].map((n) => (
        <span key={n} className={n <= score ? "text-brand-500" : "text-slate-200"}>
          ●
        </span>
      ))}
    </span>
  );
}

export function FeedbackCard({ feedback, sessionId }: { feedback: any; sessionId?: string }) {
  const [rated, setRated] = useState<null | boolean>(null);
  if (!feedback) return null;

  async function rate(helpful: boolean) {
    setRated(helpful);
    if (sessionId) {
      try {
        await api.thumbs(sessionId, helpful, feedback.for_question_id);
      } catch {
        /* non-blocking metric */
      }
    }
  }

  return (
    <div className="card border-brand-100 bg-brand-50/40">
      <div className="text-sm font-semibold text-brand-700">Feedback</div>
      <div className="mt-3 grid grid-cols-1 gap-1 sm:grid-cols-2">
        {feedback.scores.map((s: any) => (
          <div key={s.competency} className="flex items-center justify-between text-sm">
            <span className="text-slate-600">{s.name}</span>
            <span className="flex items-center gap-2">
              <Dots score={s.score} />
              <span className="w-6 text-right text-slate-500">{s.score}/5</span>
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <div className="text-xs font-semibold uppercase text-slate-500">Improve</div>
        <ul className="mt-1 space-y-1 text-sm">
          {feedback.improvements.map((imp: string, i: number) => (
            <li key={i} className="flex gap-2">
              <span className="text-brand-500">→</span>
              <span>{imp}</span>
            </li>
          ))}
        </ul>
      </div>

      {feedback.recommendations?.length > 0 && (
        <p className="mt-3 text-sm text-slate-600">
          <span className="font-medium">Try next:</span> {feedback.recommendations.join(" ")}
        </p>
      )}

      <div className="mt-4 flex items-center gap-3 text-sm">
        {rated === null ? (
          <>
            <span className="text-slate-400">Was this helpful?</span>
            <button onClick={() => rate(true)} className="rounded-lg px-2 py-1 hover:bg-white">
              👍
            </button>
            <button onClick={() => rate(false)} className="rounded-lg px-2 py-1 hover:bg-white">
              👎
            </button>
          </>
        ) : (
          <span className="text-slate-400">Thanks for the feedback!</span>
        )}
      </div>
    </div>
  );
}
