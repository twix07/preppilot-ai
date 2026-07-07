"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { FeedbackCard } from "@/components/interview/FeedbackCard";
import { api, getToken } from "@/lib/api";

const CAP = 1800;
type Phase = "setup" | "interviewing" | "done";

export default function InterviewPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("setup");
  const [track, setTrack] = useState("behavioral");
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<any>(null);
  const [progress, setProgress] = useState<{ question: number; of: number }>({ question: 1, of: 3 });
  const [answer, setAnswer] = useState("");
  const [lastFeedback, setLastFeedback] = useState<any>(null);
  const [finalReadiness, setFinalReadiness] = useState<any>(null);
  const answerRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!getToken()) router.push("/");
  }, [router]);

  async function begin() {
    setBusy(true);
    setError(null);
    try {
      let resumeId: string | null = null;
      let jdId: string | null = null;
      if (resumeText.trim().length >= 20) resumeId = (await api.uploadResume(resumeText)).id;
      if (jdText.trim().length >= 20) jdId = (await api.uploadJD(jdText)).id;
      const res = await api.startInterview(track, resumeId, jdId);
      setSessionId(res.session_id);
      setQuestion(res.question);
      setProgress(res.progress);
      setPhase("interviewing");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function submit() {
    if (!sessionId || !question || answer.trim().length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.answer(sessionId, question.id, answer.trim());
      setAnswer("");
      if (res.feedback) setLastFeedback(res.feedback);
      if (res.state === "completed") {
        setFinalReadiness(res.readiness);
        setPhase("done");
      } else {
        setQuestion(res.question);
        setProgress(res.progress);
        answerRef.current?.focus();
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (phase === "setup") {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-2xl font-bold">Start a mock interview</h1>
        <div className="card space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600">Track</label>
            <div className="mt-2 flex gap-2">
              {[
                { id: "behavioral", label: "Behavioral" },
                { id: "pm", label: "Product Management" },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTrack(t.id)}
                  className={`rounded-xl border px-4 py-2 text-sm ${
                    track === t.id
                      ? "border-brand-500 bg-brand-50 text-brand-700"
                      : "border-slate-200 text-slate-600"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">
              Resume <span className="text-slate-400">(optional — personalizes questions)</span>
            </label>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={4}
              placeholder="Paste your resume text…"
              className="mt-1 w-full rounded-xl border border-slate-300 p-3 text-sm"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600">
              Job description <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={4}
              placeholder="Paste the JD you're targeting…"
              className="mt-1 w-full rounded-xl border border-slate-300 p-3 text-sm"
            />
          </div>

          <p className="text-xs text-slate-400">3 questions · one follow-up each · ~10 minutes</p>
          <button onClick={begin} disabled={busy} className="btn-primary w-full">
            {busy ? "Preparing…" : "Begin interview ▶"}
          </button>
          {error && <p className="text-sm text-red-600">{error}</p>}
        </div>
      </div>
    );
  }

  if (phase === "done") {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <div className="card text-center">
          <h1 className="text-xl font-bold">Session complete 🎉</h1>
          {finalReadiness && (
            <p className="mt-2 text-slate-600">
              Readiness now <span className="font-bold">{Math.round(finalReadiness.overall)}</span> —{" "}
              {finalReadiness.band.replace("_", " ")}
              {finalReadiness.band === "building_baseline" &&
                ` (${finalReadiness.session_count} sessions in)`}
            </p>
          )}
        </div>
        {lastFeedback && <FeedbackCard feedback={lastFeedback} sessionId={sessionId ?? undefined} />}
        <div className="flex gap-2">
          <button onClick={() => router.push("/dashboard")} className="btn-primary flex-1">
            Back to dashboard
          </button>
          <button
            onClick={() => {
              setPhase("setup");
              setLastFeedback(null);
              setFinalReadiness(null);
            }}
            className="btn-ghost flex-1"
          >
            Practice again
          </button>
        </div>
      </div>
    );
  }

  // interviewing
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="flex items-center justify-between text-sm text-slate-500">
        <span className="font-medium capitalize">{track === "pm" ? "Product" : track} interview</span>
        <span>
          Question {progress.question} of {progress.of}
          {question?.is_follow_up && " · follow-up"}
        </span>
      </div>

      <div className="card">
        <div className="text-xs font-semibold uppercase text-slate-400">Interviewer</div>
        <p className="mt-2 text-lg">{question?.text}</p>
      </div>

      <div className="card">
        <textarea
          ref={answerRef}
          value={answer}
          onChange={(e) => setAnswer(e.target.value.slice(0, CAP))}
          rows={6}
          placeholder="Type your answer…"
          className="w-full rounded-xl border border-slate-300 p-3"
        />
        <div className="mt-2 flex items-center justify-between">
          <span className={`text-xs ${answer.length > CAP - 100 ? "text-red-500" : "text-slate-400"}`}>
            {answer.length} / {CAP} chars
          </span>
          <button onClick={submit} disabled={busy || answer.trim().length === 0} className="btn-primary">
            {busy ? "Thinking…" : "Submit answer →"}
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-400">
          Scores are hidden until after each question — just like a real interview.
        </p>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {lastFeedback && (
        <div>
          <div className="mb-1 text-xs font-medium uppercase text-slate-400">
            Feedback on your last question
          </div>
          <FeedbackCard feedback={lastFeedback} sessionId={sessionId ?? undefined} />
        </div>
      )}
    </div>
  );
}
