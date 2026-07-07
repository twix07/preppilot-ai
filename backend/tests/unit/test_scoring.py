"""Unit tests for the readiness formula (the single source of truth)."""
from __future__ import annotations

import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{tempfile.mkstemp(suffix='.db')[1]}")
os.environ.setdefault("ANTHROPIC_API_KEY", "")

from app.models.readiness_score import (  # noqa: E402
    BAND_BUILDING_BASELINE,
    BAND_DEVELOPING,
    BAND_INTERVIEW_READY,
    BAND_NEARLY_READY,
)
from app.services.scoring_service import (  # noqa: E402
    band_for,
    competency_scores_from_series,
    normalize,
    readiness_from_competencies,
)


def test_normalize_endpoints():
    assert normalize(1) == 0.0
    assert normalize(5) == 100.0
    assert normalize(3) == 50.0


def test_recency_weighting_favors_recent():
    # Newest first: recent 5s should pull the score well above the old 1.
    recent_strong = competency_scores_from_series({"structure": [5, 5, 1]}, alpha=0.6)
    older_strong = competency_scores_from_series({"structure": [1, 5, 5]}, alpha=0.6)
    assert recent_strong["structure"] > older_strong["structure"]


def test_empty_series_is_zero():
    scores = competency_scores_from_series({}, alpha=0.6)
    assert all(v == 0.0 for v in scores.values())


def test_readiness_weighted_average_uses_track_weights():
    comp = {"communication": 80, "structure": 80, "depth": 80,
            "problem_solving": 80, "behavioral_star": 80}
    # All equal -> readiness equals that value regardless of weights.
    assert readiness_from_competencies(comp, "pm") == 80.0
    assert readiness_from_competencies(comp, "behavioral") == 80.0


def test_readiness_ignores_zero_competencies():
    comp = {"communication": 60, "structure": 0, "depth": 0,
            "problem_solving": 0, "behavioral_star": 0}
    assert readiness_from_competencies(comp, "pm") == 60.0


def test_small_sample_guard():
    assert band_for(90, session_count=2) == BAND_BUILDING_BASELINE
    assert band_for(90, session_count=5) == BAND_INTERVIEW_READY


def test_bands():
    assert band_for(60, 10) == BAND_DEVELOPING
    assert band_for(78, 10) == BAND_NEARLY_READY
    assert band_for(88, 10) == BAND_INTERVIEW_READY
