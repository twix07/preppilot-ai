"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, getToken } from "@/lib/api";

function SkillChips({ items, tone = "slate" }: { items: string[]; tone?: string }) {
  const cls =
    tone === "green"
      ? "bg-green-100 text-green-700"
      : tone === "red"
      ? "bg-red-100 text-red-700"
      : "bg-slate-100 text-slate-600";
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.length === 0 && <span className="text-xs text-slate-400">—</span>}
      {items.map((s) => (
        <span key={s} className={`chip ${cls}`}>
          {s}
        </span>
      ))}
    </div>
  );
}

export default function IntelligencePage() {
  const router = useRouter();
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [companyNotes, setCompanyNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resumeResult, setResumeResult] = useState<any>(null);
  const [jdResult, setJdResult] = useState<any>(null);

  useEffect(() => {
    if (!getToken()) router.push("/");
  }, [router]);

  async function analyze() {
    setBusy(true);
    setError(null);
    setResumeResult(null);
    setJdResult(null);
    try {
      if (resumeText.trim().length < 20) {
        setError("Please paste a resume (at least a few lines).");
        return;
      }
      const resume = await api.uploadResume(resumeText);
      let jdId: string | null = null;
      if (jdText.trim().length >= 20) {
        jdId = (await api.uploadJD(jdText, companyNotes)).id;
      }
      setResumeResult(await api.analyzeResume(resume.id, jdId));
      if (jdId) setJdResult(await api.analyzeJD(jdId, resume.id));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Resume &amp; Job Intelligence</h1>
        <p className="text-sm text-slate-500">
          See your skills, how your resume matches a job, and prep tips — generated only from what
          you paste. Nothing is fetched from the web.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <label className="text-sm font-medium text-slate-600">Resume</label>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            rows={7}
            placeholder="Paste your resume text…"
            className="mt-1 w-full rounded-xl border border-slate-300 p-3 text-sm"
          />
        </div>
        <div className="card space-y-3">
          <div>
            <label className="text-sm font-medium text-slate-600">
              Job description <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={4}
              placeholder="Paste the JD to get a match % and prep tips…"
              className="mt-1 w-full rounded-xl border border-slate-300 p-3 text-sm"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-600">
              Company notes <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              value={companyNotes}
              onChange={(e) => setCompanyNotes(e.target.value)}
              rows={2}
              placeholder="Anything you know about the company/team…"
              className="mt-1 w-full rounded-xl border border-slate-300 p-3 text-sm"
            />
          </div>
        </div>
      </div>

      <button onClick={analyze} disabled={busy} className="btn-primary">
        {busy ? "Analyzing…" : "Analyze"}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}

      {resumeResult && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="card">
            <div className="text-sm font-semibold text-slate-500">Resume summary</div>
            <p className="mt-2 text-sm">{resumeResult.summary}</p>
            <div className="mt-3 text-xs font-semibold uppercase text-slate-400">Detected skills</div>
            <div className="mt-1">
              <SkillChips items={resumeResult.extracted_skills} tone="green" />
            </div>
            <div className="mt-3 text-xs font-semibold uppercase text-slate-400">Suggestions</div>
            <ul className="mt-1 space-y-1 text-sm">
              {resumeResult.suggestions.map((s: string, i: number) => (
                <li key={i} className="flex gap-2">
                  <span className="text-brand-500">→</span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          {resumeResult.jd_match && (
            <div className="card">
              <div className="text-sm font-semibold text-slate-500">JD match</div>
              <div className="mt-2 flex items-end gap-2">
                <span className="text-4xl font-bold">
                  {resumeResult.jd_match.percent != null ? `${resumeResult.jd_match.percent}%` : "—"}
                </span>
                <span className="pb-1.5 text-xs text-slate-400">match</span>
              </div>
              <p className="mt-1 text-xs italic text-slate-400">{resumeResult.jd_match.caveat}</p>
              <div className="mt-3 text-xs font-semibold uppercase text-slate-400">You have</div>
              <div className="mt-1">
                <SkillChips items={resumeResult.jd_match.matched} tone="green" />
              </div>
              <div className="mt-3 text-xs font-semibold uppercase text-slate-400">Missing / to add</div>
              <div className="mt-1">
                <SkillChips items={resumeResult.jd_match.missing} tone="red" />
              </div>
            </div>
          )}
        </div>
      )}

      {jdResult && (
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-slate-500">Company prep tips</div>
            <span className="chip bg-amber-100 text-amber-700">AI-generated from your inputs</span>
          </div>
          <ul className="mt-2 space-y-1 text-sm">
            {jdResult.company_tips.map((t: string, i: number) => (
              <li key={i} className="flex gap-2">
                <span className="text-brand-500">•</span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate-400">{jdResult.source_note}</p>
        </div>
      )}
    </div>
  );
}
