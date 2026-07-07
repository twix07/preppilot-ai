"""Unit tests for the deterministic skill extraction + JD-match heuristic."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{tempfile.mkstemp(suffix='.db')[1]}")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

from app.ai.skills import compute_jd_match, extract_skills, jd_required_skills  # noqa: E402


def test_extract_skills_phrase_and_word_boundary():
    text = "I led A/B testing and wrote SQL queries; strong stakeholder management."
    skills = extract_skills(text)
    assert "a/b testing" in skills
    assert "sql" in skills
    assert "stakeholder management" in skills


def test_extract_skills_no_false_substring():
    # "rust" should not match inside "trust"; "r" language should not match random letters.
    assert "r" not in extract_skills("I trust the process and value truth.")


def test_jd_match_percent():
    jd = "We need SQL, product management, and A/B testing experience."
    resume = "Experienced in SQL and product management."
    match = compute_jd_match(resume, jd)
    required = jd_required_skills(jd)
    assert set(required) == {"sql", "product management", "a/b testing"}
    assert match["percent"] == 67  # 2 of 3
    assert "a/b testing" in match["missing"]
    assert "ATS" in match["caveat"]


def test_jd_match_handles_empty_requirements():
    match = compute_jd_match("anything", "no recognizable skills here at all")
    assert match["percent"] is None
