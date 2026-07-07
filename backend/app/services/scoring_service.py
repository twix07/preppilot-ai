"""Readiness scoring — the single source of truth for the formula.

See docs/01-PRD.md §6 and README. Pure functions here are unit-tested; the DB
orchestration (`update_readiness`) reads per-answer scores and persists a snapshot.

Formula
-------
1. normalize:      norm = (raw - 1) / 4 * 100            # 1..5  -> 0..100
2. competency:     C_k  = Σ(w_i * norm_i) / Σ(w_i),  w_i = α^age_i  (age 0 = newest)
3. readiness:      R    = Σ(weight_k * C_k)             # weights per track
4. guard:          < MIN_SESSIONS  -> band "building_baseline"
5. bands:          <50 building · 50-70 developing · 70-85 nearly_ready · 85+ interview_ready
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rubrics import COMPETENCY_KEYS, get_rubric
from app.core.config import settings
from app.models.readiness_score import (
    BAND_BUILDING,
    BAND_BUILDING_BASELINE,
    BAND_DEVELOPING,
    BAND_INTERVIEW_READY,
    BAND_NEARLY_READY,
    ReadinessScore,
)
from app.repositories.repositories import AnswerRepository, ReadinessRepository, SessionRepository


def normalize(raw: int) -> float:
    return (raw - 1) / 4 * 100


def competency_scores_from_series(
    series_by_key: dict[str, list[int]], alpha: float | None = None
) -> dict[str, float]:
    """series_by_key: competency_key -> list of raw 1-5 scores, NEWEST FIRST.

    Returns competency_key -> 0..100 recency-weighted score (0.0 if no data).
    """
    a = settings.readiness_alpha if alpha is None else alpha
    out: dict[str, float] = {}
    for key in COMPETENCY_KEYS:
        raws = series_by_key.get(key, [])
        if not raws:
            out[key] = 0.0
            continue
        num = 0.0
        den = 0.0
        for age, raw in enumerate(raws):  # age 0 = newest
            w = a ** age
            num += w * normalize(raw)
            den += w
        out[key] = round(num / den, 2) if den else 0.0
    return out


def readiness_from_competencies(competency_scores: dict[str, float], track: str) -> float:
    weights = get_rubric(track).weights
    # Only average over competencies that have data; renormalize weights across them.
    active = {k: v for k, v in competency_scores.items() if v > 0}
    if not active:
        return 0.0
    total_w = sum(weights[k] for k in active)
    if total_w == 0:
        return 0.0
    score = sum(weights[k] * competency_scores[k] for k in active) / total_w
    return round(score, 2)


def band_for(overall: float, session_count: int) -> str:
    if session_count < settings.readiness_min_sessions:
        return BAND_BUILDING_BASELINE
    if overall < 50:
        return BAND_BUILDING
    if overall < 70:
        return BAND_DEVELOPING
    if overall < 85:
        return BAND_NEARLY_READY
    return BAND_INTERVIEW_READY


@dataclass
class ReadinessResult:
    overall: float
    band: str
    competency_breakdown: dict[str, float]
    session_count: int


async def compute_readiness(db: AsyncSession, user_id: str, track: str) -> ReadinessResult:
    """Recompute readiness purely from stored per-answer scores (auditable)."""
    answer_repo = AnswerRepository(db)
    session_repo = SessionRepository(db)

    rows = await answer_repo.recent_scores_for_user(user_id, track)
    # rows: (AnswerScore, competency_key, created_at) newest first
    series: dict[str, list[int]] = {k: [] for k in COMPETENCY_KEYS}
    for score, key, _created in rows:
        if key in series:
            series[key].append(score.raw_score)

    competency_breakdown = competency_scores_from_series(series)
    overall = readiness_from_competencies(competency_breakdown, track)
    session_count = await session_repo.completed_count(user_id)
    return ReadinessResult(
        overall=overall,
        band=band_for(overall, session_count),
        competency_breakdown=competency_breakdown,
        session_count=session_count,
    )


async def update_readiness(
    db: AsyncSession, user_id: str, track: str, session_id: str
) -> ReadinessResult:
    """Compute and persist a readiness snapshot after a completed session."""
    result = await compute_readiness(db, user_id, track)
    snapshot = ReadinessScore(
        user_id=user_id,
        session_id=session_id,
        track=track,
        overall=result.overall,
        competency_breakdown=result.competency_breakdown,
        band=result.band,
        session_count=result.session_count,
    )
    await ReadinessRepository(db).add(snapshot)
    return result
