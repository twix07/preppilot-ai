"""Deterministic skill extraction + JD-match heuristic (no external data, no LLM needed).

Used by Resume Intelligence (E1) and Job Intelligence (E2). Kept deterministic on
purpose: the "JD match %" is an honest keyword/requirement-coverage heuristic — not an
ATS score — so it must be transparent, reproducible, and testable.
"""
from __future__ import annotations

import re

# Curated lexicon of skills/keywords relevant to the two tracks and typical student
# resumes/JDs. Multi-word entries are matched as phrases. Extend freely — this is data.
SKILL_LEXICON: list[str] = [
    # Product / analytics
    "product management", "product sense", "roadmap", "roadmapping", "prioritization",
    "user research", "a/b testing", "experimentation", "metrics", "kpi", "north star",
    "stakeholder management", "go-to-market", "wireframing", "prototyping", "user stories",
    "market research", "competitive analysis", "product strategy", "user experience", "ux",
    # Data
    "sql", "python", "excel", "tableau", "power bi", "data analysis", "data visualization",
    "statistics", "machine learning", "pandas", "r",
    # Behavioral / leadership
    "leadership", "teamwork", "communication", "ownership", "mentoring", "collaboration",
    "conflict resolution", "project management", "time management", "problem solving",
    "stakeholder communication", "public speaking", "event management",
    # General tech
    "javascript", "typescript", "react", "api", "agile", "scrum", "git",
]

# Words too generic to count as "requirements" when we scan raw JD text.
_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "have", "team", "work",
    "role", "years", "experience", "ability", "strong", "good", "plus", "etc",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def extract_skills(text: str) -> list[str]:
    """Return the lexicon skills present in the text (phrase-aware, word-boundary)."""
    hay = _norm(text)
    found: list[str] = []
    for skill in SKILL_LEXICON:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        if re.search(pattern, hay):
            found.append(skill)
    # Deduplicate while keeping deterministic (sorted) order.
    return sorted(set(found))


def jd_required_skills(jd_text: str) -> list[str]:
    """Skills the JD asks for = lexicon hits in the JD text."""
    return extract_skills(jd_text)


def compute_jd_match(resume_text: str, jd_text: str) -> dict:
    """Heuristic coverage of JD-required skills by the resume. NOT an ATS score."""
    required = jd_required_skills(jd_text)
    resume_skills = set(extract_skills(resume_text))
    if not required:
        return {
            "percent": None,
            "matched": [],
            "missing": [],
            "caveat": "No recognizable required skills found in the job description.",
        }
    matched = [s for s in required if s in resume_skills]
    missing = [s for s in required if s not in resume_skills]
    percent = round(100 * len(matched) / len(required))
    return {
        "percent": percent,
        "matched": matched,
        "missing": missing,
        "caveat": ("Heuristic keyword/requirement coverage — a transparent estimate, "
                   "not a real ATS result."),
    }
